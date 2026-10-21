output "allocation_id" {
  description = "Elastic IP allocation ID for the EC2 layer to associate."
  value       = aws_eip.deployment.allocation_id
}

output "public_ip" {
  description = "Fixed public IPv4 address for DNS records and SSH access."
  value       = aws_eip.deployment.public_ip
}
