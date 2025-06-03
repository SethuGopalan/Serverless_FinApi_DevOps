import dagger
import os
import asyncio

async def main():
    async with dagger.Connection() as client:
        tf_dir = client.host().directory("AppAWSDeploy", exclude=[".git", "__pycache__"])

        tf = (
            client.container()
            .from_("hashicorp/terraform:1.5.7")
            .with_mounted_directory("/app", tf_dir)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_env_variable("AWS_REGION", "us-east-1")
        )

        # First: init (important to install plugins)
        await tf.with_exec(["terraform", "init", "-upgrade"]).exit_code()

        # Then: apply with VPC/Subnet
        await tf.with_exec([
            "terraform", "apply",
            "-auto-approve",
            "-var", f"vpc_id={os.getenv('TF_VAR_VPC_ID')}",
            "-var", f"subnet_id={os.getenv('TF_VAR_SUBNET_ID')}"
        ]).exit_code()

if __name__ == "__main__":
    asyncio.run(main())

