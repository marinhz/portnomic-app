# --- Subnet Group ---

resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.cluster_id}-redis"
  subnet_ids = var.subnet_ids

  tags = { Name = "${var.cluster_id}-redis-subnet-group" }
}

# --- Security Group ---

resource "aws_security_group" "this" {
  name_prefix = "${var.cluster_id}-redis-"
  description = "Allow Redis access from EKS nodes"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis from EKS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.allowed_security_groups
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.cluster_id}-redis-sg" }

  lifecycle {
    create_before_destroy = true
  }
}

# --- Redis Replication Group ---

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = var.cluster_id
  description          = "ShipFlow Redis ${var.environment}"

  engine         = "redis"
  engine_version = "7.0"
  port           = 6379

  node_type            = var.node_type
  num_cache_clusters   = var.num_cache_nodes
  parameter_group_name = "default.redis7"

  subnet_group_name  = aws_elasticache_subnet_group.this.name
  security_group_ids = [aws_security_group.this.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  automatic_failover_enabled = var.num_cache_nodes > 1

  maintenance_window       = "sun:05:00-sun:06:00"
  snapshot_retention_limit = var.environment == "production" ? 7 : 1
  snapshot_window          = "04:00-05:00"

  tags = {
    Name        = var.cluster_id
    Environment = var.environment
  }
}
