# ==============================================================================
# TERRAFORM OUTPUTS
# Project: Multi-Tier Resilient AWS Architecture
# Engineer: Cassiano Moura
# ==============================================================================

output "alb_dns_name" {
  description = "The public DNS name of the Application Load Balancer to access the app"
  value       = aws_lb.external_alb.dns_name
}

output "vpc_id" {
  description = "The ID of the custom provisioned VPC"
  value       = aws_vpc.main.id
}

output "public_subnets" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_app_subnets" {
  description = "IDs of the private application subnets"
  value       = aws_subnet.private_app[*].id
}

output "private_db_subnets" {
  description = "IDs of the private database subnets"
  value       = aws_subnet.private_db[*].id
}

output "rds_endpoint" {
  description = "The connection endpoint for the Amazon RDS MySQL database"
  value       = aws_db_instance.app_database.endpoint
}

output "rds_port" {
  description = "The port on which the RDS database accepts connections"
  value       = aws_db_instance.app_database.port
}
