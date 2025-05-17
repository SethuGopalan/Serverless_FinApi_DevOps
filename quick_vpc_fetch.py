# quick_vpc_fetch.py
import boto3

# Initialize EC2 client
ec2 = boto3.client("ec2", region_name="us-east-1")

# Fetch default VPC
vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])
vpc_id = vpcs["Vpcs"][0]["VpcId"]

# Fetch subnet in the default VPC
subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
subnet_id = subnets["Subnets"][0]["SubnetId"]

# Output in a format compatible with dagger env_file:
print(f"TF_VAR_vpc_id={vpc_id}")
print(f"TF_VAR_subnet_id={subnet_id}")
