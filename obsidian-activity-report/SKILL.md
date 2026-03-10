---
name: obsidian-activity-report
description: Generate a table-based activity report of AI chat session accomplishments from the Obsidian vault. Use when the user asks for a summary of what has been accomplished in recent sessions, wants to review completed tasks or work done by AI chats, or asks for a weekly/monthly/YTD activity report. Complements the export-to-obsidian skill by reading back those exported sessions and presenting them as a filterable summary. Triggers on requests like "show me what we accomplished this week", "activity report", "session summary", "what did we do last month", or "show my AI session history".
---

# Obsidian Activity Report

Generate a date-filtered markdown table of AI session accomplishments from the Obsidian vault.

## When to Use

Use this skill when the user wants to review past AI chat work — completed tasks, research, or sessions — from their Obsidian vault (`05-Archive/AI Sessions/`).

## Workflow

### Step 1: Ask for a time period (if not already specified)

Ask the user which period they want:

> Which time period would you like the report to cover?
> 1. This week
> 2. Last week
> 3. Month to date
> 4. Last month
> 5. Year to date
> 6. Custom range (provide start and end dates)

### Step 2: Run the report script

Use the appropriate period argument:

```bash
python3 /Users/Jacobj/.agents/skills/obsidian-activity-report/scripts/generate_activity_report.py <period>
```

Period values: `this_week`, `last_week`, `month_to_date`, `last_month`, `year_to_date`

For custom ranges:
```bash
python3 /Users/Jacobj/.agents/skills/obsidian-activity-report/scripts/generate_activity_report.py custom --start 2026-01-01 --end 2026-01-31
```

To export automatically without prompting:
```bash
python3 /Users/Jacobj/.agents/skills/obsidian-activity-report/scripts/generate_activity_report.py <period> --export
```

### Step 3: Present the output

Display the markdown table from the script output directly to the user. The table columns are:

| Column | Description |
|--------|-------------|
| Date | Session export date |
| Title | H1 heading from the session file |
| Repository | Git repo associated with the work |
| Type | `summary`, `research`, or `session` |
| Source | `warp` or `claude` |
| Tags | Work context and language tags (e.g. `work/sunward, terraform`) |

### Step 4: Offer to export

After displaying the table, ask the user if they want to save the report to Obsidian. If yes, re-run with `--export` or call `export_to_obsidian()` from within the script. The report saves to:

`/Users/Jacobj/Documents/obsidian/05-Archive/AI Sessions/activity-report-<start>-to-<end>.md`

## Notes

- Sessions are sourced from files exported by the `export-to-obsidian` skill
- The script uses only Python standard library — no external dependencies
- If no sessions exist for the period, the script reports that gracefully
- Reports written to Obsidian include frontmatter with `content_type: report` and `tags: [type/warp, report]`
