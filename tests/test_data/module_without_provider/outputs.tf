output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.test.id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.test.id
}
