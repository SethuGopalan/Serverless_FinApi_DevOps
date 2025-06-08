import dagger
import asyncio
import os  # ✅ Required for accessing environment variables

async def main():
    async with dagger.Connection() as client:
        # Mount FastAPI app directory inside container
        nitric_dir = client.host().directory("services/Data", exclude=["__pycache__", ".git"])

        # Build container with dependencies and environment setup
        container = (
            client.container()
            .from_("python:3.12-slim")
            .with_exec(["apt", "update", "-y"])
            .with_exec(["apt", "install", "-y", "curl", "unzip", "git", "awscli"])
            .with_exec(["curl", "-fsSL", "https://cli.nitric.io/install.sh", "-o", "install.sh"])
            .with_exec(["sh", "install.sh"])
            .with_exec(["pip", "install", "--no-cache-dir", "pulumi", "boto3", "requests", "pydantic", "fastapi"])
            .with_mounted_directory("/app", nitric_dir)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_exec([
                "sh", "-c",
                "export PULUMI_ACCESS_TOKEN=$(aws ssm get-parameter --name '/pulumi/access_token' --with-decryption --region us-east-1 --query 'Parameter.Value' --output text) && "
                "nitric deploy --stack dev"
            ])
        )

        print("Deploying Nitric app to AWS...")
        result = await container.stdout()
        print(result)
        print("Nitric app deployed successfully.")

if __name__ == "__main__":
    asyncio.run(main())


