---
name: outlook-calendar-sync
description: >
  Sync your Outlook/Microsoft 365 calendar to a local JSON file at ~/.claude/calendar.json
  for use in Claude Code sessions. Use this skill whenever the user wants to pull in calendar
  data, check their schedule, sync Outlook events, see what meetings they have, or make
  their calendar available to Claude Code. Supports SAML-federated orgs (Okta, ADFS, Ping,
  etc.) transparently via MSAL device code flow — no special SAML handling needed.
  Trigger this skill any time the user mentions calendar, Outlook, schedule, meetings, or
  wants Claude Code to be aware of upcoming events.
---

# Outlook Calendar Sync

Fetches upcoming calendar events from Outlook/Microsoft 365 via the Microsoft Graph API
and writes them to `~/.claude/calendar.json` so Claude Code can reference them in sessions.

## Prerequisites (one-time setup)

The user needs an Azure AD app registration before the script can authenticate. If they
haven't done this yet, walk them through it:

1. Go to https://portal.azure.com → **Azure Active Directory** → **App registrations**
2. Click **New registration**
   - Name: `Claude Calendar Sync` (or anything)
   - Supported account types: **Accounts in this organizational directory only**
   - Redirect URI: **Public client/native** → `https://login.microsoftonline.com/common/oauth2/nativeclient`
3. Click **Register**, then copy the **Application (client) ID** and **Directory (tenant) ID**
4. Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated**
   → search for `Calendars.Read` → Add
5. Click **Grant admin consent** (or ask your org admin to do this)
6. Go to **Authentication** → under **Advanced settings**, enable **Allow public client flows** → Save

Then set two env vars (add to `~/.zshrc` or `~/.bashrc` to persist):
```bash
export OUTLOOK_CLIENT_ID="your-application-client-id"
export OUTLOOK_TENANT_ID="your-directory-tenant-id"
```

## Running the sync

The bundled script handles everything. Check deps and run it:

```bash
# Install deps if needed (one-time)
pip install msal requests 2>/dev/null || pip3 install msal requests

# Run the sync
python3 ~/.agents/skills/outlook-calendar-sync/scripts/calendar_sync.py
```

**First run:** The script prints a URL and a short code. Open the URL in any browser,
enter the code, and sign in normally — your org's SAML/SSO flow will kick in automatically.
The token is cached at `~/.cache/claude_calendar_token.json` so subsequent runs skip auth.

**Subsequent runs:** Silent (uses cached token, re-authenticates only when token expires).

## What it writes

`~/.claude/calendar.json`:
```json
{
  "generated_utc": "2026-03-09T14:00:00+00:00",
  "range_days": 7,
  "event_count": 12,
  "events": [
    {
      "title": "Sprint Planning",
      "start": "2026-03-10T09:00:00",
      "end": "2026-03-10T10:30:00",
      "isAllDay": false,
      "location": "Teams Meeting",
      "organizer": "Jane Smith",
      "bodyPreview": "Please review the backlog before joining..."
    }
  ]
}
```

## Configuring the sync

Optional env vars to customize behavior:

| Var | Default | Description |
|-----|---------|-------------|
| `OUTLOOK_CLIENT_ID` | *(required)* | Azure AD app client ID |
| `OUTLOOK_TENANT_ID` | `common` | Azure AD tenant ID |
| `CALENDAR_DAYS_AHEAD` | `7` | How many days of events to fetch |
| `CALENDAR_OUTPUT_PATH` | `~/.claude/calendar.json` | Where to write the output |

## After syncing

Once `~/.claude/calendar.json` exists, tell the user they can reference it in Claude Code
sessions by asking things like:
- "What do I have on my calendar this week?"
- "Do I have any conflicts on Thursday?"
- "What's my first meeting tomorrow?"

Or suggest adding to their `CLAUDE.md`:
```markdown
## Calendar
My calendar is available at ~/.claude/calendar.json (run outlook-calendar-sync to refresh).
```

## Troubleshooting

**"AADSTS65001: User has not consented"** → Admin consent wasn't granted. Ask your org admin
to approve the `Calendars.Read` permission in the Azure portal.

**"AADSTS7000218: The request body must contain... client_secret"** → The app isn't configured
as a public client. Go to Authentication → enable "Allow public client flows".

**"invalid_client"** → Double-check `OUTLOOK_CLIENT_ID` matches the Application (client) ID,
not the Object ID.

**Token expired / re-auth needed** → Delete `~/.cache/claude_calendar_token.json` and re-run.
