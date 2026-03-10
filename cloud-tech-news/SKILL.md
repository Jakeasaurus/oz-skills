---
name: cloud-tech-news
description: Aggregate recent news, releases, and updates from cloud infrastructure and DevOps tools. Use when asked for cloud news, tech updates, what's new with Warp/OpenTofu/Terraform/AWS/GitHub/Scalr, recent releases, or to check for updates in the cloud/infrastructure ecosystem. Can be run on-demand or scheduled for daily briefings.
---

# Cloud Tech News

## Overview
Aggregate and summarize recent news from cloud infrastructure and DevOps ecosystem:
- Blog posts from Warp, AWS, GitHub, HashiCorp, OpenTofu, Scalr
- GitHub releases for OpenTofu, Terraform, GitHub CLI
- Status updates for major cloud services

Output is categorized by recency: Today → This Week → This Month (notable only).

## Quick Start
Run the main aggregation script:
```bash
python3 scripts/aggregate_news.py
```

This executes all collectors and formats output with brief summaries and links.

## Dependencies
Install required packages:
```bash
pip3 install feedparser requests
```

## Scheduling Daily Updates
To schedule automatic checks (e.g., daily at 9am EST), combine with the scheduler skill to set up a cron job or launchd task that runs `aggregate_news.py` and sends a macOS notification.

## News Sources
See `references/news_sources.md` for the complete list of monitored sources.

## Scripts
- `aggregate_news.py` - Main script that runs all collectors and formats output
- `fetch_tech_news.py` - Fetches RSS feeds from official blogs
- `check_releases.py` - Checks GitHub releases for key repositories
