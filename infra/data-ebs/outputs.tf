output "data_volume_id" {
  description = "EBS volume ID for the EC2 layer to attach."
  value       = aws_ebs_volume.sqlite_data.id
}
