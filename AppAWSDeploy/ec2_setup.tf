provider "aws" {
  region = "us-east-1"
}

# IAM Role for EC2 instance, adopting NitricUser permissions
resource "aws_iam_role" "nitric_ec2_role" {
  name = "NitricEC2InstanceRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "ec2.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

# Attach IAM Policies matching NitricUser
resource "aws_iam_role_policy_attachment" "nitric_policy_attachments" {
  for_each = toset([
    "AmazonEC2FullAccess",
    "AWSLambda_FullAccess",
    "IAMFullAccess",
    "AmazonS3FullAccess",
    "AmazonAPIGatewayAdministrator",
    "CloudWatchFullAccess",
    "AmazonSSMFullAccess",
    "SecretsManagerReadWrite",
    "AmazonECRFullAccess"
  ])
  role       = aws_iam_role.nitric_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/${each.key}"
}

# IAM Instance Profile for EC2
resource "aws_iam_instance_profile" "nitric_instance_profile" {
  name = "NitricEC2InstanceProfile"
  role = aws_iam_role.nitric_ec2_role.name
}

# EC2 Key Pair (SSH Access)
resource "aws_key_pair" "ec2_key" {
  key_name   = "nitric-key"
  public_key = file("~/.ssh/id_rsa.pub")
}

# Security Group for EC2
resource "aws_security_group" "nitric_sg" {
  name        = "nitric-ec2-sg"
  description = "Allow SSH and HTTP"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance
resource "aws_instance" "nitric_runner" {
  ami                         = "ami-053b0d53c279acc90" # Ubuntu 22.04 LTS (us-east-1)
  instance_type               = "t2.micro"
  key_name                    = aws_key_pair.ec2_key.key_name
  iam_instance_profile        = aws_iam_instance_profile.nitric_instance_profile.name
  associate_public_ip_address = true
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.nitric_sg.id]

  tags = {
    Name = "NitricEC2Runner"
  }

  user_data = <<-EOF
        #!/bin/bash
        sudo apt update -y
        sudo apt install -y git docker.io unzip curl python3 python3-pip jq

        # Enable Docker
        sudo usermod -aG docker ubuntu
        sudo systemctl enable docker
        sudo systemctl start docker

        # Install Nitric CLI
        curl -L https://nitric.io/install?version=latest | bash
        export PATH="/root/.nitric/bin:$PATH"
        echo 'export PATH="/root/.nitric/bin:$PATH"' >> /root/.bashrc

        # Install Pulumi CLI
        curl -fsSL https://get.pulumi.com | bash
        export PATH="/root/.pulumi/bin:$PATH"
        echo 'export PATH="/root/.pulumi/bin:$PATH"' >> /root/.bashrc

        # Install AWS CLI
        sudo apt install awscli -y

        # Fetch Pulumi access token from AWS SSM and login
        export PULUMI_ACCESS_TOKEN=$(aws ssm get-parameter \
            --name "/pulumi/access_token" \
            --with-decryption \
            --region us-east-1 \
            --query "Parameter.Value" \
            --output text)
        export PULUMI_ACCESS_TOKEN

        echo "export PULUMI_ACCESS_TOKEN=$PULUMI_ACCESS_TOKEN" >> /home/ubuntu/.bashrc
        pulumi login

        # Clone GitHub Repo
        cd /home/ubuntu
        git clone https://github.com/SethuGopalan/Serverless_FinApi_DevOps.git
        chown -R ubuntu:ubuntu Serverless_FinApi_DevOps

        # Setup GitHub Actions Runner
        RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/v//')
        curl -LO https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
        mkdir actions-runner && tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -C actions-runner

        # Fetch GitHub Runner Token from AWS SSM
        RUNNER_TOKEN=$(aws ssm get-parameter \
            --name "/github/runner_token" \
            --with-decryption \
            --region us-east-1 \
            --query "Parameter.Value" \
            --output text)

        # Configure and start GitHub Runner
        cd actions-runner
        ./config.sh --url https://github.com/SethuGopalan/Serverless_FinApi_DevOps --token $RUNNER_TOKEN --unattended
        ./svc.sh install
        ./svc.sh start


EOF
}
