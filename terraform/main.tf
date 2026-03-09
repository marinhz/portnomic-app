terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket         = "shipflow-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "shipflow-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_ca_cert)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_ca_cert)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  azs = slice(data.aws_availability_zones.available.names, 0, 3)
}

data "aws_availability_zones" "available" {
  state = "available"
}

# --- Networking ---

module "vpc" {
  source = "./modules/vpc"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  azs          = local.azs
}

# --- Compute ---

module "eks" {
  source = "./modules/eks"

  cluster_name       = "${var.project_name}-${var.environment}"
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  node_instance_type = var.eks_node_instance_type
  node_min_size      = var.eks_node_min_size
  node_max_size      = var.eks_node_max_size
  node_desired_size  = var.eks_node_desired_size
}

# --- Data Stores ---

module "rds" {
  source = "./modules/rds"

  db_name                  = "${replace(var.project_name, "-", "_")}_${var.environment}"
  instance_class           = var.db_instance_class
  allocated_storage        = var.db_allocated_storage
  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnet_ids
  allowed_security_groups  = [module.eks.node_security_group_id]
  environment              = var.environment
  multi_az                 = var.environment == "production"
  backup_retention         = var.environment == "production" ? 30 : 7
  enable_deletion_protection = var.enable_deletion_protection
}

module "elasticache" {
  source = "./modules/elasticache"

  cluster_id              = "${var.project_name}-${var.environment}"
  node_type               = var.redis_node_type
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnet_ids
  allowed_security_groups = [module.eks.node_security_group_id]
  environment             = var.environment
  num_cache_nodes         = var.environment == "production" ? 2 : 1
}

# --- Storage ---

module "s3" {
  source = "./modules/s3"

  bucket_name = "${var.project_name}-${var.environment}-storage"
  environment = var.environment
}

# --- DNS & TLS ---

module "dns" {
  source = "./modules/dns"

  domain_name = var.domain_name
  environment = var.environment
}
