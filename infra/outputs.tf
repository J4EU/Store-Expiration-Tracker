output "instance_id" {
  description = "EC2 instance ID for the manual Compose verification host."
  value       = aws_instance.compose_spike.id
}

output "public_ip" {
  description = "Public IPv4 address used for SSH and the temporary Compose test port."
  value       = aws_instance.compose_spike.public_ip
}

output "security_group_id" {
  description = "Security group attached to the Compose verification host."
  value       = aws_security_group.compose_spike.id
}
