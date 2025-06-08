import dagger
import asyncio
import os
import json
import re

async def main():
    async with dagger.Connection() as client:
        print("Deploying Nitric app to AWS...")

        # Mount the correct directory for your FastAPI Nitric app
        nitric_dir = client.host().directory("AppAWSDeploy/services", exclude=["__pycache__", ".git"])

        # Step 1: Retrieve Pulumi token from AWS SSM
        pulumi_token_raw = (
            await client.container()
            .from_("amazonlinux")
            .with_exec(["yum", "-y", "install", "awscli"])
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_exec([
                "aws", "ssm", "get-parameter",
                "--name", "/pulumi/access_token",
                "--with-decryption",
                "--region", "us-east-1"
            ])
            .stdout()
        )
        pulumi_token = json.loads(pulumi_token_raw)["Parameter"]["Value"]

        # Step 2: Deploy using Nitric CLI inside container
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

        # Step 3: Capture and display output with API link
        result = await container.stdout()
        print(result)

        match = re.search(r"https://[a-zA-Z0-9.-]+\.amazonaws\.com/[^\s]*", result)
        if match:
            print(f"\n Your API is live at: {match.group(0)}")
        else:
            print("\nDeployment finished, but API URL not found in output.")

        print("Nitric app deployment process completed.")

if __name__ == "__main__":
    asyncio.run(main())
