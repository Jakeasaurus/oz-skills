# Cloud WAN Attachment — Known Issues & Fixes

Issues encountered when working with `module_cloud_wan` and `aws_dev_blend`.

---

## 1. module_cloud_wan branch behind main

**Symptom**: Plan errors from missing fixes, deprecated attributes, or resource renames that exist on `main` but not on `module_cloud_wan`.

**Root cause**: `module_cloud_wan` diverged from `main` at an early commit and doesn't receive upstream fixes automatically.

**Fix**: Rebase onto `origin/main`. See SKILL.md pre-flight section.

**Known rebase conflict**: `modules/aws/ram/` — file mode difference only (755 vs 644), content identical. `git add modules/aws/ram/ && GIT_EDITOR=true git rebase --continue`.

---

## 2. aws_flow_log resource renamed between module versions

**Symptom**:
```
module.vpc.module.vpc_flow_logs[0].aws_flow_log.this[0] will be destroyed
module.vpc.module.vpc_flow_logs[0].aws_flow_log.vpc_flow will be created
```

**Root cause**: Zach renamed `aws_flow_log.vpc_flow` → `aws_flow_log.this` in commit `b73470da` ("bugfix: fix flow logs and tgw attachment #94") on `main`. `module_cloud_wan` diverged before this commit, so it still uses `vpc_flow`. When bumping the VPC module ref from a tagged version (which has `this`) to `module_cloud_wan` (which has `vpc_flow`), state sees a destroy+create.

**Fix**: Rebase `module_cloud_wan` onto `main` (picks up the rename). The destroy+create disappears because both the module and state now use `this`.

**Do NOT use import blocks here** — importing `vpc_flow` while `this[0]` is still in state causes a conflict (same AWS resource ID being destroyed and imported simultaneously). Use a `moved` block if you need to apply before the rebase.

---

## 3. routing_policy_label unsupported in AWS provider < 6.28

**Symptom**:
```
Error: Unsupported argument
  on .terraform/modules/cloud_wan_vpc_attachment/.../main.tf line 22:
  22:   routing_policy_label = each.value.routing_policy_label
An argument named "routing_policy_label" is not expected here.
```

**Root cause**: `routing_policy_label` was added to `aws_networkmanager_vpc_attachment` in AWS provider PR #45246 (released ~6.28). The current lock file pins 6.22.0. Even though the module requires `>= 6.0.0`, the feature didn't exist at 6.22.0 — the constraint is a floor, not a feature guarantee.

**Fix (short-term)**: Remove `routing_policy_label = each.value.routing_policy_label` from `modules/aws/cloud_wan/vpc_attachment/main.tf`. The variable definition stays in `variables.tf` for future use.

**Fix (long-term)**: Upgrade the AWS provider lock to >= 6.28 and update the module constraint to `>= 6.28.0`. Run `tofu init -upgrade` in the consuming repo.

---

## 4. enable_igw logic bug with empty public_subnets_list (fixed in #187)

**Symptom**:
```
Error: Invalid index
  on .terraform/modules/vpc/modules/aws/vpc/main.tf line 281:
  281:   route_table_id = aws_route_table.public_route_table[0].id
aws_route_table.public_route_table is empty tuple
```

**Root cause**: The `enable_igw` local used `(length(list) != 0 || list != null)` — an empty list `[]` is never null, so the `|| list != null` arm always returned `true`, making `enable_igw = true` even when `public_subnets_list = []`. Meanwhile `public_route_table` used `length != 0` for its count (= 0), while `public_default_route` used `enable_igw` (= 1), so the route tried to reference a route table that didn't exist. A `# !FIX` comment at line 276 noted the inconsistency.

**Fix** (applied in `module_cloud_wan`, tracked in zachreborn/terraform-modules#187):
```hcl
# Before (buggy)
enable_igw = var.enable_internet_gateway ? ((length(var.public_subnets_list) != 0 || var.public_subnets_list != null) ? true : false) : false

# After (fixed)
enable_igw = var.enable_internet_gateway && length(var.public_subnets_list) != 0
```
Also aligned `public_route_table` count to use `local.enable_igw ? 1 : 0`.

**Triggered by**: Rebasing `module_cloud_wan` onto `main`, which picks up commit `0e8f64b0` ("VPC Module - Allow disabling of the internet gateway #107"). That commit introduced the count-based logic but had the bug. Requires `tofu init -upgrade` after rebase to pull fresh module.

---

## 5. Stale .terraform module cache after rebase

**Symptom**: Error references the old module code even after rebasing and pushing `module_cloud_wan`.

**Fix**: Always run `tofu init -upgrade` after rebasing the module source branch. OpenTofu caches modules locally and won't re-fetch without `-upgrade`.

---

## 6. GPG commit signing fails in non-interactive shell

**Symptom**: `git commit` silently exits with code 1 when run via an agent tool call.

**Root cause**: `commit.gpgsign=true` is configured globally. The GPG agent needs a TTY for `pinentry` to prompt for a passphrase. Non-interactive shells have no TTY, so signing silently fails if the passphrase isn't already cached.

**Fix**: Install `pinentry-mac` so macOS Keychain caches the passphrase permanently after first interactive use:
```bash
brew install pinentry-mac
echo "pinentry-program $(which pinentry-mac)" >> ~/.gnupg/gpg-agent.conf
gpgconf --kill gpg-agent
```
After one interactive `git commit` in a terminal, the passphrase is cached in Keychain and agent tool calls will succeed.

**Workaround**: If pinentry-mac is not set up, commit manually in the terminal when the agent's commit fails.
