#!/bin/zsh
# Run cloud tech news and send notification

NEWS_OUTPUT=$(python3 /Users/Jacobj/.agents/skills/cloud-tech-news/scripts/aggregate_news.py 2>&1)

# Count items in "Today" section
TODAY_COUNT=$(echo "$NEWS_OUTPUT" | grep -A 100 "^## Today" | grep -B 1 "^## " | grep "^- " | wc -l | tr -d ' ')

if [ "$TODAY_COUNT" -gt 0 ]; then
    osascript -e "display notification \"$TODAY_COUNT new items today. Check /tmp/cloudtechnews.out for details.\" with title \"Cloud Tech News\" sound name \"Glass\""
else
    osascript -e "display notification \"No news today. Check /tmp/cloudtechnews.out for this week's updates.\" with title \"Cloud Tech News\""
fi

# Save full output
echo "$NEWS_OUTPUT" > /tmp/cloudtechnews.out
echo "News updated at $(date)" >> /tmp/cloudtechnews.out
