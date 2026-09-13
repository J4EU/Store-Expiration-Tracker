output "instance_id" {
  description = "EC2 instance ID for the deployment host."
  value       = aws_instance.deployment.id
}

output "public_ip" {
  description = "Public IPv4 address used for SSH and application access."
  value       = aws_instance.deployment.public_ip
}

output "security_group_id" {
  description = "Security group attached to the deployment host."
  value       = aws_security_group.deployment.id
}

output "data_volume_id" {
  description = "EBS volume ID that stores the SQLite service data."
  value       = data.aws_ebs_volume.sqlite_data.id
}
