#!/usr/bin/env python3
"""Aggregate news from all sources and format output."""

import subprocess
import json
import sys
from datetime import datetime, timedelta

def run_script(script_path):
    """Run a script and return parsed JSON output."""
    try:
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path}: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print(f"Error parsing output from {script_path}", file=sys.stderr)
        return []

def categorize_by_date(items):
    """Categorize items by how recent they are."""
    now = datetime.now()
    today = []
    this_week = []
    this_month = []
    
    for item in items:
        try:
            item_date = datetime.strptime(item["published"], "%Y-%m-%d")
            days_ago = (now - item_date).days
            
            if days_ago == 0:
                today.append(item)
            elif days_ago <= 7:
                this_week.append(item)
            elif days_ago <= 30:
                this_month.append(item)
        except:
            this_week.append(item)  # Default to this week if date parsing fails
    
    return today, this_week, this_month

def format_output(news_items, releases):
    """Format the aggregated news as readable text with links."""
    output = []
    
    # Combine and categorize
    all_items = news_items + releases
    today, this_week, this_month = categorize_by_date(all_items)
    
    if today:
        output.append("## Today")
        for item in today:
            if "repo" in item:  # It's a release
                output.append(f"- **{item['repo']}** released {item['tag']}")
                output.append(f"  {item['url']}")
            else:  # It's a news item
                output.append(f"- **{item['source']}**: {item['title']}")
                output.append(f"  {item['link']}")
        output.append("")
    
    if this_week:
        output.append("## This Week")
        for item in this_week:
            if "repo" in item:
                output.append(f"- **{item['repo']}** released {item['tag']} ({item['published']})")
                output.append(f"  {item['url']}")
            else:
                output.append(f"- **{item['source']}**: {item['title']} ({item['published']})")
                output.append(f"  {item['link']}")
        output.append("")
    
    if this_month:
        output.append("## This Month (Notable)")
        # Only show significant items from this month
        for item in this_month[:5]:  # Limit to 5 items
            if "repo" in item and not item.get("prerelease"):  # Only stable releases
                output.append(f"- **{item['repo']}** released {item['tag']} ({item['published']})")
                output.append(f"  {item['url']}")
            elif "repo" not in item:
                output.append(f"- **{item['source']}**: {item['title']} ({item['published']})")
                output.append(f"  {item['link']}")
    
    if not output:
        output.append("No recent news found.")
    
    return "\n".join(output)

def main():
    """Main aggregation function."""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Fetch from all sources
    news_items = run_script(os.path.join(script_dir, "fetch_tech_news.py"))
    releases = run_script(os.path.join(script_dir, "check_releases.py"))
    
    # Format and print
    print(format_output(news_items, releases))

if __name__ == "__main__":
    main()
