
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.0"
    }
  }
}


provider "aws" {
  region = "us-east-1"
}

# IAM Role for GitHub Actions EC2 Runner
resource "aws_iam_role" "runner_role" {
  name = "GitHubRunnerRole"
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

# Attach necessary policies
resource "aws_iam_role_policy_attachment" "runner_policy" {
  for_each = toset([
    "AmazonEC2FullAccess",
    "CloudWatchFullAccess",
    "AmazonSSMFullAccess"
  ])
  role       = aws_iam_role.runner_role.name
  policy_arn = "arn:aws:iam::aws:policy/${each.key}"
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "runner_profile" {
  name = "GitHubRunnerProfile"
  role = aws_iam_role.runner_role.name
}

# SSH Key Pair
resource "aws_key_pair" "nitric_key" {
  key_name = aws_key_pair.nitric_key.key_name

  public_key = var.ssh_public_key
}

# Security Group
resource "aws_security_group" "runner_sg" {
  name        = "runner-sg"
  description = "Allow SSH"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
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
resource "aws_instance" "runner_instance" {
  ami           = "ami-053b0d53c279acc90" # Ubuntu 22.04 LTS
  instance_type = "t2.micro"
  key_name      = aws_key_pair.nitric_key.key_name

  iam_instance_profile        = aws_iam_instance_profile.runner_profile.name
  associate_public_ip_address = true
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.runner_sg.id]

  tags = {
    Name = "GitHubActionsRunner"
  }

  user_data = <<-EOF
              #!/bin/bash
              sudo apt update -y
              sudo apt install -y git docker.io unzip curl python3 python3-pip jq

              sudo usermod -aG docker ubuntu
              sudo systemctl enable docker
              sudo systemctl start docker

              cd /home/ubuntu
              git clone https://github.com/SethuGopalan/Serverless_FinApi_DevOps.git
              chown -R ubuntu:ubuntu Serverless_FinApi_DevOps

              RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/v//')

              curl -LO https://github.com/actions/runner/releases/download/v\\${RUNNER_VERSION}/actions-runner-linux-x64-\\${RUNNER_VERSION}.tar.gz

              mkdir actions-runner && tar xzf actions-runner-linux-x64-\\${RUNNER_VERSION}.tar.gz -C actions-runner

              RUNNER_TOKEN=$(aws ssm get-parameter --name "/github/runner_token" --with-decryption --region us-east-1 --query "Parameter.Value" --output text)
              cd actions-runner
              ./config.sh --url https://github.com/SethuGopalan/Serverless_FinApi_DevOps --token \\$RUNNER_TOKEN --unattended
              ./svc.sh install
              ./svc.sh start
          EOF


}
