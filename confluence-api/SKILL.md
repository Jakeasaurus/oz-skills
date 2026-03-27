---
name: confluence-api
description: Expert at reading, updating, and managing Confluence pages via the Atlassian REST API. Retrieves pages, updates titles and content, manages versions, and handles authentication using stored API tokens from macOS Keychain. Use when you need to read, update, or modify Confluence pages, manage page versions, or perform bulk operations on Confluence content.
---

# Confluence API

Read, update, and manage Confluence pages via the Atlassian REST API with secure authentication using macOS Keychain.

## Authentication

The API token is securely stored in macOS Keychain. Retrieve it using:

```bash
security find-generic-password -s "confluence-api-token" -w
```

For non-scoped API tokens, use the site-specific URL with Basic Authentication:

```bash
TOKEN=$(security find-generic-password -s 'confluence-api-token' -w)
curl -u "jjones@gosunward.org:$TOKEN" \
  "https://gosunward.atlassian.net/wiki/rest/api/content/..."
```

## API Endpoints

**Base URL:** `https://gosunward.atlassian.net/wiki/rest/api/content/{pageId}`

### Get Page Details (with version info)

```bash
TOKEN=$(security find-generic-password -s 'confluence-api-token' -w)
curl -s "https://gosunward.atlassian.net/wiki/rest/api/content/1473937410?expand=version,space,body.storage" \
  -u "jjones@gosunward.org:$TOKEN"
```

Returns page metadata, current version number, and storage-format content (HTML-like).

### Update Page Title and/or Content

⚠️ **DISABLED - Do not use.** Write operations are currently disabled. This documentation is kept for future reference.

```bash
TOKEN=$(security find-generic-password -s 'confluence-api-token' -w)
curl -X PUT "https://gosunward.atlassian.net/wiki/rest/api/content/{pageId}" \
  -u "jjones@gosunward.org:$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "page",
    "title": "New Title",
    "status": "current",
    "version": {
      "number": 2
    },
    "body": {
      "storage": {
        "value": "<p>Content here</p>",
        "representation": "storage"
      }
    }
  }'
```

### List Child Pages

```bash
TOKEN=$(security find-generic-password -s 'confluence-api-token' -w)
curl -s "https://gosunward.atlassian.net/wiki/rest/api/content/{pageId}/child/page" \
  -u "jjones@gosunward.org:$TOKEN"
  -H "Authorization: Bearer $TOKEN"
```

## Key Requirements for Updates

1. **Version Number**: Must increment the current version by 1
2. **All Required Fields**: `type`, `title`, `status`, `version`, and `body` must all be present
3. **Body Format**: Use storage format (HTML-like representation)
4. **Content Type Header**: Always include `Content-Type: application/json`

## Workflow for Bulk Updates

When updating multiple pages:

1. Fetch each page with `?expand=version,space,body.storage`
2. Extract current version number
3. Prepare new title/content
4. Increment version: `"number": currentVersion + 1`
5. Send PUT request with all required fields
6. Verify success (HTTP 200)
7. Log results

## Error Handling

- **403 Forbidden**: Check token permissions, may need to refresh token
- **400 Bad Request**: Missing required fields or malformed JSON
- **409 Conflict**: Version number mismatch — fetch latest version first
- **401 Unauthorized**: Token is wrong or expired

## Storing/Updating Token in Keychain

To add or update the token:

```bash
security add-generic-password -s "confluence-api-token" -a "jjones@gosunward.org" -w "YOUR_API_TOKEN" -U
```

The `-U` flag updates if it already exists.

## Helper Script

Use the provided `confluence.sh` script for common operations:

```bash
./confluence.sh get-page <page_id>              # Get page details with version info
./confluence.sh update-title <page_id> <title>  # Update page title (keeps existing content)
./confluence.sh list-children <page_id>         # List child pages
```
