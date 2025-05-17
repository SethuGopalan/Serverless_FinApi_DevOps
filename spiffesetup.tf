provider "aws" {
  region = "us-east-1"
}

variable "vpc_id" {}
variable "subnet_id" {}

resource "random_string" "suffix" {
  length  = 4
  special = false
}

# ✅ Security Group for SPIRE Server
resource "aws_security_group" "Ip_spire_sg" {
  name        = "Ip_spire-sg-${random_string.suffix.result}"
  description = "Allow SPIRE server traffic"
  vpc_id      = var.vpc_id


  ingress {
    description = "SPIRE server port"
    from_port   = 8081
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Or tighten if needed
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ✅ EC2 Instance using pre-attached IAM role (DEVOPS)
resource "aws_instance" "spire_server" {
  ami                    = "ami-0c7217cdde317cfec" # Amazon Linux 2 (x86_64)
  instance_type          = "t3.micro"
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.Ip_spire_sg.id]

  # 🚫 Skip IAM instance profile because you're using DEVOPS role already

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y wget unzip

              mkdir -p /opt/spire/{bin,conf,run}
              cd /opt/spire

              wget https://github.com/spiffe/spire/releases/download/v1.6.5/spire-1.6.5-linux-x86_64-glibc.tar.gz
              tar -xzf spire-1.6.5-linux-x86_64-glibc.tar.gz
              cp spire-1.6.5/bin/* /opt/spire/bin

              cat <<EOCONF > /opt/spire/conf/server.conf
              server {
                bind_address = "0.0.0.0"
                bind_port = 8081
                trust_domain = "financeapi.dev"
                data_dir = "/opt/spire/run"
              }

              plugins {
                DataStore "memory" {
                  plugin_data {}
                }

                NodeAttestor "join_token" {
                  plugin_data {}
                }

                KeyManager "memory" {
                  plugin_data {}
                }
              }
              EOCONF

              /opt/spire/bin/spire-server run -config /opt/spire/conf/server.conf
              EOF

  tags = {
    Name = "Spire-Server"
  }
}
