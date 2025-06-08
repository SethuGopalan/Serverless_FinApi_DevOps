import dagger
import os
import asyncio

async def main():
    async with dagger.Connection() as client:
        tf_dir = client.host().directory("AppAWSDeploy", exclude=[".git", "__pycache__"])

        tf_container = (
            client.container()
            .from_("hashicorp/terraform:1.8.0")
            .with_mounted_directory("/app", tf_dir)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_env_variable("AWS_REGION", "us-east-1")
        )

        terraform_command = (
            "terraform init -upgrade && "
            "terraform apply -auto-approve "
            f"-var='vpc_id={os.getenv('TF_VAR_VPC_ID')}' "
            f"-var='subnet_id={os.getenv('TF_VAR_SUBNET_ID')}' "
            f"-var='ssh_public_key={os.getenv('TF_VAR_SSH_PUBLIC_KEY')}'"
        )

        print("Running terraform init and apply...")
        result = await tf_container.with_exec(["sh", "-c", terraform_command]).stdout()
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
