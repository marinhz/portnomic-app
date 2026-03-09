locals {
  fqdn = var.environment == "production" ? var.domain_name : "${var.environment}.${var.domain_name}"
}

# --- Route53 Hosted Zone ---

resource "aws_route53_zone" "this" {
  name = local.fqdn

  tags = {
    Name        = local.fqdn
    Environment = var.environment
  }
}

# --- ACM Certificate ---

resource "aws_acm_certificate" "this" {
  domain_name               = local.fqdn
  subject_alternative_names = ["*.${local.fqdn}"]
  validation_method         = "DNS"

  tags = {
    Name        = "${local.fqdn}-cert"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# --- DNS Validation Records ---

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.this.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.this.zone_id
}

resource "aws_acm_certificate_validation" "this" {
  certificate_arn         = aws_acm_certificate.this.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# --- A Record (alias to LB, created when lb_dns_name is provided) ---

resource "aws_route53_record" "app" {
  count = var.lb_dns_name != "" ? 1 : 0

  zone_id = aws_route53_zone.this.zone_id
  name    = local.fqdn
  type    = "A"

  alias {
    name                   = var.lb_dns_name
    zone_id                = var.lb_zone_id
    evaluate_target_health = true
  }
}
