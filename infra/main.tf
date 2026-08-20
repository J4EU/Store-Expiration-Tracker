terraform {
  required_version = ">= 1.15.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0, < 7.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default_vpc" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

data "aws_ssm_parameter" "amazon_linux_2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

locals {
  subnet_id = sort(data.aws_subnets.default_vpc.ids)[0]
}

resource "aws_security_group" "compose_spike" {
  name        = "${var.name_prefix}-compose-spike"
  description = "Temporary SSH and Compose test access"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH from the operator current public IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_operator_cidr]
  }

  ingress {
    description = "Temporary Nginx Compose test port from the operator"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.allowed_operator_cidr]
  }

  egress {
    description = "Outbound access for manual host setup"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-compose-spike-sg"
  }
}

resource "aws_instance" "compose_spike" {
  ami                         = data.aws_ssm_parameter.amazon_linux_2023.value
  instance_type               = var.instance_type
  subnet_id                   = local.subnet_id
  key_name                    = var.key_pair_name
  vpc_security_group_ids      = [aws_security_group.compose_spike.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name = "${var.name_prefix}-compose-spike"
  }
}
