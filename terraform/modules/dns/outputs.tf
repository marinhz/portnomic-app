output "zone_id" {
  description = "Route53 hosted zone ID"
  value       = aws_route53_zone.this.zone_id
}

output "certificate_arn" {
  description = "ARN of the validated ACM certificate"
  value       = aws_acm_certificate.this.arn
}

output "fqdn" {
  description = "Fully qualified domain name for the environment"
  value       = local.fqdn
}
