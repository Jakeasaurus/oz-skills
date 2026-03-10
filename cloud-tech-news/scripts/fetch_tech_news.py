#!/usr/bin/env python3
"""Fetch tech news from RSS feeds and blogs."""

import feedparser
import requests
from datetime import datetime, timedelta
import json
import sys

# RSS Feeds to monitor
FEEDS = {
    "Warp": "https://www.warp.dev/blog/rss.xml",
    "AWS": "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
    "GitHub": "https://github.blog/feed/",
    "HashiCorp": "https://www.hashicorp.com/blog/feed.xml",
    "OpenTofu": "https://opentofu.org/blog/rss.xml",
}

def parse_date(date_str):
    """Parse various date formats to datetime."""
    try:
        # Try common formats
        for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except:
        return None

def fetch_feed(name, url, days_back=7):
    """Fetch and parse an RSS feed."""
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            return []
        
        cutoff = datetime.now() - timedelta(days=days_back)
        
        items = []
        for entry in feed.entries[:10]:  # Limit to 10 most recent
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            
            if pub_date and pub_date >= cutoff:
                items.append({
                    "source": name,
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "published": pub_date.strftime("%Y-%m-%d"),
                    "summary": entry.get("summary", "")[:200]  # First 200 chars
                })
        
        return items
    except Exception as e:
        print(f"Error fetching {name}: {e}", file=sys.stderr)
        return []

def main():
    """Fetch all news sources and output JSON."""
    all_news = []
    
    for name, url in FEEDS.items():
        items = fetch_feed(name, url)
        all_news.extend(items)
    
    # Sort by date (newest first)
    all_news.sort(key=lambda x: x["published"], reverse=True)
    
    # Output as JSON
    print(json.dumps(all_news, indent=2))

if __name__ == "__main__":
    main()
