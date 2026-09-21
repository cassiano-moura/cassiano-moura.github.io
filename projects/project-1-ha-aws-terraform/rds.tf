# ==============================================================================
# MULTI-AZ RDS MYSQL DATABASE TIER
# Project: Multi-Tier Resilient AWS Architecture
# Engineer: Cassiano Moura
# ==============================================================================

# 1. DB Subnet Group across Private DB Subnets
resource "aws_db_subnet_group" "rds_subnet_group" {
  name        = "${var.project_name}-db-subnet-group"
  description = "Isolated subnets for Multi-AZ RDS instance"
  subnet_ids  = aws_subnet.private_db[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# 2. Amazon RDS MySQL Database Instance
resource "aws_db_instance" "app_database" {
  identifier        = "${var.project_name}-db"
  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]

  # Multi-AZ Redundancy across Availability Zones
  multi_az = true

  # Security & Maintenance
  publicly_accessible    = false
  skip_final_snapshot    = true
  deletion_protection    = false
  backup_retention_period = 7

  tags = {
    Name = "${var.project_name}-mysql-db"
    Tier = "Database"
  }
}
