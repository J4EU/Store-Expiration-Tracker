output "bucket_name" {
  description = "S3 bucket that stores Terraform state for the other layers."
  value       = aws_s3_bucket.tfstate.bucket
}
