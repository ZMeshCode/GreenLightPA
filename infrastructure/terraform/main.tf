# GreenLightPA Production Infrastructure
# Terraform configuration for AWS EKS + RDS deployment

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
  
  backend "s3" {
    bucket         = "greenlightpa-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "greenlightpa-terraform-locks"
  }
}

# AWS Provider Configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "greenlightpa"
      Environment = var.environment
      ManagedBy   = "terraform"
      HIPAA       = "compliant"
    }
  }
}

# Data Sources
data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Local Variables
locals {
  name_prefix = "greenlightpa-${var.environment}"
  
  common_tags = {
    Project     = "greenlightpa"
    Environment = var.environment
    ManagedBy   = "terraform"
    HIPAA       = "compliant"
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name_prefix = local.name_prefix
  cidr_block  = var.vpc_cidr
  
  availability_zones = data.aws_availability_zones.available.names
  
  tags = local.common_tags
}

# EKS Module
module "eks" {
  source = "./modules/eks"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnet_ids
  
  node_groups = var.eks_node_groups
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}

# RDS Module
module "rds" {
  source = "./modules/rds"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.database_subnet_ids
  
  instance_class = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage
  engine_version = var.rds_engine_version
  
  database_name = var.database_name
  master_username = var.database_username
  master_password = var.database_password
  
  backup_retention_period = var.rds_backup_retention
  multi_az = var.rds_multi_az
  
  allowed_security_groups = [module.eks.node_security_group_id]
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}

# ElastiCache Module
module "elasticache" {
  source = "./modules/elasticache"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.database_subnet_ids
  
  node_type = var.redis_node_type
  num_cache_clusters = var.redis_num_clusters
  
  allowed_security_groups = [module.eks.node_security_group_id]
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}

# KMS Module
module "kms" {
  source = "./modules/kms"
  
  name_prefix = local.name_prefix
  description = "GreenLightPA ${var.environment} encryption keys"
  
  tags = local.common_tags
}

# S3 Module for Backups
module "s3" {
  source = "./modules/s3"
  
  name_prefix = local.name_prefix
  kms_key_id  = module.kms.key_id
  
  tags = local.common_tags
}

# CloudWatch Module
module "monitoring" {
  source = "./modules/monitoring"
  
  name_prefix = local.name_prefix
  
  rds_instance_id = module.rds.instance_id
  eks_cluster_name = module.eks.cluster_name
  redis_cluster_id = module.elasticache.cluster_id
  
  sns_topic_arn = module.alerts.sns_topic_arn
  
  tags = local.common_tags
}

# SNS Alerts Module
module "alerts" {
  source = "./modules/alerts"
  
  name_prefix = local.name_prefix
  email_endpoints = var.alert_email_endpoints
  
  tags = local.common_tags
} 