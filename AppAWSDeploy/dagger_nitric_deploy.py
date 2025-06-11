import dagger
import os
import asyncio
import json

async def main():
    # Ensure necessary environment variables are available from the GitHub Actions runner.
    # AWS credentials are for authenticating with AWS.
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_default_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1") # Default to us-east-1 if not set

    if not aws_access_key_id or not aws_secret_access_key:
        print("Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set as environment variables.")
        return

    async with dagger.Connection() as client:
        print("Deploying Nitric app to AWS...")

        # Mount source directory for your Nitric project
        # This path should reflect where your nitric.yaml and source code live within your repo.
        nitric_dir = client.host().directory("AppAWSDeploy/services", exclude=["__pycache__", ".git"])

        # Pull Pulumi token from AWS SSM using a temporary container.
        # This container needs AWS CLI installed and AWS credentials to access SSM.
        print("Fetching Pulumi Access Token from AWS SSM...")
        try:
            pulumi_token_json = (
                await client.container()
                .from_("amazonlinux:2023") # Use a lightweight Linux image with AWS CLI support
                .with_exec(["dnf", "-y", "install", "awscli"]) # Install AWS CLI using dnf for Amazon Linux 2023
                .with_env_variable("AWS_ACCESS_KEY_ID", aws_access_key_id)
                .with_env_variable("AWS_SECRET_ACCESS_KEY", aws_secret_access_key)
                .with_env_variable("AWS_DEFAULT_REGION", aws_default_region) # Ensure region is set for SSM call
                .with_exec([
                    "aws", "ssm", "get-parameter",
                    "--name", "/pulumi/access_token",
                    "--with-decryption",
                    "--region", "us-east-1" # Hardcoding region for SSM for now, can be made dynamic
                ])
                .stdout()
            )
            pulumi_token = json.loads(pulumi_token_json)["Parameter"]["Value"]
            print("Pulumi Access Token fetched successfully.")
        except dagger.ExecError as e:
            print(f"Error fetching Pulumi token from SSM: {e}")
            print(f"Stderr: {e.stderr}")
            print(f"Stdout: {e.stdout}")
            raise # Re-raise to stop execution if token can't be fetched
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from SSM response: {e}")
            print(f"SSM Raw Output: {pulumi_token_json}")
            raise
        except KeyError as e:
            print(f"Key missing in SSM response (expected 'Parameter' or 'Value'): {e}")
            print(f"SSM Raw Output: {pulumi_token_json}")
            raise

        # Use your custom image with Nitric CLI already installed
        # This container will perform the actual Nitric deployment.
        container = (
            client.container()
            .from_("7797/nitric-cli:v1") # Use your pre-built Docker image with Nitric CLI
            .with_mounted_directory("/app", nitric_dir) # Mount your Nitric project code to /app
            .with_workdir("/app") # Set working directory inside the container to /app
            # Pass AWS credentials and Pulumi token to the deployment container
            .with_env_variable("AWS_ACCESS_KEY_ID", aws_access_key_id)
            .with_env_variable("AWS_SECRET_ACCESS_KEY", aws_secret_access_key)
            .with_env_variable("AWS_DEFAULT_REGION", aws_default_region)
            .with_env_variable("PULUMI_ACCESS_TOKEN", pulumi_token)
        )

        print("Running Nitric CLI diagnostics in custom image...")
        try:
            # Get Nitric CLI version for debugging
            nitric_version_output = await container.with_exec(["nitric", "version"]).stdout()
            print("Nitric CLI Version:")
            print(nitric_version_output)

            # Run Nitric doctor to check environment health
            nitric_doctor_output = await container.with_exec(["nitric", "doctor"]).stdout()
            print("\nNitric Doctor Output:")
            print(nitric_doctor_output)

            # Execute the Nitric deployment command.
            # 'nitric up' typically finds the 'nitric.yaml' in the working directory
            # and infers the cloud provider from its configuration.
            print(f"\nAttempting Nitric deployment to AWS (region: {aws_default_region})...")
            # If your nitric.yaml explicitly defines the provider (e.g., provider: aws),
            # then 'nitric up' without --stack should work.
            result = await container.with_exec(["nitric", "up"]).stdout()
            print("Nitric deployment successful:")
            print(result)

        except dagger.ExecError as e:
            print(f"Nitric operation failed: {e}")
            print(f"Stderr: {e.stderr}")
            print(f"Stdout: {e.stdout}")
            # Re-raise the exception to propagate the failure
            raise
        except Exception as e:
            print(f"An unexpected error occurred during Nitric deployment: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())