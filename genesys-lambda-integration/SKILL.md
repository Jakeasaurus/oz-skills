---
name: genesys-lambda-integration
description: Build and configure AWS Lambda functions for Genesys Cloud Data Actions integrations. Use when creating new Genesys Cloud Lambda integrations, setting up IAM cross-account roles for Genesys, writing Lambda functions that return data to Genesys agent scripts, or configuring Genesys Cloud Data Action output contracts. Covers Terraform IAM module patterns, Lambda JSON response requirements, and Genesys ClickOps setup.
---

# Genesys Cloud Lambda Integration

## Critical: Lambda Response Must Be a JSON Object

Genesys Cloud Data Actions can *display* a plain string response but **cannot bind it to an output variable**. The Lambda must return a named JSON object — not a plain string.

**Wrong:** `"042817"` — Genesys sees it but can't use it as a variable.
**Correct:** `{"OTP":"042817"}` — Genesys maps the `OTP` field to a typed output variable.

See `references/lambda-patterns.md` for Go response struct examples and naming conventions.

## IAM Setup (Terraform)

Genesys Cloud assumes a role in your AWS account via STS — no stored credentials needed.

**Required resources:**
1. `iam/policy` module — scoped to `lambda:InvokeFunction` on the specific function ARN only
2. `iam/role` module — trusted by Genesys Cloud AWS account with `sts:ExternalId` = Genesys org ID

See `references/iam.md` for complete Terraform module patterns, the Genesys AWS account ID, and security notes.

## Genesys Cloud ClickOps

After `tfa`, the `genesys_cloud_role_arn` Terraform output provides the Role ARN needed for setup.

See `references/genesys-clickops.md` for step-by-step Data Action and Script configuration.

## End-to-End Workflow

1. Write the Lambda returning a typed JSON struct (see `references/lambda-patterns.md`)
2. Build the deployment artifact (`./build.sh`)
3. Add Terraform IAM policy + role modules and Lambda module
4. Run `tfa` — copy `genesys_cloud_role_arn` output value
5. Configure Genesys integration + Data Action (see `references/genesys-clickops.md`)
6. Test via the Genesys Data Action test tab — confirm named field is returned
7. Wire into agent Script: button triggers Data Action, label displays the output variable
