import dagger
import asyncio
import os

async def main():
    async with dagger.Connection() as client:
        nitric_dir = client.host().directory("services/Data", exclude=["__pycache__", ".git"])

        container = (
            client.container()
            .from_("python:3.12-slim")
            .with_exec(["apt", "update", "-y"])
            .with_exec(["apt", "install", "-y", "curl", "unzip", "git"])
            .with_exec(["curl", "-fsSL", "https://cli.nitric.io/install.sh", "-o", "install.sh"])
            .with_exec(["sh", "install.sh"])
            .with_exec(["pip", "install", "--no-cache-dir", "pulumi", "boto3", "requests", "pydantic", "fastapi"])
            .with_mounted_directory("/app", nitric_dir)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_env_variable("PULUMI_ACCESS_TOKEN", os.getenv("PULUMI_ACCESS_TOKEN"))
            .with_exec(["nitric", "deploy", "--stack", "dev"])
        )

        print("Deploying Nitric app to AWS...")
        result = await container.stdout()
        print(result)
        print("Nitric app deployed successfully.")

if __name__ == "__main__":
    asyncio.run(main())

