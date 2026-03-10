# Module Patterns Reference

This document captures established patterns from the terraform-modules repository.

## Module Structure Standard

Every module follows this file organization:

```
module-name/
├── main.tf           # Provider config, data sources, locals, resources
├── variables.tf      # All input variables with validation
├── outputs.tf        # All useful resource attributes
└── README.md         # Usage examples + terraform-docs injection
```

## File Organization Pattern

### main.tf Structure

Files are organized with comment headers in this order:

```hcl
###########################
# Provider Configuration
###########################
terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0.0"
    }
  }
}

###########################
# Data Sources
###########################
# Place data sources here (e.g., aws_caller_identity, aws_region)

###########################
# Locals
###########################
# Local values for computed configuration

###########################
# Module Configuration
###########################
# Primary resources here

###########################
# Supporting Resources
###########################
# Optional/conditional supporting resources
```

### variables.tf Structure

Variables are grouped with comment headers:

```hcl
###########################
# Primary Resource Variables
###########################
# Variables for main resource configuration

###########################
# Supporting Resource Variables  
###########################
# Variables for optional/supporting resources

###########################
# General Variables
###########################
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

### outputs.tf Structure

```hcl
###########################
# Resource Outputs
###########################
output "arn" {
  description = "ARN of the resource"
  value       = aws_resource.this.arn
}

output "id" {
  description = "ID of the resource"
  value       = aws_resource.this.id
}
```

## Variable Patterns

### Naming Convention
- Use fixed resource names (no `name_prefix`) to enable import capability
- Use descriptive variable names matching AWS parameter names
- Include AWS documentation references in descriptions

### Description Format
```hcl
variable "example" {
  description = "(Optional/Required) AWS-style description of the parameter."
  type        = string
  default     = "sensible-default"
}
```

### Default Values
- Set secure defaults: `publicly_accessible = false`, `encrypted = true`
- Use `null` for truly optional parameters
- Provide working examples in defaults for complex types

### Validation Blocks
Add validation when:
- Value must be from a constrained set
- Value format matters (e.g., CIDR blocks, durations)
- Early failure prevents costly apply errors

```hcl
variable "instance_tenancy" {
  description = "(Optional) A tenancy option for instances launched into the VPC"
  type        = string
  default     = "default"
  validation {
    condition     = can(regex("^(default|dedicated)$", var.instance_tenancy))
    error_message = "instance_tenancy must be either default or dedicated"
  }
}
```

## Dynamic Block Patterns

Use dynamic blocks for repeatable nested configuration:

```hcl
dynamic "origin" {
  for_each = var.origins != null ? var.origins : {}
  content {
    connection_attempts = origin.value.connection_attempts
    domain_name        = origin.value.domain_name
    origin_id          = origin.key
    # Additional attributes...
  }
}
```

### Nested Dynamic Blocks
For optional sub-blocks within dynamic blocks:

```hcl
dynamic "origin" {
  for_each = var.origins != null ? var.origins : {}
  content {
    domain_name = origin.value.domain_name
    
    dynamic "custom_origin_config" {
      for_each = origin.value.custom_origin_config != null ? [true] : []
      content {
        http_port              = origin.value.custom_origin_config.http_port
        origin_protocol_policy = origin.value.custom_origin_config.origin_protocol_policy
      }
    }
  }
}
```

## Variable Type Patterns

### Simple Types
```hcl
variable "enabled" {
  description = "(Optional) Whether the resource is enabled."
  type        = bool
  default     = true
}

variable "instance_count" {
  description = "(Optional) Number of instances to create."
  type        = number
  default     = 1
}
```

### List with Inline Comments
```hcl
variable "private_subnets_list" {
  description = "A list of private subnets inside the VPC."
  type        = list(string)
  default     = [
    "10.11.1.0/24",   # us-east-2a
    "10.11.2.0/24",   # us-east-2b
    "10.11.3.0/24"    # us-east-2c
  ]
}
```

### Complex Object Types
```hcl
variable "origins" {
  description = "(Required) One or more origins for this distribution."
  type = map(object({
    domain_name              = string               # The DNS domain name
    connection_attempts      = optional(number, 3)  # Defaults to 3
    origin_access_control_id = optional(string)     # Optional parameter
    custom_origin_config = optional(object({
      http_port                = optional(number, 80)
      origin_protocol_policy   = optional(string, "http-only")
    }))
  }))
}
```

## Count vs For_Each Patterns

### Use `count` for binary on/off resources
```hcl
resource "aws_vpc_endpoint" "ssm" {
  count = var.enable_ssm_vpc_endpoints ? 1 : 0
  # configuration...
}
```

### Use `for_each` for multiple similar resources
```hcl
resource "aws_subnet" "private_subnets" {
  for_each          = toset(var.private_subnets_list)
  availability_zone = element(var.azs, index(var.private_subnets_list, each.value))
  cidr_block        = each.value
  vpc_id            = aws_vpc.vpc.id
  tags              = merge(tomap({ Name = "${var.name}_private_${element(var.azs, index(var.private_subnets_list, each.value))}" }), var.tags)
}
```

## Resource Naming Pattern

Use `merge()` with `tomap()` for resource names:

```hcl
tags = merge(tomap({ Name = var.name }), var.tags)
```

This allows the Name tag to be overridden by user-provided tags if needed.

## Data Source Usage

Common data sources to include:

```hcl
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {}
```

Reference with:
```hcl
service_name = "com.amazonaws.${data.aws_region.current.region}.s3"
```

## Module Composition

Modules can call other modules:

```hcl
module "vpc_flow_logs" {
  source = "../../flow_logs"
  
  count                        = var.enable_flow_logs ? 1 : 0
  cloudwatch_name_prefix       = var.cloudwatch_name_prefix
  cloudwatch_retention_in_days = var.cloudwatch_retention_in_days
  flow_traffic_type            = var.flow_traffic_type
  flow_transit_gateway_ids     = [aws_ec2_transit_gateway.transit_gateway.id]
  tags                         = var.tags
}
```

## README.md Pattern

Every README follows this template:

```markdown
# Module Name

<h3 align="center">Module Title</h3>
  <p align="center">
    Brief description of what this module creates.
  </p>

## Usage

### Example Name

Description of this example scenario.

\`\`\`hcl
module "example" {
  source = "github.com/zachreborn/terraform-modules//modules/aws/module-name"
  
  # Required variables
  required_var = "value"
  
  # Optional variables
  optional_var = "value"
}
\`\`\`

<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
```

The `<!-- BEGIN_TF_DOCS -->` markers tell terraform-docs where to inject documentation.
