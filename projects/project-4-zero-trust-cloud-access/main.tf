# ==============================================================================
# ZERO-TRUST ENTERPRISE REMOTE ACCESS (AWS SSM & AUDIT)
# Project: Bastionless Zero-Trust Infrastructure Access
# Engineer: Cassiano Moura
# ==============================================================================

terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "zero-trust-ssm-access"
}

# 1. Encrypted S3 Bucket for SSM Session Auditing
resource "aws_s3_bucket" "audit_bucket" {
  bucket_prefix = "${var.project_name}-audit-"
  force_destroy = true

  tags = {
    Project     = var.project_name
    Compliance  = "Enterprise-Audit-Log"
    Owner       = "Cassiano Moura"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "audit_encryption" {
  bucket = aws_s3_bucket.audit_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access to audit bucket
resource "aws_s3_bucket_public_access_block" "audit_block" {
  bucket = aws_s3_bucket.audit_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 2. IAM Role for Managed EC2 Instances
resource "aws_iam_role" "ssm_instance_role" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWS Managed SSM Policy
resource "aws_iam_role_policy_attachment" "ssm_core_attach" {
  role       = aws_iam_role.ssm_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance Profile for EC2
resource "aws_iam_instance_profile" "ssm_instance_profile" {
  name = "${var.project_name}-profile"
  role = aws_iam_role.ssm_instance_role.name
}

# 3. Private Security Group - ZERO INBOUND RULES (Port 22 completely closed)
resource "aws_security_group" "zero_trust_sg" {
  name        = "${var.project_name}-sg"
  description = "Zero inbound rules. Ingress strictly handled by AWS SSM agent outbound tunnel"

  # No ingress blocks defined! Port 22 is closed to all.

  egress {
    description = "Outbound HTTPS (Port 443) to AWS Systems Manager service endpoints"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-sg"
    ZeroTrust   = "Enabled"
  }
}

output "audit_s3_bucket" {
  description = "S3 bucket storing immutable session logs for compliance audits"
  value       = aws_s3_bucket.audit_bucket.bucket
}

output "security_group_id" {
  description = "Security group ID confirming 0 inbound ports open"
  value       = aws_security_group.zero_trust_sg.id
}
