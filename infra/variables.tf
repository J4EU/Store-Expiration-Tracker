variable "aws_region" {
  description = "AWS region for this manual deployment spike."
  type        = string
  default     = "ap-northeast-2"
}

variable "name_prefix" {
  description = "Prefix for AWS resource names."
  type        = string
  default     = "store-expiration-tracker"
}

variable "key_pair_name" {
  description = "Existing EC2 key pair used for manual SSH access."
  type        = string
  default     = "j4eu-ec2"
}

variable "instance_type" {
  description = "EC2 instance type for the Compose verification host."
  type        = string
  default     = "t3.micro"
}

variable "allowed_operator_cidr" {
  description = "Your current public IPv4 address in CIDR form, for example 203.0.113.10/32."
  type        = string

  validation {
    condition     = can(cidrhost(var.allowed_operator_cidr, 0))
    error_message = "allowed_operator_cidr must be a valid CIDR block, such as 203.0.113.10/32."
  }
}
