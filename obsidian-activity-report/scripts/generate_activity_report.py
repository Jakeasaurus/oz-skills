#!/usr/bin/env python3
"""
Generate an activity report from Obsidian AI Sessions exports.

Scans exported session files, filters by date range, and produces
a markdown table showing what was accomplished. Optionally exports
the report back to the Obsidian vault.
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta

VAULT_ROOT = Path.home() / "Documents" / "obsidian"
AI_SESSIONS_FOLDER = VAULT_ROOT / "05-Archive" / "AI Sessions"


def get_date_range(period: str, start_str: str = None, end_str: str = None):
    """Return (start_date, end_date) for the given period keyword."""
    today = date.today()

    if period == "this_week":
        start = today - timedelta(days=today.weekday())  # Monday of current week
        end = today
    elif period == "last_week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
    elif period == "month_to_date":
        start = today.replace(day=1)
        end = today
    elif period == "last_month":
        first_of_this = today.replace(day=1)
        end = first_of_this - timedelta(days=1)
        start = end.replace(day=1)
    elif period == "year_to_date":
        start = today.replace(month=1, day=1)
        end = today
    elif period == "custom":
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
    else:
        raise ValueError(f"Unknown period: {period}")

    return start, end


def parse_frontmatter(text: str) -> tuple:
    """
    Parse YAML frontmatter from markdown text using a simple line-by-line approach.
    Returns (frontmatter_dict, body_text).
    Handles simple key: value pairs and YAML list (- item) structures.
    """
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    fm_text = parts[1]
    body = parts[2]
    fm = {}
    current_key = None
    current_list = None

    for line in fm_text.splitlines():
        # YAML list item (indented or top-level)
        if re.match(r"^\s+-\s+", line):
            item = re.sub(r"^\s+-\s+", "", line).strip().strip("'\"")
            if current_list is not None:
                current_list.append(item)
            continue

        # Key: value line
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip("'\"")

            # Flush any in-progress list to the previous key
            if current_list is not None and current_key:
                fm[current_key] = current_list
                current_list = None

            if val == "":
                # Start of a list value
                current_key = key
                current_list = []
            else:
                current_key = key
                fm[key] = val

    # Flush last list
    if current_list is not None and current_key:
        fm[current_key] = current_list

    return fm, body


def extract_title(filename_stem: str, body: str) -> str:
    """Extract title from first H1 in the top 10 lines of body, else humanize filename.
    Limits search to top of document to avoid picking up section headers deeper in the content.
    """
    top = "\n".join(body.splitlines()[:10])
    match = re.search(r"^#\s+(.+)$", top, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        return title if len(title) <= 60 else title[:57] + "..."
    return filename_stem.replace("-", " ").title()


def get_display_tags(tags) -> str:
    """Return relevant tags (skip type/ prefixed ones), max 3, dash if empty."""
    if not tags:
        return "—"
    filtered = [t for t in tags if not t.startswith("type/")]
    return ", ".join(filtered[:3]) if filtered else "—"


def parse_date_val(val: str):
    """Parse YYYY-MM-DD or ISO datetime string to a date object."""
    if not val:
        return None
    try:
        return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def scan_sessions(start: date, end: date) -> list:
    """Scan AI Sessions folder and return rows within the date range."""
    if not AI_SESSIONS_FOLDER.exists():
        print(f"Error: AI Sessions folder not found: {AI_SESSIONS_FOLDER}", file=sys.stderr)
        sys.exit(1)

    rows = []
    for md_file in sorted(AI_SESSIONS_FOLDER.glob("*.md"), reverse=True):
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        fm, body = parse_frontmatter(text)

        # Prefer 'date' field, fall back to 'created'
        file_date = parse_date_val(fm.get("date") or fm.get("created", ""))
        if not file_date:
            continue
        if not (start <= file_date <= end):
            continue

        title = extract_title(md_file.stem, body)
        raw_repo = fm.get("repository") or "—"
        repo = raw_repo if len(raw_repo) <= 40 else raw_repo[:37] + "..."
        content_type = fm.get("content_type", "summary")
        ai_source = fm.get("ai_source", "warp")
        tags = fm.get("tags", [])
        display_tags = get_display_tags(tags)

        rows.append({
            "date": file_date.strftime("%Y-%m-%d"),
            "title": title,
            "repository": repo,
            "type": content_type,
            "source": ai_source,
            "tags": display_tags,
            "filename": md_file.name,
        })

    return rows


def _cell(value: str) -> str:
    """Escape pipe characters so they don't break markdown table columns."""
    return str(value).replace("|", "\\|")


def build_report(rows: list, start: date, end: date) -> str:
    """Build the full markdown report string."""
    period_label = f"{start.strftime('%B %d, %Y')} → {end.strftime('%B %d, %Y')}"
    header = (
        f"# AI Session Activity Report\n\n"
        f"**Period**: {period_label}  \n"
        f"**Total sessions**: {len(rows)}\n\n"
    )

    if not rows:
        return header + "_No AI session exports found in this period._\n"

    table = "| Date | Title | Repository | Type | Source | Tags |\n"
    table += "|------|-------|------------|------|--------|------|\n"
    for row in rows:
        table += (
            f"| {_cell(row['date'])} "
            f"| {_cell(row['title'])} "
            f"| {_cell(row['repository'])} "
            f"| {_cell(row['type'])} "
            f"| {_cell(row['source'])} "
            f"| {_cell(row['tags'])} |\n"
        )

    return header + table


def export_to_obsidian(report_md: str, start: date, end: date) -> Path:
    """Write the report as a new note in the AI Sessions folder."""
    AI_SESSIONS_FOLDER.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    period_str = f"{start.strftime('%Y-%m-%d')}-to-{end.strftime('%Y-%m-%d')}"
    filename = f"activity-report-{period_str}.md"

    frontmatter = (
        "---\n"
        f"date: {now.strftime('%Y-%m-%d')}\n"
        f"created: {now.isoformat()}\n"
        "content_type: report\n"
        "ai_source: warp\n"
        "tags:\n"
        "  - type/warp\n"
        "  - report\n"
        "---\n\n"
    )

    export_path = AI_SESSIONS_FOLDER / filename
    export_path.write_text(frontmatter + report_md, encoding="utf-8")
    return export_path


def prompt_period() -> tuple:
    """Interactively prompt the user for a time period. Returns (period, start, end)."""
    print("Select time period for the activity report:")
    print("  1) This week")
    print("  2) Last week")
    print("  3) Month to date")
    print("  4) Last month")
    print("  5) Year to date")
    print("  6) Custom range")

    choice = input("\nEnter choice (1-6) [default: 3]: ").strip() or "3"
    period_map = {
        "1": "this_week",
        "2": "last_week",
        "3": "month_to_date",
        "4": "last_month",
        "5": "year_to_date",
        "6": "custom",
    }
    period = period_map.get(choice, "month_to_date")
    start_str = end_str = None

    if period == "custom":
        start_str = input("Start date (YYYY-MM-DD): ").strip()
        end_str = input("End date (YYYY-MM-DD): ").strip()

    return period, start_str, end_str


def main():
    parser = argparse.ArgumentParser(
        description="Generate activity report from Obsidian AI Sessions"
    )
    parser.add_argument(
        "period",
        nargs="?",
        choices=["this_week", "last_week", "month_to_date", "last_month", "year_to_date", "custom"],
        help="Time period (omit to be prompted interactively)",
    )
    parser.add_argument("--start", help="Start date for custom period (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date for custom period (YYYY-MM-DD)")
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export the report to the Obsidian vault automatically",
    )
    args = parser.parse_args()

    # Interactive mode if period not supplied
    if not args.period:
        period, start_str, end_str = prompt_period()
    else:
        period = args.period
        start_str = args.start
        end_str = args.end

    if period == "custom" and (not start_str or not end_str):
        print("Error: --start and --end are required for custom period.", file=sys.stderr)
        sys.exit(1)

    start, end = get_date_range(period, start_str, end_str)
    rows = scan_sessions(start, end)
    report_md = build_report(rows, start, end)

    print(report_md)

    # Export logic
    if args.export:
        path = export_to_obsidian(report_md, start, end)
        print(f"Exported to: {path}")
    elif rows:
        answer = input("Export this report to Obsidian? (y/n): ").strip().lower()
        if answer == "y":
            path = export_to_obsidian(report_md, start, end)
            print(f"Exported to: {path}")


if __name__ == "__main__":
    main()
