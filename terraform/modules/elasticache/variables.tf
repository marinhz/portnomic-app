variable "cluster_id" {
  description = "Identifier for the Redis replication group"
  type        = string
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "vpc_id" {
  description = "VPC ID for the security group"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for the cache subnet group"
  type        = list(string)
}

variable "allowed_security_groups" {
  description = "Security group IDs allowed to connect to Redis"
  type        = list(string)
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "num_cache_nodes" {
  description = "Number of cache nodes (>1 enables automatic failover)"
  type        = number
  default     = 1
}
