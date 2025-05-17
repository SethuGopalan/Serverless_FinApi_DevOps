import dagger
import boto3
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

def get_aws_network():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
    vpc_id = vpcs["Vpcs"][0]["VpcId"]
    subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
    subnet_id = subnets["Subnets"][0]["SubnetId"]
    return vpc_id, subnet_id

async def main():
    vpc_id, subnet_id = get_aws_network()

    async with dagger.Connection() as client:
        host_dir = client.host().directory(".")

        # Step 1: Terraform Destroy
        destroy = (
            client.container()
            .from_("hashicorp/terraform:light")
            .with_mounted_directory("/app", host_dir)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_env_variable("AWS_REGION", os.getenv("AWS_REGION"))
            .with_env_variable("TF_VAR_vpc_id", vpc_id)
            .with_env_variable("TF_VAR_subnet_id", subnet_id)
            .with_exec(["terraform", "init"])
            .with_exec(["terraform", "destroy", "-auto-approve"])
        )
        destroy_output = await destroy.stdout()
        print("[INFO] Terraform Destroy Output:\n", destroy_output)

        # Step 2: Terraform Apply (SPIRE EC2)
        apply = (
            client.container()
            .from_("hashicorp/terraform:light")
            .with_mounted_directory("/app", host_dir)
            .with_workdir("/app")
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
            .with_env_variable("AWS_REGION", os.getenv("AWS_REGION"))
            .with_env_variable("TF_VAR_vpc_id", vpc_id)
            .with_env_variable("TF_VAR_subnet_id", subnet_id)
            .with_exec(["terraform", "init"])
            .with_exec(["terraform", "plan", "-out=tfplan"])
            .with_exec(["terraform", "apply", "tfplan"])
        )
        apply_output = await apply.stdout()
        print("[INFO] Terraform Apply Output:\n", apply_output)

        # Step 3: Deploy FastAPI via Nitric CLI Docker
        nitric_up = (
            client.container()
            .from_("asalkeld/nitric-cli:latest")
            .with_mounted_directory("/app", client.host().directory("."))  # ensure nitric-dev.yaml is included
            .with_workdir("/app")
            .with_exec(["ls", "-la"])  # optional: verify contents in logs
            .with_exec(["cat", "nitric.dev.yaml"])  # optional: verify visibility
            .with_exec(["mv", "nitric.dev.yaml", "nitric-dev.yaml"])
            .with_exec(["nitric", "up", "--stack", "dev"])
        )


        nitric_output = await nitric_up.stdout()
        print("[SUCCESS] Nitric Deployment Output:\n", nitric_output)

asyncio.run(main())
