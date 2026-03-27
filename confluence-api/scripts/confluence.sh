#!/bin/bash

# Confluence API Helper Script
# This script provides common functions for interacting with the Confluence REST API
# Token is retrieved securely from macOS Keychain

set -e

BASE_URL="https://gosunward.atlassian.net/wiki/rest/api/content"
EMAIL="jjones@gosunward.org"

# Retrieve token from Keychain
get_token() {
  security find-generic-password -s "confluence-api-token" -w 2>/dev/null || {
    echo "Error: Token not found in Keychain. Store it first with:" >&2
    echo "security add-generic-password -s 'confluence-api-token' -a 'jjones@gosunward.org' -w 'YOUR_TOKEN'" >&2
    exit 1
  }
}

# Generate Basic Auth header
get_auth_header() {
  local token=$(get_token)
  echo -n "$EMAIL:$token" | base64
}

# Get page details with version info
get_page() {
  local page_id=$1
  local auth=$(get_auth_header)

  curl -s "${BASE_URL}/${page_id}?expand=version,space,body.storage" \
    -H "Authorization: Basic $auth"
}

# Update page title (requires page_id and new_title)
update_title() {
  local page_id=$1
  local new_title=$2
  local auth=$(get_auth_header)

  # Get current page data
  local page_data=$(get_page "$page_id")
  local current_version=$(echo "$page_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['version']['number'])" 2>/dev/null)
  local current_body=$(echo "$page_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['body']['storage']['value'])" 2>/dev/null)

  if [ -z "$current_version" ]; then
    echo "Error: Could not fetch page version" >&2
    exit 1
  fi

  local new_version=$((current_version + 1))

  # Escape JSON in body content
  local escaped_body=$(echo "$current_body" | python3 -c "import sys, json; print(json.dumps(sys.stdin.read()))" 2>/dev/null)

  # Update page
  curl -s -X PUT "${BASE_URL}/${page_id}" \
    -H "Authorization: Basic $auth" \
    -H "Content-Type: application/json" \
    -d "{
      \"type\": \"page\",
      \"title\": \"${new_title}\",
      \"status\": \"current\",
      \"version\": {
        \"number\": ${new_version}
      },
      \"body\": {
        \"storage\": {
          \"value\": ${escaped_body},
          \"representation\": \"storage\"
        }
      }
    }"
}

# List child pages
list_children() {
  local page_id=$1
  local auth=$(get_auth_header)

  curl -s "${BASE_URL}/${page_id}/child/page" \
    -H "Authorization: Basic $auth"
}

# Display usage
usage() {
  cat <<EOF
Usage: confluence.sh <command> [arguments]

Commands:
  get-page <page_id>              Get page details with version info
  update-title <page_id> <title>  Update page title (keeps existing content)
  list-children <page_id>         List child pages

Examples:
  ./confluence.sh get-page 1329234126
  ./confluence.sh update-title 1329234126 "KLM: Discovery - Existing Servers"
  ./confluence.sh list-children 1329234126
EOF
}

# Main
case "${1}" in
  get-page)
    get_page "$2"
    ;;
  update-title)
    update_title "$2" "$3" | python3 -m json.tool
    ;;
  list-children)
    list_children "$2" | python3 -m json.tool
    ;;
  *)
    usage
    exit 1
    ;;
esac
