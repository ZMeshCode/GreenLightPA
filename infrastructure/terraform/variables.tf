# GreenLightPA Terraform Variables
# Configuration variables for production infrastructure

# General Variables
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "production"
}

# VPC Variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# EKS Variables
variable "eks_node_groups" {
  description = "EKS node group configurations"
  type = map(object({
    instance_types = list(string)
    scaling_config = object({
      desired_size = number
      max_size     = number
      min_size     = number
    })
    disk_size = number
  }))
  default = {
    greenlightpa_nodes = {
      instance_types = ["r6g.large"]
      scaling_config = {
        desired_size = 3
        max_size     = 10
        min_size     = 2
      }
      disk_size = 100
    }
  }
}

# RDS Variables
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.xlarge"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 1000
}

variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "16.1"
}

variable "rds_backup_retention" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 30
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = true
}

# Database Configuration
variable "database_name" {
  description = "Name of the production database"
  type        = string
  default     = "greenlightpa_prod"
}

variable "database_username" {
  description = "Master username for RDS instance"
  type        = string
  default     = "greenlightpa_admin"
}

variable "database_password" {
  description = "Master password for RDS instance"
  type        = string
  sensitive   = true
}

# Redis Variables
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r7g.large"
}

variable "redis_num_clusters" {
  description = "Number of Redis cache clusters"
  type        = number
  default     = 3
}

# Monitoring Variables
variable "alert_email_endpoints" {
  description = "Email addresses for alerts"
  type        = list(string)
  default     = []
}

# Security Variables
variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access resources"
  type        = list(string)
  default     = []
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
} 