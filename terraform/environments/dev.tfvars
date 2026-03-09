environment = "dev"
aws_region  = "us-east-1"

# Networking
vpc_cidr = "10.0.0.0/16"

# Database — small for development
db_instance_class    = "db.t3.micro"
db_allocated_storage = 20

# Cache — minimal
redis_node_type = "cache.t3.micro"

# EKS — single node
eks_node_instance_type = "t3.small"
eks_node_min_size      = 1
eks_node_max_size      = 2
eks_node_desired_size  = 1

# DNS
domain_name = "shipflow.io"

# Safety — relaxed for dev
enable_deletion_protection = false
