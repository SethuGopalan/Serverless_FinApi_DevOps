# Import the Dagger SDK for defining and running CI/CD pipelines
import dagger

# Import Boto3, the AWS SDK for Python, to interact with AWS resources
import boto3

# Define a function to fetch default VPC and subnet ID from AWS
def get_aws_network():
    # Initialize EC2 client in us-east-1 region
    ec2 = boto3.client("ec2", region_name="us-east-1")
    
    # Fetch default VPC by filtering for "isDefault = true"
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
    # Extract the VPC ID of the default VPC
    vpc_id = vpcs["Vpcs"][0]["VpcId"]

    # Get all subnets that belong to the above VPC
    subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
    # Take the first subnet ID from the list
    subnet_id = subnets["Subnets"][0]["SubnetId"]

    # Return both VPC and Subnet IDs
    return vpc_id, subnet_id

# Open a connection to the Dagger engine
with dagger.Connection() as client:
    # Call the function to get VPC and Subnet IDs from AWS
    vpc_id, subnet_id = get_aws_network()

    # Create a container from the official Terraform image
    container = (
        client.container()
        .from_("hashicorp/terraform:light")
        .with_mounted_directory("/app", client.host().directory("."))
        .with_workdir("/app")
        .with_env_variable("TF_VAR_vpc_id", vpc_id)
        .with_env_variable("TF_VAR_subnet_id", subnet_id)
        .with_exec(["terraform", "init"])
        .with_exec(["terraform", "apply", "-auto-approve"])
    )
    container.exit()


