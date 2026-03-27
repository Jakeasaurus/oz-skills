---
name: cloud-wan-test-attachment
description: Workflow for attaching VPCs to AWS Cloud WAN core networks cross-account using the module_cloud_wan branch of terraform-modules. Use when working on Cloud WAN VPC attachments, connect attachments, or SD-WAN connectivity in aws_dev_blend or similar repos that source from the module_cloud_wan branch. Covers pre-flight checks, known issues, fixes, and state management patterns specific to this branch and infrastructure.
---

# Cloud WAN Test Attachment

Workflow for testing cross-account Cloud WAN VPC attachments using `github.com/zachreborn/terraform-modules//modules/aws/cloud_wan/vpc_attachment?ref=module_cloud_wan` as the module source.

## Pre-flight Checklist

Before planning or applying, run these checks to avoid known issues.

### 1. Check module_cloud_wan branch freshness

```bash
git -C /Users/Jacobj/Documents/projects/terraform-modules fetch origin
git --no-pager -C /Users/Jacobj/Documents/projects/terraform-modules log --oneline main ^module_cloud_wan | wc -l
```

If behind by more than 0 commits, rebase before proceeding:

```bash
git -C /Users/Jacobj/Documents/projects/terraform-modules checkout module_cloud_wan
git -C /Users/Jacobj/Documents/projects/terraform-modules rebase origin/main
git -C /Users/Jacobj/Documents/projects/terraform-modules push origin module_cloud_wan --force-with-lease
```

**Known rebase conflict**: The `modules/aws/ram/` files conflict with a file mode difference (755 vs 644) but have identical content. Just `git add modules/aws/ram/` and `git rebase --continue`.

### 2. Refresh module cache after any rebase

```bash
tofu init -upgrade
```

Always run after rebasing — stale `.terraform/modules/` cache will use the old module code.

### 3. Verify provider version

Check `.terraform.lock.hcl` for the AWS provider version. Known constraints:
- `routing_policy_label` on `aws_networkmanager_vpc_attachment` requires provider **>= 6.28**
- If locked to < 6.28, the attribute must be absent from `modules/aws/cloud_wan/vpc_attachment/main.tf`

See `references/known-issues.md` for details on all version-sensitive attributes.

## Module Sources Used

| Module | Source ref |
|--------|-----------|
| VPC | `module_cloud_wan` |
| Cloud WAN VPC attachment | `module_cloud_wan` |
| Transit Gateway attachment | `v4.2.0` |
| Route | `v4.2.0` |

## State Management Patterns

### Imports (one-time)

Import blocks in `imports.tf` are one-time operations. After `tofu apply` succeeds, delete `imports.tf` and commit the removal.

### Resource renames (moved blocks)

If a module update renames a resource (e.g. `aws_flow_log.this` ↔ `aws_flow_log.vpc_flow`), use a `moved` block in the root rather than an import block. An import block alone does not prevent the old resource from being destroyed.

```hcl
moved {
  from = module.vpc.module.vpc_flow_logs[0].aws_flow_log.this[0]
  to   = module.vpc.module.vpc_flow_logs[0].aws_flow_log.vpc_flow
}
```

A rebase that picks up the rename commit is the permanent fix; the moved block is only needed if applying before the rebase.

## Known Issues

See `references/known-issues.md` for the full list of issues encountered and their fixes.
