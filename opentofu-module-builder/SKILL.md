---
name: opentofu-module-builder
description: Build production-ready OpenTofu/Terraform modules for AWS following established patterns from terraform-modules repository. Use when creating new infrastructure modules, refactoring existing modules, or extending module capabilities for AWS resources.
---

# OpenTofu Module Builder

Build production-ready OpenTofu/Terraform modules for AWS that follow established patterns and best practices.

## Repository Context

**Local Repository**: `/Users/Jacobj/Documents/projects/terraform-modules`
**Remote Repository**: `https://github.com/zachreborn/terraform-modules`
**Provider**: AWS Provider >= 6.0.0
**Terraform/OpenTofu**: >= 1.0.0

All modules are stored in `modules/aws/` subdirectory.

## Module Creation Workflow

### 1. Research the AWS Resource

Before writing any code, thoroughly research the AWS service:

1. Search OpenTofu AWS provider documentation at `https://search.opentofu.org/provider/hashicorp/aws/latest`
   - Find the specific resource page (e.g., `/docs/resources/vpc`, `/docs/resources/rds_instance`)
   - Review all available parameters, their types, and AWS behavior
   - Check for nested configuration blocks
   - Note deprecated parameters to avoid

2. Understand resource dependencies:
   - What other AWS resources does this typically work with?
   - Are there supporting resources that should be included? (e.g., security groups, IAM roles)
   - Can this resource stand alone or does it need other modules?

3. Review existing similar modules in the repository for patterns

### 2. Determine Module Scope

Decide the module's complexity based on resource characteristics:

**Simple Resource Wrapper** (like `eip` module):
- Resource is simple and self-contained
- Few configuration options
- No or minimal supporting resources
- Other resources may reference it independently

**Complex Module** (like `vpc` or `cloudfront`):
- Resource has many configuration options
- Includes multiple supporting resources
- Benefits from encapsulating related resources together
- Complex nested configuration blocks

**Module with Sub-modules** (like `transit_gateway/*`):
- Large service with multiple logical components
- Each component can be used independently
- Split into subdirectories: `tgw/`, `attachment/`, `route/`, etc.

### 3. Create Module Structure

Create the module directory and files:

```bash
cd /Users/Jacobj/Documents/projects/terraform-modules/modules/aws
mkdir <module-name>
cd <module-name>
touch main.tf variables.tf outputs.tf README.md
```

For complex modules with sub-modules:
```bash
mkdir <module-name>/{submodule1,submodule2}
```

### 4. Build main.tf

Start with the most foundational resource and work outward. Consult `references/module-patterns.md` for structure.

**Order of Implementation**:
1. Provider configuration block
2. Data sources (if needed for region, account ID, etc.)
3. Locals (for computed values)
4. Primary resource
5. Supporting resources in logical dependency order

**Key Patterns**:
- Use dynamic blocks for repeatable nested configuration (see module-patterns.md)
- Use `count` for binary enable/disable resources
- Use `for_each` for multiple similar resources
- Use `merge(tomap({ Name = var.name }), var.tags)` for resource tags
- Include inline comments for CIDR blocks and availability zones
- Group related resources with comment headers

**Example skeleton**:
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
data "aws_region" "current" {}

###########################
# Locals
###########################
locals {
  # Computed values here
}

###########################
# Module Configuration
###########################
resource "aws_<service>_<resource>" "this" {
  # Primary resource configuration
}

###########################
# Supporting Resources
###########################
# Optional/conditional supporting resources
```

### 5. Build variables.tf

Define all input variables with appropriate types, defaults, and validation. Consult `references/aws-best-practices.md` for security defaults.

**Variable Organization**:
```hcl
###########################
# Primary Resource Variables
###########################
# Variables for the main resource

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

**Variable Best Practices**:
- Start descriptions with `(Required)` or `(Optional)` matching AWS API style
- Use descriptive names matching AWS parameter names
- Set secure defaults (see aws-best-practices.md)
- Add validation blocks for constrained values
- Use `null` for truly optional parameters (not empty strings)
- Document inline for complex types
- Prefer specific types over `any`

**Validation Examples**:
```hcl
variable "instance_tenancy" {
  description = "(Optional) A tenancy option for instances"
  type        = string
  default     = "default"
  validation {
    condition     = can(regex("^(default|dedicated)$", var.instance_tenancy))
    error_message = "instance_tenancy must be either default or dedicated"
  }
}

variable "retention_days" {
  description = "(Optional) Number of days to retain"
  type        = number
  default     = 90
  validation {
    condition     = can(index([1, 3, 5, 7, 14, 30, 60, 90, 120, 180, 365, 0], var.retention_days))
    error_message = "retention_days must be one of: 1, 3, 5, 7, 14, 30, 60, 90, 120, 180, 365, 0."
  }
}
```

### 6. Build outputs.tf

Export all useful resource attributes that consumers might need:

```hcl
###########################
# Resource Outputs
###########################
output "arn" {
  description = "ARN of the resource"
  value       = aws_<service>_<resource>.this.arn
}

output "id" {
  description = "ID of the resource"
  value       = aws_<service>_<resource>.this.id
}

# Add all other useful attributes
```

**Output Guidelines**:
- Export ARN, ID, and name at minimum
- Include DNS names, endpoints, URLs when available
- Export attributes that other modules might reference
- Use clear, consistent descriptions

### 7. Create README.md

Create documentation with terraform-docs markers:

```markdown
<!-- Blank module readme template: Do a search and replace with your text editor for the following: `module_name`, `module_description` -->
<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->

<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/zachreborn/terraform-modules">
    <img src="/images/terraform_modules_logo.webp" alt="Logo" width="500" height="500">
  </a>

<h3 align="center">Module Title</h3>
  <p align="center">
    Brief description of what this module creates.
    <br />
    <a href="https://github.com/zachreborn/terraform-modules"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://zacharyhill.co">Zachary Hill</a>
    ·
    <a href="https://github.com/zachreborn/terraform-modules/issues">Report Bug</a>
    ·
    <a href="https://github.com/zachreborn/terraform-modules/issues">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#requirements">Requirements</a></li>
    <li><a href="#providers">Providers</a></li>
    <li><a href="#modules">Modules</a></li>
    <li><a href="#Resources">Resources</a></li>
    <li><a href="#inputs">Inputs</a></li>
    <li><a href="#outputs">Outputs</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## Usage

### Example Scenario Name

Describe the use case for this example.

```hcl
module "example" {
  source = "github.com/zachreborn/terraform-modules//modules/aws/<module-name>"

  # Required variables
  required_var = "value"
  
  # Optional variables
  optional_var = "value"
}
```

_For more examples, please refer to the [Documentation](https://github.com/zachreborn/terraform-modules)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- terraform-docs output will be input automatically below-->
<!-- terraform-docs markdown table --output-file README.md --output-mode inject .-->
<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->

<!-- LICENSE -->

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

Zachary Hill - [![LinkedIn][linkedin-shield]][linkedin-url] - zhill@zacharyhill.co

Project Link: [https://github.com/zachreborn/terraform-modules](https://github.com/zachreborn/terraform-modules)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

- [Zachary Hill](https://zacharyhill.co)
- [Jake Jones](https://github.com/jakeasarus)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/zachreborn/terraform-modules.svg?style=for-the-badge
[contributors-url]: https://github.com/zachreborn/terraform-modules/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/zachreborn/terraform-modules.svg?style=for-the-badge
[forks-url]: https://github.com/zachreborn/terraform-modules/network/members
[stars-shield]: https://img.shields.io/github/stars/zachreborn/terraform-modules.svg?style=for-the-badge
[stars-url]: https://github.com/zachreborn/terraform-modules/stargazers
[issues-shield]: https://img.shields.io/github/issues/zachreborn/terraform-modules.svg?style=for-the-badge
[issues-url]: https://github.com/zachreborn/terraform-modules/issues
[license-shield]: https://img.shields.io/github/license/zachreborn/terraform-modules.svg?style=for-the-badge
[license-url]: https://github.com/zachreborn/terraform-modules/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/zachary-hill-5524257a/
[product-screenshot]: /images/screenshot.webp
[Terraform.io]: https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform
[Terraform-url]: https://terraform.io
```

The `<!-- BEGIN_TF_DOCS -->` and `<!-- END_TF_DOCS -->` markers tell terraform-docs where to inject documentation. GitHub Actions will handle this automatically.

### 8. Testing the Module

Create a test configuration to validate the module:

**Option A: External Test Repository**
Call the module from another repository to test it (typical workflow).

**Option B: Local Test Directory**
Create a `tests/` or `examples/` directory within the module:

```bash
mkdir tests
cd tests
```

Create a test configuration:

```hcl
# tests/basic.tf
module "test" {
  source = "../"  # Reference parent module
  
  # Provide test values for required variables
  name = "test-resource"
  
  # Test optional features
  tags = {
    environment = "test"
    terraform   = "true"
  }
}

output "test_output" {
  value = module.test
}
```

**Testing Steps**:
1. Initialize: `tofu init` or `terraform init`
2. Validate syntax: `tofu validate`
3. Generate plan: `tofu plan`
4. Review the speculative plan for correctness
5. If plan succeeds and looks correct, module structure is valid

Do NOT apply in tests - the goal is validation only.

### 9. OpenTofu-Specific Considerations

When creating modules, consider OpenTofu features that may differ from or enhance Terraform:

**State Encryption**: OpenTofu offers end-to-end state encryption. Document if the module benefits from this.

**Enhanced Functions**: Check OpenTofu documentation for newer functions that might simplify logic.

**Provider Features**: Verify the AWS provider version supports the resources you're using. OpenTofu maintains compatibility with Terraform providers.

**Version Pinning**: Use `>= 1.0.0` for broad compatibility, but test with current OpenTofu versions.

If you discover OpenTofu-specific features that would improve the module, document them as comments for future enhancement.

## Module Complexity Guidelines

When deciding how to structure a module:

**Create a Simple Wrapper When**:
- Resource is simple (few parameters)
- No mandatory supporting resources
- Other resources need to reference it independently
- Example: `eip`, `keypair`

**Build a Complex Module When**:
- Resource requires many related supporting resources
- Configuration is intricate with many nested blocks
- Consumers benefit from encapsulation
- Example: `vpc` (includes subnets, route tables, gateways, endpoints)

**Use Sub-modules When**:
- Service has distinct logical components
- Components can be used independently
- Improves organization and maintainability
- Example: `transit_gateway/tgw`, `transit_gateway/attachment`

## Checklist

Before considering a module complete:

- [ ] Researched AWS resource in OpenTofu provider documentation
- [ ] Created proper file structure (main.tf, variables.tf, outputs.tf, README.md)
- [ ] Followed established patterns from references/module-patterns.md
- [ ] Set secure defaults per references/aws-best-practices.md
- [ ] Added validation blocks where appropriate
- [ ] Used dynamic blocks for repeatable configuration
- [ ] Included helpful inline comments
- [ ] Created comprehensive outputs
- [ ] Added usage examples to README.md
- [ ] Included terraform-docs markers in README
- [ ] Tested with `tofu validate`
- [ ] Generated and reviewed `tofu plan`
- [ ] Verified all provider parameters are current (not deprecated)

## Common Patterns Quick Reference

**Enable/Disable Optional Resource**:
```hcl
resource "aws_resource" "optional" {
  count = var.enable_feature ? 1 : 0
  # configuration
}
```

**Multiple Resources from List**:
```hcl
resource "aws_subnet" "private" {
  for_each   = toset(var.private_subnets)
  cidr_block = each.value
}
```

**Conditional Nested Blocks**:
```hcl
dynamic "custom_config" {
  for_each = var.custom_config != null ? [true] : []
  content {
    # configuration from var.custom_config
  }
}
```

**Resource Tags**:
```hcl
tags = merge(tomap({ Name = var.name }), var.tags)
```

## Reference Documents

For detailed patterns and best practices, read:
- `references/module-patterns.md` - Established coding patterns
- `references/aws-best-practices.md` - Security and AWS-specific defaults
