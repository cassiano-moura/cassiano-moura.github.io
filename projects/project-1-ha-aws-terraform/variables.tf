# ==============================================================================
# VARIABLES DEFINITION
# Project: Multi-Tier Resilient AWS Architecture (Zero-Cost / Free-Tier Friendly)
# Engineer: Cassiano Moura
# ==============================================================================

variable "aws_region" {
  description = "AWS Region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for tagging and resource naming"
  type        = string
  default     = "enterprise-ha-platform"
}

variable "environment" {
  description = "Deployment environment (e.g. prod, staging, dev)"
  type        = string
  default     = "production"
}

# --- Network CIDRs ---
variable "vpc_cidr" {
  description = "CIDR block for the custom VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of Availability Zones for Multi-AZ redundancy"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (ALB & NAT)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_app_subnet_cidrs" {
  description = "CIDR blocks for private application subnets (EC2 Auto Scaling)"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "private_db_subnet_cidrs" {
  description = "CIDR blocks for isolated database subnets (RDS Multi-AZ)"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24"]
}

# --- Compute / EC2 ---
variable "instance_type" {
  description = "EC2 Instance type (t3.micro is AWS Free Tier eligible)"
  type        = string
  default     = "t3.micro"
}

variable "asg_min_size" {
  description = "Minimum number of EC2 instances in the Auto Scaling Group"
  type        = number
  default     = 2
}

variable "asg_max_size" {
  description = "Maximum number of EC2 instances in the Auto Scaling Group"
  type        = number
  default     = 4
}

variable "asg_desired_capacity" {
  description = "Desired number of EC2 instances in the Auto Scaling Group"
  type        = number
  default     = 2
}

# --- Database / RDS ---
variable "db_instance_class" {
  description = "RDS DB instance class (db.t3.micro is Free Tier eligible)"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS instance in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Default database name"
  type        = string
  default     = "app_production_db"
}

variable "db_username" {
  description = "Master username for RDS MySQL database"
  type        = string
  default     = "admin_user"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for RDS MySQL database"
  type        = string
  default     = "SecureMasterPass2026!"
  sensitive   = true
}
