# Zach's Review Patterns for Terraform Modules

This document catalogs common feedback patterns from Zach's reviews of Terraform modules to help anticipate and address issues proactively.

## Table of Contents
- [Module Structure and Organization](#module-structure-and-organization)
- [Naming Conventions](#naming-conventions)
- [Variable Design](#variable-design)
- [Dynamic Blocks and For-Each](#dynamic-blocks-and-for-each)
- [Resource Completeness](#resource-completeness)
- [Documentation Requirements](#documentation-requirements)
- [Provider Configuration](#provider-configuration)

## Module Structure and Organization

### Comment Headers
Always add comment headers to major sections to match existing modules:

```hcl
###########################
# Provider Configuration
###########################

###########################
# Locals
###########################

###########################
# VPC DHCP Options Variables
###########################
```

**Why:** Consistency across the module repository makes navigation easier.

### File Organization
Standard module structure:
- `main.tf` - Provider config → locals → primary resource → supporting resources
- `variables.tf` - Input variables with validation
- `outputs.tf` - All useful attributes
- `README.md` - terraform-docs compatible documentation

## Naming Conventions

### Name vs Name Prefix
**Key Decision Rule:** If there could be multiples of something, default to using `name_prefix` as they avoid collisions at the outset. It's rare that we care if the name includes the datetime suffix.

**Example from PR #112:**
```hcl
# Consider whether we want to use `name` or `name_prefix`
# My rule of thumb has been that if there could be multiples of something
# I default to using `name_prefix` as they avoid collisions at the outset.
```

**Resources that typically need `name_prefix`:**
- Load balancers
- Target groups
- Auto-scaling groups
- Security groups

**Resources that typically use fixed `name`:**
- Resources requiring import capability
- Singleton resources per account/region

### Module-Specific Naming
Prefer consistency with existing modules. For example, IAM modules should use `enable_iam_roles` not `iam_roles_enabled` to match other modules.

**Example from PR #164:**
```
Should this be renamed to `enable_iam_roles` to match our other modules?
```

## Variable Design

### Type Consistency
When using dynamic blocks with for_each, ensure the variable type matches the for_each pattern.

**Maps should default to empty map `{}`:**
```hcl
# Correct
for_each = each.value.health_check != null ? each.value.health_check : {}

# Not this
for_each = each.value.health_check != null ? each.value.health_check : []
```

**Lists should default to empty list `[]`:**
```hcl
# Correct  
for_each = var.access_logs != null ? var.access_logs : []

# Not this - unnecessary brackets
for_each = var.access_logs != null ? [var.access_logs] : []
```

**If converting to set is needed, use `toset()` explicitly:**
```hcl
for_each = var.access_logs != null ? toset(var.access_logs) : []
```

**Example from PR #112:**
```
Change this to remove the brackets around var.access_logs.
If we need each type to be a set then we should set that requirement 
within the variable rather than turning the variable into a set this way.
If instead, you do want to take the input of a single object and turn 
it into a set a better more prescriptive way would be to use toset().
```

### Variable Validation
Add validation for enums and restricted values:

```hcl
variable "load_balancer_type" {
  description = "Valid values are application, gateway, or network."
  type        = string
  
  validation {
    condition     = contains(["application", "gateway", "network"], var.load_balancer_type)
    error_message = "load_balancer_type must be application, gateway, or network."
  }
}
```

**Note:** Do NOT use `length()` validation on nullable variables - this causes issues.

### Avoid Length Validation on Nullable Variables
From existing terraform-modules rule:
```
NEVER DO:
- Use length() validation on nullable variables
```

This is a critical pattern - nullable variables with length validation will fail unexpectedly.

## Dynamic Blocks and For-Each

### Conditional Resource Creation
When a resource depends on another resource being enabled AND a related variable being populated, check both conditions:

```hcl
# Check both that feature is enabled AND list is non-empty
count = var.enable_nat_gateway && length(var.private_subnets_list) > 0 ? 1 : 0
```

**Example from PR #131:**
Added `length(var.*_subnets_list) > 0` check in each `aws_route` resource's `count` expression to only create default routes when the NAT gateway is enabled AND the corresponding subnet list is non-empty.

### Mutual Exclusivity
When AWS resources have mutually exclusive parameters, add logic to handle this:

**Example from PR #112:**
```
Subnets and subnet_mappings are mutual exclusive, 
I think this needs some additional logic. Likely on each.
```

## Resource Completeness

### Include All AWS Parameters
When creating a new module, include ALL available AWS parameters from the provider documentation, even if not immediately needed.

**Example from PR #112 - Load Balancer Module Missing Parameters:**
- `client_keep_alive`
- `dns_record_client_routing_policy`
- `enable_tls_version_and_cipher_suite_headers`
- `enable_xff_client_port`
- `enable_zonal_shift`
- `enforce_security_group_inbound_rules_on_private_link_traffic`
- `preserve_host_header`
- `xff_header_processing_mode`
- `dynamic "connection_logs"` block

**Why:** Better to have complete modules from the start rather than adding parameters incrementally as needs arise.

### Check Parameter Availability Across Resource Types
Some parameters are available for multiple load balancer types (application, network, gateway). Don't assume parameters are type-specific without checking documentation.

**Example from PR #112:**
```
Also available for network load balancers. 
Suggest moving to common settings.
```

### Include All Dynamic Blocks
Don't forget optional dynamic blocks like:
- `connection_logs` for load balancers
- `access_logs` configurations
- Health check configurations
- Stickiness settings

## Documentation Requirements

### README.md Standards
Use the module_template README.md as the base and customize:

1. Copy from `module_template/` folder
2. Add real usage examples in the `# Usage` section
3. Include all variables, outputs, and resource documentation
4. Generate with terraform-docs for consistency

**Example from PR #112:**
```
Please copy over from the module_template folder the template README.md file 
and input your examples in the # Usage section.

See https://github.com/zachreborn/terraform-modules/blob/main/modules/aws/cloudfront/README.md 
as an example.
```

### Description Accuracy
Variable descriptions should match actual default values:

**Example from PR #128:**
```
The description indicates 'Defaults True', which conflicts with 
the actual default value of false. Please update the description 
to accurately reflect the default setting.
```

## Provider Configuration

### Standard Provider Block
All modules should include:

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
```

**Note:** Version requirements may vary - check existing modules for current standards. Recent modules use AWS provider >= 6.0.0.

### AWS Provider Version Changes
Be aware of deprecated attributes when upgrading provider versions:

**Example from PR #135:**
- `data.aws_region.current.name` → `data.aws_region.current.region` (AWS provider v6 upgrade)

Update all references consistently across the module.

## Module Reusability and Consolidation

### Avoid Creating Duplicate Modules
If functionality can be added to an existing module with variables, prefer that over creating a new module.

**Example from PR #163:**
```
Let's move this back into the policy and role modules 
instead of unique modules.
```

Consider whether new functionality warrants a separate module or should be integrated into existing modules with feature flags.

## Common Patterns from Existing Modules

### Review These Reference Modules
Before creating a new module, review these for patterns:
- `cloudfront` - Comprehensive documentation example
- `lb` - Complex dynamic blocks and multiple resource types
- `transit_gateway` - Advanced networking patterns
- `vpc` - Conditional resource creation

### DRY Principle
Use dynamic blocks and variable-driven lists instead of duplicating code:
- Group similar ingress/egress rules into lists
- Use for_each for multiple similar resources
- Leverage locals for computed values used multiple times

### Secure Defaults
Always set secure defaults:
- `publicly_accessible = false`
- `encrypted = true`
- `enable_deletion_protection = true` (for production resources)

## Integration with Existing Infrastructure

### Module Path References
When working with local modules:
- Local source: `/Users/Jacobj/Documents/projects/terraform-modules`
- Remote source: `github.com/zachreborn/terraform-modules`
- Always use latest source version unless otherwise specified

### Testing Before PR
Include successful Terraform run links in PR comments demonstrating:
1. Initial resource creation
2. Modifications/updates  
3. Any edge cases or special configurations

**Example pattern from PRs:**
```
Tested branch here:
https://app.terraform.io/app/SLFCU/workspaces/aws_dev_sandbox/runs/run-xxxxx
```
