---
name: zach-review
description: Proactively review Terraform modules against Zach's feedback patterns before submitting PRs to terraform-modules repository. Use when creating or modifying Terraform modules in the terraform-modules repo, preparing PRs for review, or when asked to check module code against Zach's standards and common review feedback.
---

# Zach Review

Proactively identify and address common issues in Terraform modules based on historical review feedback patterns from the terraform-modules repository.

## When to Apply This Skill

Apply this review when:
- Creating a new Terraform module
- Modifying an existing module before submitting a PR
- Asked to review module code against Zach's standards
- Preparing code for the terraform-modules repository

## Review Process

### 1. Load Review Patterns
Read the comprehensive review patterns reference:
```bash
read_files references/review-patterns.md
```

### 2. Review Checklist

Apply these checks in order:

#### Module Structure
- [ ] Comment headers present for all major sections (Provider, Locals, Variables)
- [ ] File organization follows standard: main.tf → variables.tf → outputs.tf → README.md
- [ ] Provider configuration block included with correct version requirements

#### Naming
- [ ] Resources use `name_prefix` if multiples could exist (LBs, target groups, ASGs, SGs)
- [ ] Fixed `name` only used for import-capable or singleton resources
- [ ] Variable names consistent with other modules (e.g., `enable_iam_roles`)

#### Variables
- [ ] Type consistency: maps default to `{}`, lists to `[]`
- [ ] No unnecessary wrapping in brackets or sets (use `toset()` explicitly if needed)
- [ ] Validation blocks for enum values using `contains()`
- [ ] NO `length()` validation on nullable variables
- [ ] Descriptions match actual default values

#### Dynamic Blocks and Conditionals
- [ ] Conditional resources check ALL required conditions (e.g., feature enabled AND list non-empty)
- [ ] Mutually exclusive parameters handled with proper logic
- [ ] for_each types match variable types (map→map, list→list)

#### Resource Completeness
- [ ] ALL AWS parameters from provider docs included (even if not immediately needed)
- [ ] All optional dynamic blocks included (access_logs, connection_logs, health_check, stickiness)
- [ ] Parameters not assumed to be type-specific without checking docs

#### Documentation
- [ ] README.md copied from module_template and customized
- [ ] Real usage examples in # Usage section
- [ ] Variable descriptions accurate
- [ ] terraform-docs markers present (automated by PR workflow)

#### Security and Best Practices
- [ ] Secure defaults: `publicly_accessible = false`, `encrypted = true`
- [ ] DRY principle: lists and for_each instead of duplication
- [ ] Locals used for computed values used multiple times

### 3. Reference Module Review

Before finalizing, compare against these reference modules for patterns:
- `cloudfront` - Documentation standards
- `lb` - Complex dynamic blocks
- `transit_gateway` - Advanced patterns
- `vpc` - Conditional resource creation

### 4. Report Findings

Provide findings in this format:

**Structure Issues:**
- List any missing comment headers, incorrect file organization

**Naming Issues:**
- Identify name vs name_prefix decisions
- Flag inconsistent variable naming

**Variable Issues:**
- Type mismatches with for_each usage
- Missing validation blocks
- Length validation on nullable variables

**Completeness Issues:**
- Missing AWS parameters (compare to provider docs)
- Missing dynamic blocks
- Parameters that work across multiple resource types

**Documentation Issues:**
- README not following template
- Missing or incorrect examples
- Description/default mismatches

**Recommendations:**
- Specific code changes needed
- Reference to similar implementations in existing modules

## Advanced Usage

### Compare Against Specific Module
When reviewing, reference similar existing modules:
```bash
# Example: reviewing a new RDS module
read_files modules/aws/redshift/main.tf modules/aws/redshift/variables.tf
```

### Check AWS Provider Documentation
For new resources, verify all parameters are included:
1. Identify the AWS resource type (e.g., `aws_lb`)
2. Check Terraform AWS provider docs for that resource
3. Compare module parameters against full provider parameter list

### Pattern Recognition
Common patterns to watch for:
- **Name prefix pattern**: Load balancers, target groups → always use name_prefix
- **Type consistency pattern**: Maps with for_each must default to `{}`
- **Completeness pattern**: New modules often missing 5-10 optional parameters
- **Mutual exclusivity pattern**: subnets vs subnet_mappings require conditional logic

## Notes

This skill is based on analysis of 20+ PRs from the terraform-modules repository spanning 2024-2026, with particular focus on detailed feedback from PRs #112, #127, #131, #163 which had extensive review comments.

The patterns documented reflect Zach's consistent preferences for:
- Module completeness over minimal implementation
- Consistency across the module repository
- Type safety and validation
- Comprehensive documentation
- Secure defaults
