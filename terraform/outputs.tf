output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API server endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "db_endpoint" {
  description = "RDS PostgreSQL connection endpoint"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "db_name" {
  description = "RDS database name"
  value       = module.rds.db_name
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = module.elasticache.redis_endpoint
}

output "s3_bucket_name" {
  description = "S3 bucket name for file storage"
  value       = module.s3.bucket_name
}

output "certificate_arn" {
  description = "ACM certificate ARN for TLS"
  value       = module.dns.certificate_arn
}

output "domain_name" {
  description = "Fully qualified domain name"
  value       = module.dns.fqdn
}
