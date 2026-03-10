# Export to Obsidian - Usage Examples

## Quick Start Patterns

### Task Completion Summary

When you complete a significant task in a Warp session, create a summary export:

```python
from export_to_obsidian import export_content

export_content(
    title="Deploy Lambda function for SNS processing",
    content="""
    Successfully deployed Lambda function to process SNS messages.
    
    Changes made:
    - Created new Lambda function in aws_prod_organization
    - Set up SNS subscription triggers
    - Configured CloudWatch logging
    - Updated IAM role with required permissions
    
    Testing completed and verified in production.
    """,
    content_type="summary",
    ai_source="warp",
    summary_for_daily="Deployed SNS processing Lambda to production",
    repository="aws_prod_organization"
)
```

Result: Creates `deploy-lambda-function-for-sns-processing.md` with tags `#type/warp`, `#work/sunward`, `#python`

### Research Investigation

When you investigate a technical question:

```python
export_content(
    title="S3 Cross-Region Replication Strategies",
    content="""
    # S3 Cross-Region Replication Research
    
    ## Key Findings
    - CRR automatically replicates objects to destination region
    - Replication rules must be explicitly enabled
    - Only newly created/modified objects are replicated after rule creation
    
    ## Limitations
    - Cannot replicate to same region
    - Versioning must be enabled on both buckets
    - Delete markers not replicated by default
    
    ## Recommended Approach
    For aws_prod_organization: Use CRR with specific prefixes to control costs.
    """,
    content_type="research",
    ai_source="warp",
    summary_for_daily="Researched S3 CRR strategies and limitations",
    repository="aws_prod_organization"
)
```

Result: Creates `s3-cross-region-replication-strategies.md` with tags `#type/warp`, `#work/sunward`, `#aws`

### Full Chat Session

Archive an entire troubleshooting or implementation session:

```python
export_content(
    title="Cloud WAN troubleshooting session",
    content="[Full chat transcript here...]",
    content_type="session",
    ai_source="warp",
    summary_for_daily="Debugged Cloud WAN connectivity and resolved latency issues",
    repository="terraform-modules"
)
```

Result: Creates `cloud-wan-troubleshooting-session.md` with `#type/warp`, `#work/sunward`, `#terraform`

### Claude Code Integration

When using Claude Code for code generation or refactoring:

```python
export_content(
    title="Refactor Terraform variables for better modularity",
    content="""
    Generated improved variables.tf structure for terraform-modules/aws/cloud-wan
    
    Key improvements:
    - Added variable validation blocks
    - Improved variable descriptions
    - Grouped related variables with comment headers
    - Added default values where appropriate
    """,
    content_type="summary",
    ai_source="claude",
    summary_for_daily="Claude refactored Terraform module variables",
    repository="terraform-modules"
)
```

Result: Creates file with `#type/claude` instead of `#type/warp`

## Auto-Tagging Examples

### Repository Detection

| Repository | Auto-Tags |
|-----------|-----------|
| `aws_prod_organization` | `#type/warp`, `#work/sunward` |
| `gosunward_api` | `#type/warp`, `#work/sunward` |
| `scalr_management` | `#type/warp`, `#work/sunward` |
| `slfcu-infrastructure` | `#type/warp`, `#work/sunward` |
| `terraform-modules` | `#type/warp`, `#work/sunward` |
| `personal-project` | `#type/warp`, `#personal` |

### Language Detection

Content with Python imports → adds `#python`
Content with Terraform resources → adds `#terraform`
Content with Go functions → adds `#go`
Content with SQL queries → adds `#sql`
Content with Bash scripts → adds `#bash`
Content with TypeScript → adds `#typescript`

### Combined Example

Export for `aws_prod_organization` with Terraform and Python code:
```
Tags: #type/warp, #work/sunward, #terraform, #python
```

## Daily Note Integration

When you export content, the backlink automatically appears in today's daily note:

```markdown
## 📝 Notes
- [[AI Sessions/deploy-lambda-function-for-sns-processing|deploy-lambda-function-for-sns-processing]] - Deployed SNS processing Lambda to production
- [[AI Sessions/s3-cross-region-replication-strategies|s3-cross-region-replication-strategies]] - Researched S3 CRR strategies and limitations
```

## Filtering in Dashboards

Use these tags to filter content in Obsidian dashboards:

```dataview
table file.frontmatter.created as "Created"
from #type/warp
where file.frontmatter["ai_source"] = "warp"
  and file.frontmatter.tags contains "work/sunward"
sort file.frontmatter.created desc
```

Or search for all Claude Code exports:
```dataview
table repository
from #type/claude
sort file.frontmatter.created desc
```
