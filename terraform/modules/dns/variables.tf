variable "domain_name" {
  description = "Root domain name (e.g. shipflow.io)"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "lb_dns_name" {
  description = "DNS name of the load balancer for the A record alias (empty to skip)"
  type        = string
  default     = ""
}

variable "lb_zone_id" {
  description = "Route53 zone ID of the load balancer"
  type        = string
  default     = ""
}
