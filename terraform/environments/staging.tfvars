environment = "staging"
aws_region  = "us-east-1"

# Networking
vpc_cidr = "10.1.0.0/16"

# Database — medium, mirrors production schema
db_instance_class    = "db.t3.medium"
db_allocated_storage = 50

# Cache
redis_node_type = "cache.t3.medium"

# EKS — 2 nodes for basic HA testing
eks_node_instance_type = "t3.medium"
eks_node_min_size      = 2
eks_node_max_size      = 4
eks_node_desired_size  = 2

# DNS
domain_name = "shipflow.io"

# Safety
enable_deletion_protection = true
