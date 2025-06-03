import dagger
import os

# Initialize the Dagger client
async def main():
    async with dagger.Connection() as client:
        # Mount local Terraform directory
        tf_dir = client.host().directory("AppAWSDeploy", exclude=[".git", "__pycache__"])

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

        # Terraform init (with upgrade to refresh providers)
        await tf.with_exec(["terraform", "init", "-upgrade"]).exit_code()

        # Terraform apply with required vars from GitHub secrets
        await tf.with_exec([
            "terraform", "apply", "-auto-approve",
            "-var", f"vpc_id={os.getenv('TF_VAR_VPC_ID')}",
            "-var", f"subnet_id={os.getenv('TF_VAR_SUBNET_ID')}"
        ]).exit_code()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

