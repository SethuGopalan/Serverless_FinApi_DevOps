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
            .with_env_variable("TF_VAR_VPC_ID", os.getenv("TF_VAR_VPC_ID"))
            .with_env_variable("TF_VAR_SUBNET_ID", os.getenv("TF_VAR_SUBNET_ID"))
            .with_env_variable("TF_VAR_SSH_PUBLIC_KEY", os.getenv("TF_VAR_SSH_PUBLIC_KEY"))
        )

        terraform_commands = [
            "sh",
            "-c",
            "terraform init -upgrade && terraform apply -auto-approve"
        ]

        print("Running terraform init and apply...")
        output = await tf_container.with_exec(terraform_commands).stdout()
        print(output)
        print("Terraform operations completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())

