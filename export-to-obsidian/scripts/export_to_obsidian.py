#!/usr/bin/env python3
"""
Export content to Obsidian vault with auto-tagging and daily note linking.
Supports task summaries, research findings, and full chat sessions.
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List

VAULT_ROOT = Path.home() / "Documents" / "obsidian"
AI_SESSIONS_FOLDER = VAULT_ROOT / "05-Archive" / "AI Sessions"
DAILY_NOTES_FOLDER = VAULT_ROOT / "01-Daily"

# Repository patterns for auto-tagging
SUNWARD_REPOS = {
    "aws_prod_",
    "aws_dev_",
    "gosunward_",
    "scalr_",
    "slfcu-infrastructure",
    "terraform-modules",  # Work infrastructure modules
}

# Language patterns for detection
LANGUAGE_PATTERNS = {
    "python": r"\bpython\b|\.py\b|import\s+|from\s+\w+\s+import|def\s+\w+",
    "terraform": r"\.tf\b|resource\s+\"|\bhcl\b|terraform|module\s+\"",
    "go": r"\.go\b|package\s+\w+|func\s+|import\s+\(",
    "javascript": r"\.js\b|\.tsx?\b|const\s+|import\s+|require\(",
    "typescript": r"\.ts\b|\.tsx\b|interface\s+|type\s+",
    "bash": r"\.sh\b|#!/bin/bash|#!/bin/zsh",
    "sql": r"SELECT\s+|INSERT\s+|UPDATE\s+|DELETE\s+",
    "json": r"\{.*\}|\"[\w]+\"\s*:",
}


def detect_languages(content: str) -> List[str]:
    """Detect programming languages in content."""
    detected = []
    content_lower = content.lower()
    
    for lang, pattern in LANGUAGE_PATTERNS.items():
        if re.search(pattern, content_lower, re.IGNORECASE):
            detected.append(lang)
    
    return detected


def detect_repository(content: str) -> Optional[str]:
    """Detect repository name from content."""
    # Look for common patterns: /path/to/repo, repository: name, repo: name
    patterns = [
        r"(?:repository|repo):\s*['\"]?([a-zA-Z0-9_-]+)",
        r"/Documents/projects/([a-zA-Z0-9_-]+)",
        r"(?:at|in)\s+(?:repo|repository)\s+([a-zA-Z0-9_-]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def get_work_context_tags(repo: Optional[str], content: str) -> List[str]:
    """Determine work context tags based on repository and content patterns."""
    tags = []
    
    if repo:
        # Check if it's a Sunward/SLFCU repository
        if any(repo.startswith(prefix) for prefix in SUNWARD_REPOS) or "slfcu" in repo.lower():
            tags.append("work/sunward")
        else:
            tags.append("personal")
    else:
        # Try to infer from content
        if any(keyword in content.lower() for keyword in ["sunward", "slfcu", "aws_prod", "aws_dev"]):
            tags.append("work/sunward")
        else:
            tags.append("personal")
    
    return tags


def generate_frontmatter(
    content_type: str,
    ai_source: str,
    tags: List[str],
    repository: Optional[str] = None,
) -> str:
    """Generate YAML frontmatter for the export."""
    now = datetime.now()
    
    # Add content type and AI source tags
    all_tags = list(tags)
    all_tags.insert(0, f"type/{ai_source}")
    
    tag_yaml = "\n  - ".join(all_tags)
    
    frontmatter = f"""---
date: {now.strftime('%Y-%m-%d')}
created: {now.isoformat()}
content_type: {content_type}
ai_source: {ai_source}
tags:
  - {tag_yaml}
"""
    
    if repository:
        frontmatter += f"repository: {repository}\n"
    
    frontmatter += "---\n"
    
    return frontmatter


def get_today_daily_note_path() -> Path:
    """Get path to today's daily note."""
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m-%B")  # e.g., "03-March"
    date = now.strftime("%Y-%m-%d")
    
    daily_note = DAILY_NOTES_FOLDER / year / month / f"{date}.md"
    return daily_note


def append_to_daily_note(export_filename: str, summary: str) -> None:
    """Append a backlink to the export in today's daily note."""
    import subprocess
    
    daily_note = get_today_daily_note_path()
    
    # If daily note doesn't exist, create it using obsidian CLI
    if not daily_note.exists():
        try:
            subprocess.run(["obsidian", "daily"], capture_output=True, timeout=5)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"Warning: Could not create daily note via obsidian CLI: {e}", file=sys.stderr)
            return
    
    # Verify note was created
    if not daily_note.exists():
        print(f"Warning: Daily note not found at {daily_note}", file=sys.stderr)
        return
    
    content = daily_note.read_text()
    
    # Look for the Warp skill append marker in Completed Tasks section
    if "<!-- Warp skill will append here -->" in content:
        marker = "<!-- Warp skill will append here -->"
        insert_text = f"\n- [[AI Sessions/{export_filename}|{Path(export_filename).stem}]] - {summary}"
        updated_content = content.replace(marker, marker + insert_text)
        daily_note.write_text(updated_content)
    # Fallback to Notes section if marker not found
    elif "## 📝 Notes" in content:
        section_marker = "## 📝 Notes"
        insert_text = f"\n- [[AI Sessions/{export_filename}|{Path(export_filename).stem}]] - {summary}"
        parts = content.split(section_marker)
        if len(parts) == 2:
            updated_content = parts[0] + section_marker + insert_text + parts[1]
            daily_note.write_text(updated_content)
    # Final fallback to Links section
    elif "## 🔗 Links" in content:
        section_marker = "## 🔗 Links"
        insert_text = f"\n- [[AI Sessions/{export_filename}|{Path(export_filename).stem}]] - {summary}"
        parts = content.split(section_marker)
        if len(parts) == 2:
            updated_content = parts[0] + section_marker + insert_text + parts[1]
            daily_note.write_text(updated_content)
    else:
        print(f"Warning: Could not find Completed Tasks, Notes, or Links section in daily note", file=sys.stderr)
        return


def export_content(
    title: str,
    content: str,
    content_type: str = "summary",  # summary, research, session
    ai_source: str = "warp",  # warp, claude
    summary_for_daily: Optional[str] = None,
    repository: Optional[str] = None,
) -> Path:
    """
    Export content to Obsidian AI Sessions folder.
    
    Args:
        title: Descriptive title for the export (used as filename)
        content: Full content to export
        content_type: Type of content (summary, research, session)
        ai_source: Source of content (warp, claude)
        summary_for_daily: Brief summary for daily note backlink (defaults to first line)
        repository: Repository name for auto-tagging (optional)
    
    Returns:
        Path to created file
    """
    # Ensure AI Sessions folder exists
    AI_SESSIONS_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Generate filename: descriptive title, sanitized
    filename = re.sub(r'[^\w\s-]', '', title).strip()
    filename = re.sub(r'[-\s]+', '-', filename).lower()
    filename = f"{filename}.md"
    
    # Detect repository if not provided
    if not repository:
        repository = detect_repository(content)
    
    # Detect languages
    languages = detect_languages(content)
    
    # Get work context tags
    work_tags = get_work_context_tags(repository, content)
    
    # Combine all tags
    all_tags = work_tags + languages
    
    # Generate frontmatter
    frontmatter = generate_frontmatter(
        content_type=content_type,
        ai_source=ai_source,
        tags=all_tags,
        repository=repository,
    )
    
    # Write file
    export_path = AI_SESSIONS_FOLDER / filename
    export_path.write_text(frontmatter + content)
    
    # Append to daily note
    daily_summary = summary_for_daily or content.split('\n')[0][:100]
    append_to_daily_note(filename, daily_summary)
    
    return export_path


if __name__ == "__main__":
    # Example usage via command line
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <title> <content_file> [content_type] [ai_source] [repository]")
        sys.exit(1)
    
    title = sys.argv[1]
    content_file = Path(sys.argv[2])
    content_type = sys.argv[3] if len(sys.argv) > 3 else "summary"
    ai_source = sys.argv[4] if len(sys.argv) > 4 else "warp"
    repository = sys.argv[5] if len(sys.argv) > 5 else None
    
    if not content_file.exists():
        print(f"Error: Content file not found: {content_file}", file=sys.stderr)
        sys.exit(1)
    
    content = content_file.read_text()
    
    try:
        export_path = export_content(
            title=title,
            content=content,
            content_type=content_type,
            ai_source=ai_source,
            repository=repository,
        )
        print(f"Exported to: {export_path}")
    except Exception as e:
        print(f"Error exporting content: {e}", file=sys.stderr)
        sys.exit(1)
