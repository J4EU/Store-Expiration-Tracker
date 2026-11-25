terraform {
  required_version = ">= 1.15.0, < 2.0.0"

  backend "s3" {
    bucket       = "j4eu-store-expiration-tracker-tfstate"
    key          = "data-ebs/terraform.tfstate"
    region       = "ap-northeast-2"
    encrypt      = true
    use_lockfile = true
  }

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

locals {
  # DLM은 이 태그가 붙은 볼륨을 찍고, Recycle Bin은 이 태그가 붙은 스냅샷을 보존한다.
  backup_tags = {
    Backup = "${var.name_prefix}-sqlite-data"
  }
}

resource "aws_ebs_volume" "sqlite_data" {
  availability_zone = var.availability_zone
  size              = 1
  type              = "gp3"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name   = "${var.name_prefix}-sqlite-data"
    Backup = local.backup_tags.Backup
  }
}
