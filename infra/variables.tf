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
  description = "EC2 instance type for the deployment host."
  type        = string
  default     = "t3.micro"
}

variable "data_volume_id" {
  description = "Existing Data EBS volume ID managed by the data-ebs layer."
  type        = string
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
