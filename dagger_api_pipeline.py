
import dagger
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

DOCKERHUB_USERNAME = os.getenv("DOCKERHUB_USERNAME")
DOCKERHUB_PASSWORD = os.getenv("DOCKERHUB_PASSWORD")
DOCKER_IMAGE_NAME = "7797/population-api:latest"

async def main():
    async with dagger.Connection() as client:
        # Mount local project directory
        source = client.host().directory(".")

        # Step 1: Build Docker image for the API
        python_builder = (
            client.container()
            .from_("docker:24.0.5-dind")
            .with_mounted_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["cp", "python.dockerfile", "Dockerfile"])  # Copy custom Dockerfile to default name
            .with_exec(["docker", "build", "-t", DOCKER_IMAGE_NAME, "."])
        )
        print("[✓] API Docker image built.")

        # Step 2: Push Docker image to Docker Hub
        docker_push = (
            client.container()
            .from_("docker:24.0.5-dind")
            .with_mounted_directory("/app", source)
            .with_workdir("/app")
            .with_env_variable("DOCKER_USER", DOCKERHUB_USERNAME)
            .with_env_variable("DOCKER_PASS", DOCKERHUB_PASSWORD)
            .with_exec(["sh", "-c", "echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin"])
            .with_exec(["docker", "push", DOCKER_IMAGE_NAME])
        )
        print("[✓] Docker image pushed to Docker Hub.")

        # Step 3: Deploy to AWS via Nitric CLI
        nitric_up = (
            client.container()
            .from_("7797/nitric-cli:v1")  # Your custom Nitric CLI image
            .with_mounted_directory("/app", source)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_env_variable("AWS_REGION", os.getenv("AWS_REGION"))
            .with_exec(["ls", "-la"])  # Optional debug step
            .with_exec(["cat", "nitric.yaml"])
            .with_exec(["nitric", "up", "--stack", "dev"])
        )

        deploy_output = await nitric_up.stdout()
        print("[SUCCESS] Nitric Deployment Output:\n", deploy_output)

asyncio.run(main())
