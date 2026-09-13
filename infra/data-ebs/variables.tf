variable "aws_region" {
  description = "AWS region for the Data EBS layer."
  type        = string
  default     = "ap-northeast-2"
}

variable "availability_zone" {
  description = "Availability Zone where the Data EBS is created."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for AWS resource names."
  type        = string
  default     = "store-expiration-tracker"
}
