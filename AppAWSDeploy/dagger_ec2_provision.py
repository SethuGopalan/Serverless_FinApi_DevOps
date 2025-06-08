import dagger
import os
import asyncio

async def main():
    # Fetch environment variables
    vpc_id = os.getenv("TF_VAR_VPC_ID")
    subnet_id = os.getenv("TF_VAR_SUBNET_ID")
    ssh_key = os.getenv("TF_VAR_SSH_PUBLIC_KEY")

    # Debug prints (optional but useful during troubleshooting)
    if not all([vpc_id, subnet_id, ssh_key]):
        raise ValueError("One or more required TF_VARs are not set.")

    print(" VPC ID:", vpc_id)
    print(" Subnet ID:", subnet_id)
    print(" SSH key (first 20 chars):", ssh_key[:20], "...")

    async with dagger.Connection() as client:
        tf_dir = client.host().directory("AppAWSDeploy", exclude=[".git", "__pycache__"])

        tf_container = (
            client.container()
            .from_("hashicorp/terraform:1.8.0")  # Terraform image
            .with_mounted_directory("/app", tf_dir)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_env_variable("AWS_REGION", "us-east-1")
        )

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
        print("Terraform output:\n", output)
        print("Terraform operations completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())


