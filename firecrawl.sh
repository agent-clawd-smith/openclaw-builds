#!/bin/zsh
# Firecrawl search + scrape helper
# Usage:
#   firecrawl.sh search "your query" [limit]
#   firecrawl.sh scrape "https://example.com"

FIRECRAWL_API_KEY=$(python3 -c "import json; c=json.load(open('$HOME/.openclaw/secrets.json')); print(c['firecrawl']['apiKey'])")
BASE="https://api.firecrawl.dev/v1"

case "$1" in
  search)
    QUERY="$2"
    LIMIT="${3:-5}"
    curl -s -X POST "$BASE/search" \
      -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"query\": \"$QUERY\", \"limit\": $LIMIT}"
    ;;
  scrape)
    URL="$2"
    curl -s -X POST "$BASE/scrape" \
      -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"url\": \"$URL\", \"formats\": [\"markdown\"]}"
    ;;
  *)
    echo "Usage: $0 search <query> [limit]"
    echo "       $0 scrape <url>"
    ;;
esac
