variable "aws_region" {
  description = "AWS region for the Elastic IP layer."
  type        = string
  default     = "ap-northeast-2"
}

variable "name_prefix" {
  description = "Prefix for AWS resource names."
  type        = string
  default     = "store-expiration-tracker"
}
