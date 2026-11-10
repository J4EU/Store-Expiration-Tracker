variable "aws_region" {
  description = "AWS region for the EC2 deployment layer."
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

variable "ami_id" {
  description = "Pinned Amazon Linux 2023 AMI for the deployment host. Changing it replaces the EC2 instance and its root volume."
  type        = string
  # al2023-ami-2023.12.20261026.1-kernel-6.18-x86_64 (ap-northeast-2)
  default = "ami-0ee840e948c0ac14b"
}

variable "instance_type" {
  description = "EC2 instance type for the deployment host."
  type        = string
  default     = "t3.micro"
}

variable "allowed_operator_cidrs" {
  description = "Public IPv4 CIDR blocks allowed to access the instance through operator-facing ports such as SSH and Nginx."
  type        = list(string)

  validation {
    condition = length(var.allowed_operator_cidrs) > 0 && alltrue([
      for cidr in var.allowed_operator_cidrs : can(cidrhost(cidr, 0))
    ])

    error_message = "allowed_operator_cidrs must contain at least one valid CIDR block, such as 203.0.113.10/32."
  }
}
