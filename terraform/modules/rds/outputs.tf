output "db_endpoint" {
  description = "RDS instance endpoint (host:port)"
  value       = aws_db_instance.this.endpoint
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.this.db_name
}

output "db_port" {
  description = "Database port"
  value       = aws_db_instance.this.port
}

output "db_security_group_id" {
  description = "Security group ID of the RDS instance"
  value       = aws_security_group.this.id
}
