import dagger
import os
import asyncio
import boto3
import base64

async def get_pulumi_token():
    """Fetch Pulumi access token from AWS SSM Parameter Store"""
    ssm = boto3.client('ssm', region_name="us-east-1")
    response = ssm.get_parameter(Name="/Pulumi/AccessToken", WithDecryption=True)
    return response['Parameter']['Value']

async def main():
    print("Deploying Nitric app to AWS...")

    # Fetch Pulumi token from SSM
    print("Fetching Pulumi Access Token from AWS SSM...")
    pulumi_access_token = await get_pulumi_token()
    print("Pulumi Access Token fetched successfully.")

    # Start Dagger connection
    async with dagger.Connection(timeout=600) as client:
        src = client.host().directory(".")

        # Base Nitric image (with Python SDK)
        nitric_image = "docker.io/nitrictech/nitric:1.61.0-python"

        # Mount source code and Docker socket
        container = (
            client.container()
            .from_(nitric_image)
            .with_mounted_directory("/src", src)
            .with_workdir("/src")
            .with_unix_socket("/var/run/docker.sock", client.host().unix_socket("/var/run/docker.sock"))
            .with_env_variable("AWS_ACCESS_KEY_ID", os.environ["AWS_ACCESS_KEY_ID"])
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.environ["AWS_SECRET_ACCESS_KEY"])
            .with_env_variable("AWS_REGION", os.environ.get("AWS_REGION", "us-east-1"))
            .with_env_variable("PULUMI_ACCESS_TOKEN", pulumi_access_token)
        )

        print("Running Nitric CLI diagnostics in custom image...")
        version_output = await container.with_exec(["nitric", "version"]).stdout()
        print(f"Nitric CLI Version:\n{version_output}")

        print("\nAttempting Nitric deployment to AWS (region: us-east-1)...")
        try:
            result = await container.with_exec(["nitric", "up"]).stdout()
            print(" Nitric deployment successful!")
            print(result)
        except dagger.ExecError as e:
            print("Nitric operation failed.")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            raise
        except Exception as e:
            print("Unexpected error during Nitric deployment.")
            raise
        # print

if __name__ == "__main__":
    asyncio.run(main())
