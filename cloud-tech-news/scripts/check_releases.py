#!/usr/bin/env python3
"""Check GitHub releases for key tools."""

import requests
from datetime import datetime, timedelta
import json
import sys

# Repositories to monitor
REPOS = [
    "opentofu/opentofu",
    "hashicorp/terraform",
    "cli/cli",
]

def fetch_releases(repo, days_back=30):
    """Fetch recent GitHub releases."""
    try:
        url = f"https://api.github.com/repos/{repo}/releases"
        response = requests.get(url, headers={"Accept": "application/vnd.github+json"})
        response.raise_for_status()
        
        releases = response.json()
        cutoff = datetime.now() - timedelta(days=days_back)
        
        recent = []
        for release in releases[:5]:  # Check latest 5 releases
            published = datetime.strptime(release["published_at"], "%Y-%m-%dT%H:%M:%SZ")
            
            if published >= cutoff:
                recent.append({
                    "repo": repo,
                    "name": release["name"] or release["tag_name"],
                    "tag": release["tag_name"],
                    "url": release["html_url"],
                    "published": published.strftime("%Y-%m-%d"),
                    "prerelease": release["prerelease"],
                    "body": release["body"][:300] if release.get("body") else ""
                })
        
        return recent
    except Exception as e:
        print(f"Error fetching releases for {repo}: {e}", file=sys.stderr)
        return []

def main():
    """Fetch all releases and output JSON."""
    all_releases = []
    
    for repo in REPOS:
        releases = fetch_releases(repo)
        all_releases.extend(releases)
    
    # Sort by date (newest first)
    all_releases.sort(key=lambda x: x["published"], reverse=True)
    
    # Output as JSON
    print(json.dumps(all_releases, indent=2))

if __name__ == "__main__":
    main()
