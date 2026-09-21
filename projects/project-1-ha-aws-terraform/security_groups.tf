# ==============================================================================
# LAYERED SECURITY GROUPS (Principle of Least Privilege)
# Project: Multi-Tier Resilient AWS Architecture
# Engineer: Cassiano Moura
# ==============================================================================

# 1. ALB Security Group (Publicly Facing)
resource "aws_security_group" "alb_sg" {
  name        = "${var.project_name}-alb-sg"
  description = "Controls HTTP/HTTPS ingress from public internet to ALB"
  vpc_id      = aws_vpc.main.id

  # Ingress HTTP
  ingress {
    description = "Allow inbound HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Ingress HTTPS
  ingress {
    description = "Allow inbound HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress to anywhere
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# 2. Application Tier Security Group (Private Subnet EC2 Instances)
resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-app-sg"
  description = "Allows inbound traffic exclusively from the Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  # Ingress from ALB ONLY
  ingress {
    description     = "Allow HTTP strictly from ALB Security Group"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  # Egress to anywhere (e.g. for updates or talking to DB)
  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-app-sg"
  }
}

# 3. Database Tier Security Group (Private Subnet RDS MySQL)
resource "aws_security_group" "db_sg" {
  name        = "${var.project_name}-db-sg"
  description = "Allows MySQL traffic strictly from the Application EC2 instances"
  vpc_id      = aws_vpc.main.id

  # Ingress strictly on MySQL port 3306 from app_sg
  ingress {
    description     = "Allow MySQL traffic strictly from App Security Group"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  # Outbound rule
  egress {
    description = "Allow outbound response traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-db-sg"
  }
}
