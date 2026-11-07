variable "aws_region" {
  description = "AWS region for the Terraform state bucket."
  type        = string
  default     = "ap-northeast-2"
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name for Terraform state. The backend blocks of the other layers use the same literal value."
  type        = string
  default     = "j4eu-store-expiration-tracker-tfstate"
}
