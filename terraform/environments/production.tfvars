environment = "production"
aws_region  = "us-east-1"

# Networking
vpc_cidr = "10.2.0.0/16"

# Database — production-grade, Multi-AZ handled automatically
db_instance_class    = "db.r6g.large"
db_allocated_storage = 100

# Cache — production with failover
redis_node_type = "cache.r6g.large"

# EKS — 3+ nodes with autoscaling headroom
eks_node_instance_type = "t3.large"
eks_node_min_size      = 3
eks_node_max_size      = 10
eks_node_desired_size  = 3

# DNS
domain_name = "shipflow.io"

# Safety — fully protected
enable_deletion_protection = true
