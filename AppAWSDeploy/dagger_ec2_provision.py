
import dagger
import os

# Initialize the Dagger client
async def main():
    async with dagger.Connection() as client:
        # Mount local Terraform directory
        tf_dir = client.host().directory(".", exclude=[".git", "__pycache__"])

        # Create a container to run Terraform
        tf = (
            client.container()
            .from_("hashicorp/terraform:1.5.7")
            .with_mounted_directory("/app", tf_dir)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_env_variable("AWS_REGION", "us-east-1")
        )

        # Terraform init and apply
        await tf.with_exec(["init"]).exit_code()
        await tf.with_exec(["apply", "-auto-approve"]).exit_code()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
