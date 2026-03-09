# ShipFlow AI — Terraform Infrastructure

Infrastructure-as-Code for the ShipFlow AI maritime SaaS platform on AWS.

## Architecture

| Module        | Resources                                      |
|---------------|-------------------------------------------------|
| **vpc**       | VPC, public/private subnets (3 AZs), NAT, IGW  |
| **eks**       | EKS cluster, managed node group, OIDC/IRSA      |
| **rds**       | PostgreSQL 16, encryption, automated backups     |
| **elasticache** | Redis 7 replication group, encryption in-transit |
| **s3**        | Versioned bucket, lifecycle rules, TLS-only      |
| **dns**       | Route53 zone, ACM certificate with DNS validation|

## Prerequisites

- Terraform >= 1.5
- AWS CLI configured with appropriate credentials
- S3 bucket `shipflow-terraform-state` and DynamoDB table `shipflow-terraform-locks` for remote state (create once manually or via a bootstrap script)

## Quick Start

```bash
cd terraform

# Initialize (first time or after backend changes)
terraform init

# Deploy a specific environment
terraform plan  -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

## Environment Deployment

Each environment uses its own tfvars file and **separate VPC CIDRs** to allow peering if needed:

| Environment | File                            | VPC CIDR     |
|-------------|---------------------------------|--------------|
| dev         | `environments/dev.tfvars`       | 10.0.0.0/16  |
| staging     | `environments/staging.tfvars`   | 10.1.0.0/16  |
| production  | `environments/production.tfvars`| 10.2.0.0/16  |

### Using Terraform Workspaces

```bash
terraform workspace new dev
terraform workspace new staging
terraform workspace new production

terraform workspace select production
terraform apply -var-file=environments/production.tfvars
```

## Accessing Outputs

```bash
terraform output eks_cluster_name
terraform output -json db_endpoint
```

## Destroying Resources

**Production** has `enable_deletion_protection = true` and S3 `prevent_destroy`. To tear down:

1. Set `enable_deletion_protection = false` in tfvars and apply
2. Remove `prevent_destroy` lifecycle rules if deleting S3
3. Run `terraform destroy -var-file=environments/<env>.tfvars`

> **Warning**: Destroying production infrastructure is irreversible. Always take final RDS snapshots and verify S3 backups before proceeding.
