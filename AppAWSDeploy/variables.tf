variable "vpc_id" {
  description = "The VPC ID for the EC2 instance"
  type        = string
}

variable "subnet_id" {
  description = "The Subnet ID for the EC2 instance"
  type        = string
}
variable "ssh_public_key" {
  description = "SSH Public Key content"
  type        = string
}

