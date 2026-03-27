# IAM Terraform Patterns — Genesys Cloud Lambda Integration

## Genesys Cloud AWS Account IDs

| Region Type | Account ID |
|---|---|
| Core / Satellite (us-west-2, us-east-1, etc.) | `765628985471` |
| FedRAMP (us-east-2) | `325654371633` |

## How It Works

Genesys Cloud assumes a role in your AWS account using STS (`sts:AssumeRole`). No access keys or stored credentials are needed. The `sts:ExternalId` condition prevents confused deputy attacks by ensuring only your specific Genesys org can assume the role.

## Terraform Pattern

Uses `zachreborn/terraform-modules` IAM modules. Always use the latest version tag.

```hcl
################################################################
# Genesys Cloud Integration - IAM
# Allows Genesys Cloud to assume a role in this account to
# invoke the Lambda. ExternalId = Genesys org ID (confused
# deputy prevention).
################################################################

module "genesys_cloud_<function_name>_invoke_policy" {
  source = "github.com/zachreborn/terraform-modules//modules/aws/iam/policy?ref=v8.10.0"

  name        = "genesys-cloud-<function_name>-invoke"
  description = "Allows Genesys Cloud to invoke the <function_name> Lambda function"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = module.<function_name>.arn
    }]
  })
  tags = {
    terraform   = "true"
    created_by  = "terraform"
    environment = "prod"
    role        = "utility"
  }
}

module "genesys_cloud_<function_name>_role" {
  #checkov:skip=CKV_AWS_61:Genesys Cloud requires sts:AssumeRole on a specific external account
  # principal (765628985471) with sts:ExternalId condition - not a wildcard trust policy
  source = "github.com/zachreborn/terraform-modules//modules/aws/iam/role?ref=v8.10.0"

  name        = "genesys-cloud-<function_name>"
  description = "Assumed by Genesys Cloud to invoke the <function_name> Lambda function"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::765628985471:root" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "sts:ExternalId" = var.genesys_org_id
        }
      }
    }]
  })
  policy_arns = [module.genesys_cloud_<function_name>_invoke_policy.arn]
  tags = {
    terraform   = "true"
    created_by  = "terraform"
    environment = "prod"
    role        = "utility"
  }
}
```

## Required Variable

Add to `variables.tf`:

```hcl
variable "genesys_org_id" {
  type        = string
  description = "Genesys Cloud organization ID used as the External ID in the IAM trust policy to prevent confused deputy attacks"
  default     = "<org-uuid>"
}
```

Find the org ID: Genesys Cloud → Admin → Organization Settings → Organization Details.

## Required Output

Add to `outputs.tf` — this is what you paste into Genesys Cloud when setting up the integration:

```hcl
output "genesys_cloud_role_arn" {
  description = "IAM Role ARN to paste into Genesys Cloud AWS Lambda integration credentials"
  value       = module.genesys_cloud_<function_name>_role.arn
}
```

## Lambda Execution Role

The Lambda also needs its own execution role (separate from the Genesys invocation role):

```hcl
module "<function_name>_lambda_role" {
  source = "github.com/zachreborn/terraform-modules//modules/aws/iam/role?ref=v8.10.0"

  name        = "<function_name>_lambda"
  description = "IAM role for the <function_name> Lambda function"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
  policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
  tags = {
    terraform   = "true"
    created_by  = "terraform"
    environment = "prod"
    role        = "utility"
  }
}
```

## Checkov Notes

- **CKV_AWS_61** will flag the Genesys trust policy as a false positive. Add the `#checkov:skip` comment inside the module block (not before it) as shown above.
- **CKV2_AWS_5** may flag security groups defined in submodules as unattached. Add a skip with explanation if the SG is attached in a parent module.
