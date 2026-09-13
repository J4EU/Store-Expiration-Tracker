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

resource "aws_ebs_volume" "sqlite_data" {
  availability_zone = var.availability_zone
  size              = 20
  type              = "gp3"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "${var.name_prefix}-sqlite-data"
  }
}
