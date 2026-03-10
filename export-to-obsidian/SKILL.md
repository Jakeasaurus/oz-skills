---
name: export-to-obsidian
description: Export AI work sessions, summaries, and research to Obsidian vault with auto-tagging and daily note linking. Use when saving Warp or Claude Code work to your vault for task summaries and completion logs, research findings and documentation, or full chat session records. Creates descriptively-named files in AI Sessions folder with proper frontmatter and automatically links from today's daily note.
---

# Export to Obsidian

Export AI work to your Obsidian vault with automatic tagging, daily note integration, and content audit trails.

## Overview

This skill handles exporting content from Warp or Claude Code sessions to your Obsidian vault. It:
- Creates descriptively-named files in `05-Archive/AI Sessions/`
- Auto-detects programming languages and work context (Sunward vs. personal)
- Tags content with `#type/warp` or `#type/claude` plus relevant work/language tags
- Adds creation date in frontmatter for filtering
- Creates backlinks in today's daily note

## Usage

### In Python

Use the `export_content()` function for direct integration:

```python
from export_to_obsidian import export_content

export_path = export_content(
    title="Terraform refactor for cloud-wan module",
    content="Full session summary or chat transcript",
    content_type="summary",  # or "research", "session"
    ai_source="warp",  # or "claude"
    summary_for_daily="Refactored cloud-wan module for better reusability",
    repository="terraform-modules"  # optional
)
```

### Via Command Line

```bash
# Export a task summary
python3 export_to_obsidian.py "Deploy API gateway to prod" content.txt summary warp aws_prod_organization

# Export research findings
python3 export_to_obsidian.py "Lambda concurrency limits research" research.txt research claude

# Export full chat session
python3 export_to_obsidian.py "Cloud-WAN troubleshooting session" chat.txt session warp terraform-modules
```

## Parameters

**title** (required)
- Descriptive title for the export
- Becomes filename: sanitized, lowercased, hyphenated
- Example: "Terraform refactor for cloud-wan" → `terraform-refactor-for-cloud-wan.md`

**content** (required)
- Full content to export
- Can include code snippets, notes, research findings, chat transcripts

**content_type** (optional, default: "summary")
- `summary` - Brief work summary or task completion log
- `research` - Research findings or investigation results
- `session` - Full chat transcript or extended session log

**ai_source** (optional, default: "warp")
- `warp` - Content from Warp/Oz sessions
- `claude` - Content from Claude Code or other Claude integrations

**summary_for_daily** (optional)
- Brief one-liner for the daily note backlink
- If omitted, uses first line of content (truncated to 100 chars)

**repository** (optional)
- Repository name for context detection
- Auto-detects from content if not provided
- Used to determine work context tags

## Auto-Tagging

Content is automatically tagged based on:

### Work Context
- **Sunward repositories**: `aws_prod_*`, `aws_dev_*`, `gosunward_*`, `scalr_*`, `slfcu-infrastructure` → `#work/sunward`
- **Other work**: Inferred from content keywords → `#work/sunward` or `#personal`

### Programming Languages
Detected and tagged: `#python`, `#terraform`, `#go`, `#typescript`, `#bash`, `#sql`, `#json`, etc.

### Content Type & Source
- Always tagged with `#type/warp` or `#type/claude`
- Also tagged with content_type if relevant

## Frontmatter

Generated files include:
```yaml
---
date: 2026-03-06
created: 2026-03-06T15:42:46Z
content_type: summary
ai_source: warp
tags:
  - type/warp
  - work/sunward
  - terraform
  - python
repository: terraform-modules
---
```

## Daily Note Integration

Automatically creates and links to today's daily note:

1. **Creates daily note if needed**: Uses `obsidian daily` CLI command to create today's note if it doesn't exist
2. **Appends to Completed Tasks**: Adds backlink under the `<!-- Warp skill will append here -->` marker in the Completed Tasks section
3. **Fallback sections**: If the marker isn't found, falls back to Notes or Links sections

Example result in daily note:
```markdown
## ✅ Completed Tasks
<!-- Warp skill will append here -->
- [[AI Sessions/terraform-refactor-for-cloud-wan|terraform-refactor-for-cloud-wan]] - Refactored cloud-wan module for better reusability
```

If the Obsidian CLI is not available, the export still succeeds and logs a warning.

## File Location

All exports go to: `/Users/Jacobj/Documents/obsidian/05-Archive/AI Sessions/`

Folder is created automatically if it doesn't exist.
