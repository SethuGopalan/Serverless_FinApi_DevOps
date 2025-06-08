import dagger
import asyncio
import os

async def main():
    async with dagger.Connection() as client:
        print("Deploying Nitric app to AWS...")

        # Correct directory structure: mount entire 'services' directory
        nitric_dir = client.host().directory("AppAWSDeploy/services", exclude=["__pycache__", ".git"])

        # Retrieve Pulumi token from AWS SSM Parameter Store
        pulumi_token = (
            await client.container()
            .from_("amazonlinux")
            .with_exec(["yum", "-y", "install", "awscli"])
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_exec(["aws", "ssm", "get-parameter", "--name", "/pulumi/access_token", "--with-decryption", "--region", "us-east-1"])
            .stdout()
        )

        # Extract the token from JSON string
        import json
        pulumi_token = json.loads(pulumi_token)["Parameter"]["Value"]

        # Prepare container to install Nitric, Pulumi, Python packages, and deploy
        container = (
            client.container()
            .from_("python:3.12-slim")
            .with_exec(["apt", "update", "-y"])
            .with_exec(["apt", "install", "-y", "curl", "unzip", "git"])
            .with_exec(["sh", "-c", "curl -fsSL https://cli.nitric.io/install.sh | sh"])
            .with_exec(["pip", "install", "--no-cache-dir", "pulumi", "boto3", "requests", "pydantic", "fastapi"])
            .with_mounted_directory("/app", nitric_dir)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_env_variable("PULUMI_ACCESS_TOKEN", pulumi_token)
            .with_exec(["nitric", "deploy", "--stack", "dev"])
        )

        # Run the deployment
        result = await container.stdout()
        print(result)
        print(" Nitric app deployed successfully.")

if __name__ == "__main__":
    asyncio.run(main())



