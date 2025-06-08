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
            .with_env_variable("AWS_ACCESS_KEY_ID", os.environ["AWS_ACCESS_KEY_ID"])
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.environ["AWS_SECRET_ACCESS_KEY"])
            .with_env_variable("AWS_REGION", "us-east-1")
        )

        # Pull TF vars securely
        vpc_id = os.environ.get("TF_VAR_VPC_ID")
        subnet_id = os.environ.get("TF_VAR_SUBNET_ID")
        ssh_key = os.environ.get("TF_VAR_SSH_PUBLIC_KEY")

        if not vpc_id or not subnet_id or not ssh_key:
            raise Exception("Missing one or more required TF_VAR environment variables")

        terraform_commands = [
            "sh",
            "-c",
            f"terraform init -upgrade && terraform apply -auto-approve "
            f"-var 'vpc_id={vpc_id}' "
            f"-var 'subnet_id={subnet_id}' "
            f"-var 'ssh_public_key={ssh_key}'"
        ]

        print("Running terraform init and apply...")
        output = await tf_container.with_exec(terraform_commands).stdout()
        print(output)
        print(" Terraform operations completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
