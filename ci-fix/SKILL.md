---
name: ci-fix
description: Diagnose and fix GitHub Actions CI failures. Inspects workflow runs and logs, identifies root causes, implements minimal fixes, and pushes to a fix branch. Use when CI is failing, red, broken, or needs diagnosis.
license: MIT
---

# CI Fix

Diagnose CI failures and implement fixes with minimal, targeted diffs. Pushes fixes to a dedicated branch without creating PRs.

## Prerequisites

Verify GitHub CLI authentication before proceeding:

```bash
gh auth status
```

If not authenticated, instruct the user to run `gh auth login` first.

## Workflow

### 1. Locate the Failing Run

Determine the failing workflow run. If working on a PR branch:

```bash
gh pr view --repo <owner>/<repo> --json statusCheckRollup --jq '.statusCheckRollup[] | {name: .name, conclusion: .conclusion, state: .state}'
```

If working from a branch or run ID:

```bash
gh run list --repo <owner>/<repo> --branch <branch> --status failure --limit 5
```

### 2. Extract Failure Logs

Pull logs from failed steps to identify the root cause:

```bash
gh run view <run-id> --repo <owner>/<repo> --log-failed
```

**If `--log-failed` returns empty** (logs expired or run was a rerun), use one of these fallbacks:

```bash
# Option A: Rerun failed jobs to get a fresh run with accessible logs
gh run rerun <run-id> --repo <owner>/<repo> --failed

# Option B: Download the log ZIP and extract
gh api repos/<owner>/<repo>/actions/runs/<run-id>/logs > /tmp/run_logs.zip
unzip -p /tmp/run_logs.zip "0_Linter.txt" | grep -E "ERROR|NOTICE|failed|passed"
```

For targeted inspection of what passed vs. failed:

```bash
gh run view <run-id> --repo <owner>/<repo> --log-failed 2>&1 | grep -E "Errors found|Successfully linted"
```

### 3. Analyze and Plan — Present Before Implementing

**Before making any changes**, analyze all failures and present a categorized plan to the user. Do not start editing files until the plan is approved.

Group failures by fix strategy:

- **Direct code fix**: Typos, syntax errors, missing braces — fix in source
- **By design**: The code does what it's supposed to; the check is a false positive for this repo type (e.g., a reusable module library where callers control security posture)
- **Configurable by caller**: Static analysis can't see how callers set variables; suppress at the config level
- **Workflow/config change**: Update CI config, add ignore files, adjust permissions

Identify common failure patterns:

- **Build/compilation errors**: Missing dependencies, syntax issues, unclosed blocks
- **Test failures**: Assertion failures, timeouts, flaky tests
- **Linting/formatting**: Style violations, unused imports
- **Security scanners**: Checkov, Trivy, Zizmor — often require ignore configs for module repos
- **Environment issues**: Missing secrets, permissions, resource limits

### 4. Implement the Fix

Make minimal, scoped changes matching the repository's existing style.

#### Checkov on Reusable Module Repos

When Checkov fires extensively on a Terraform module library, the right approach is a centralized `.checkov.yaml` skip list — **not** inline `# checkov:skip` comments scattered across 50+ files. Group skips by rationale:

```yaml
skip-check:
  # BY DESIGN: module purpose requires this capability
  - CKV_AWS_24   # Security group ingress - caller controls rules

  # CONFIGURABLE BY CALLER: static analysis can't see variable values
  - CKV_AWS_91   # LB access logging - exposed as access_logs variable
```

#### Trivy on Reusable Module Repos

A `.trivyignore` file at the repo root is automatically picked up by super-linter's Trivy integration. Use AVD IDs with explanatory comments:

```
# AVD-AWS-0090: S3 versioning - configurable by caller via versioning variable
AVD-AWS-0090
```

#### YAML_PRETTIER

Before committing any `.yaml`/`.yml` changes, run prettier to preempt `YAML_PRETTIER` failures:

```bash
prettier --write <file>.yaml
```

#### GITHUB_ACTIONS_ZIZMOR: Unpinned Actions

When zizmor flags `unpinned-uses`, pin action references to exact commit SHAs:

```bash
# For lightweight tags (direct commit ref):
gh api repos/<owner>/<action>/git/ref/tags/<version> --jq '.object.sha'

# For annotated tags (two-step dereference):
TAG_SHA=$(gh api repos/<owner>/<action>/git/ref/tags/<version> --jq '.object.sha')
gh api repos/<owner>/<action>/git/tags/$TAG_SHA --jq '.object.sha'
```

Then update the workflow:
```yaml
# Before:
uses: actions/checkout@v4
# After:
uses: actions/checkout@abc123def456... # v4
```

#### GITHUB_ACTIONS_ZIZMOR: Excessive Permissions

When zizmor flags `excessive-permissions` at the workflow level, move permissions to job-level so each job gets only what it needs:

```yaml
# Before — all jobs get these:
permissions:
  contents: read
  checks: write
  statuses: write

# After — only the job that needs them gets them:
permissions:
  contents: read  # workflow default

jobs:
  build:
    permissions:
      contents: read  # only needs to read

  lint:
    permissions:
      contents: read
      checks: write   # linter posts check results
      statuses: write
```

#### super-linter Cascading Failures

When using `VALIDATE_ALL_CODEBASE: false`, super-linter only lints **changed files**. This means each round of fixes may expose new failures as different file types get linted:

- Changing `.yaml` files → triggers `YAML_PRETTIER`, `YAML`
- Changing `.yml` workflow files → triggers `GITHUB_ACTIONS`, `GITHUB_ACTIONS_ZIZMOR`
- Changing `.tf` files → triggers `TERRAFORM_FMT`, `TERRAFORM_TFLINT`, `CHECKOV`, `TRIVY`

**Expect multiple fix iterations.** After each push, check which new linters fired and address them before declaring done.

Also note: removing deprecated workflow env vars (e.g., `VALIDATE_TERRAFORM_TERRASCAN`) and adding missing ones (e.g., `VALIDATE_GIT_COMMITLINT: false` when no commitlint config exists) prevents warnings that will become fatal errors in future super-linter versions.

### 5. Push to Fix Branch

Create or update a dedicated fix branch (use whatever name the user requests, defaulting to `ci-fix/<original-branch>`):

```bash
git checkout -b ci-fix/<original-branch>
git add <specific-files>  # prefer explicit files over git add -A
git commit -m "fix: resolve CI failure in <job-name>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push -u origin ci-fix/<original-branch>
```

If the fix branch already exists:

```bash
git checkout ci-fix/<original-branch>
git pull origin <original-branch>
# make fixes
git commit -m "fix: <description>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push
```

### 6. Verify the Fix

Watch the CI run triggered by the push:

```bash
gh run list --repo <owner>/<repo> --branch <branch> --limit 1 --json databaseId,status,workflowName
gh run watch <run-id> --repo <owner>/<repo> --exit-status
```

Check linter pass/fail summary:

```bash
gh run view <run-id> --repo <owner>/<repo> --log-failed 2>&1 | grep -E "Errors found|Successfully linted"
```

To rerun only failed jobs:

```bash
gh run rerun <run-id> --repo <owner>/<repo> --failed
```

**If new failures appear after fixing the original ones** (common with super-linter), repeat steps 2–5 for each new failure category. This is expected behavior, not a regression.

## Safety Notes

- Avoid `pull_request_target` unless explicitly requested — it can expose secrets to untrusted code
- When modifying workflow files, move `permissions` to job-level rather than broadening workflow-level access
- Pin actions to commit SHAs rather than tags to prevent tag hijacking
- For flaky tests, prefer deterministic fixes over blind reruns
- Never use `git add -A` blindly — stage specific files to avoid accidentally committing secrets or binaries

## Deliverable

After fixing, provide a brief summary:

- **Failing run**: Link or ID
- **Root cause**: What broke and why
- **Fix**: What changed
- **Verification**: New run link showing green status
