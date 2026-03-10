# AWS Best Practices and Security Defaults

## Security-First Defaults

When creating modules, always default to secure configurations:

### Encryption
```hcl
variable "encrypted" {
  description = "(Optional) Whether to enable encryption at rest."
  type        = bool
  default     = true  # Always default to encrypted
}

variable "kms_key_id" {
  description = "(Optional) KMS key ID for encryption. If not specified, uses AWS managed keys."
  type        = string
  default     = null
}
```

### Network Exposure
```hcl
variable "publicly_accessible" {
  description = "(Optional) Whether the resource is publicly accessible."
  type        = bool
  default     = false  # Always default to private
}
```

### Logging and Monitoring
```hcl
variable "enable_logging" {
  description = "(Optional) Whether to enable logging."
  type        = bool
  default     = true  # Default to logging enabled
}
```

## Resource-Specific Best Practices

### S3 Buckets
- Enable versioning by default
- Enable server-side encryption
- Block public access by default
- Enable logging

```hcl
variable "versioning_enabled" {
  description = "(Optional) Enable versioning for the S3 bucket."
  type        = bool
  default     = true
}

variable "block_public_acls" {
  description = "(Optional) Whether to block public ACLs."
  type        = bool
  default     = true
}
```

### RDS/Database Instances
- Enable automated backups
- Encrypt at rest
- Not publicly accessible
- Enable deletion protection for production
- Enable performance insights
- Enable enhanced monitoring

```hcl
variable "backup_retention_period" {
  description = "(Optional) Days to retain backups."
  type        = number
  default     = 7
}

variable "deletion_protection" {
  description = "(Optional) Enable deletion protection."
  type        = bool
  default     = false  # Set per environment
}
```

### EC2 Instances
- Use IMDSv2 only
- Enable detailed monitoring
- Encrypt EBS volumes
- Use Systems Manager for access (no SSH keys in metadata)

```hcl
variable "metadata_options" {
  description = "(Optional) Metadata options for the instance."
  type = object({
    http_endpoint               = optional(string, "enabled")
    http_tokens                 = optional(string, "required")  # IMDSv2
    http_put_response_hop_limit = optional(number, 1)
  })
  default = {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }
}
```

### VPC Configuration
- Enable DNS support and hostnames
- Enable flow logs
- Create VPC endpoints for AWS services to avoid internet traffic
- Use CIDR blocks that don't overlap with other VPCs

```hcl
variable "enable_dns_support" {
  description = "(Optional) Enable DNS support in the VPC."
  type        = bool
  default     = true
}

variable "enable_dns_hostnames" {
  description = "(Optional) Enable DNS hostnames in the VPC."
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "(Optional) Enable VPC flow logs."
  type        = bool
  default     = true
}
```

### Security Groups
- Use egress rules (don't allow all outbound by default if possible)
- Include descriptions for all rules
- Use security group references instead of CIDR blocks when possible
- Never use 0.0.0.0/0 for ingress unless absolutely necessary

```hcl
variable "ingress_rules" {
  description = "(Optional) List of ingress rules."
  type = list(object({
    description              = string
    from_port                = number
    to_port                  = number
    protocol                 = string
    cidr_blocks              = optional(list(string))
    source_security_group_id = optional(string)
  }))
  default = []
}
```

### IAM Policies
- Use least privilege principle
- Include conditions when possible
- Use managed policies when appropriate
- Document why permissions are needed

## Tagging Strategy

Always include a tags variable with sensible defaults:

```hcl
variable "tags" {
  description = "(Optional) Map of tags to assign to the resource."
  type        = map(any)
  default = {
    created_by  = "terraform"
    terraform   = "true"
    environment = "prod"
  }
}
```

Common tags to consider:
- `Name` - Resource name
- `environment` - prod/dev/staging
- `terraform` - "true" to indicate IaC management
- `created_by` - Tool or person who created it
- `cost_center` - For cost allocation
- `project` - Project association

## Naming Conventions

Use consistent naming:
```hcl
variable "name" {
  description = "(Required) Name of the resource."
  type        = string
}

# Then use in resource:
tags = merge(tomap({ Name = var.name }), var.tags)
```

Avoid `name_prefix` in modules - use fixed names for import capability.

## High Availability Patterns

For services that support it, default to multi-AZ:

```hcl
variable "multi_az" {
  description = "(Optional) Enable Multi-AZ deployment."
  type        = bool
  default     = true
}

variable "availability_zones" {
  description = "(Optional) List of availability zones."
  type        = list(string)
  default     = []  # Typically determined by subnet selection
}
```

## Backup and Recovery

Enable backups by default:

```hcl
variable "backup_retention_period" {
  description = "(Optional) Number of days to retain backups."
  type        = number
  default     = 7
  validation {
    condition     = var.backup_retention_period >= 0 && var.backup_retention_period <= 35
    error_message = "Backup retention must be between 0 and 35 days."
  }
}

variable "backup_window" {
  description = "(Optional) Preferred backup window."
  type        = string
  default     = "03:00-04:00"
}
```

## Performance Considerations

### CloudWatch Metrics
Include monitoring by default:

```hcl
variable "enable_detailed_monitoring" {
  description = "(Optional) Enable detailed CloudWatch monitoring."
  type        = bool
  default     = true
}
```

### Auto Scaling
For services with auto-scaling, provide sensible defaults:

```hcl
variable "min_capacity" {
  description = "(Optional) Minimum capacity."
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "(Optional) Maximum capacity."
  type        = number
  default     = 3
}
```

## Cost Optimization

Provide cost-effective defaults while maintaining security:

```hcl
variable "storage_type" {
  description = "(Optional) Storage type for the resource."
  type        = string
  default     = "gp3"  # GP3 is more cost-effective than GP2
}

variable "instance_class" {
  description = "(Optional) Instance class."
  type        = string
  default     = "db.t3.micro"  # T3 for burstable workloads
}
```

## Lifecycle Management

Consider including lifecycle rules:

```hcl
lifecycle {
  create_before_destroy = true
  # prevent_destroy = true  # Consider for production resources
}
```

## Common tfsec Ignores

When security scanning tools flag intentional design decisions, document with inline comments:

```hcl
egress {
  description = "All traffic"
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  #tfsec:ignore:aws-ec2-no-public-egress-sgr
  cidr_blocks = ["0.0.0.0/0"]
}
```

Only use ignores when:
1. The pattern is intentional
2. You've documented why it's needed
3. It's a module design decision (e.g., VPC endpoints need broad egress)
