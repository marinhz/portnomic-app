resource "random_password" "db" {
  length  = 32
  special = false
}

# --- Subnet Group ---

resource "aws_db_subnet_group" "this" {
  name       = "${var.db_name}-subnet-group"
  subnet_ids = var.subnet_ids

  tags = { Name = "${var.db_name}-subnet-group" }
}

# --- Security Group ---

resource "aws_security_group" "this" {
  name_prefix = "${var.db_name}-rds-"
  description = "Allow PostgreSQL access from EKS nodes"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from EKS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_groups
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.db_name}-rds-sg" }

  lifecycle {
    create_before_destroy = true
  }
}

# --- Parameter Group ---

resource "aws_db_parameter_group" "this" {
  name   = "${var.db_name}-pg16"
  family = "postgres16"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "500"
  }

  tags = { Name = "${var.db_name}-params" }
}

# --- RDS Instance ---

resource "aws_db_instance" "this" {
  identifier = var.db_name
  engine     = "postgres"
  engine_version = "16"

  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = replace(var.db_name, "-", "_")
  username = "shipflow_admin"
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.this.id]
  parameter_group_name   = aws_db_parameter_group.this.name

  multi_az            = var.multi_az
  publicly_accessible = false

  backup_retention_period = var.backup_retention
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  deletion_protection       = var.enable_deletion_protection
  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.db_name}-final-snapshot" : null

  performance_insights_enabled = var.environment == "production"

  tags = {
    Name        = var.db_name
    Environment = var.environment
  }

  lifecycle {
    prevent_destroy = false
  }
}

# --- Store password in SSM ---

resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.environment}/shipflow/db-password"
  type  = "SecureString"
  value = random_password.db.result

  tags = { Environment = var.environment }
}
