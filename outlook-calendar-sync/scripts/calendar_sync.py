#!/usr/bin/env python3
"""
Outlook Calendar Sync for Claude Code

Authenticates via MSAL device code flow (handles SAML/federated orgs transparently)
and writes upcoming calendar events to a local JSON file.

Required env vars:
  OUTLOOK_CLIENT_ID   - Azure AD app Application (client) ID
  OUTLOOK_TENANT_ID   - Azure AD Directory (tenant) ID (defaults to "common")

Optional env vars:
  CALENDAR_DAYS_AHEAD   - Days of events to fetch (default: 7)
  CALENDAR_OUTPUT_PATH  - Output file path (default: ~/.claude/calendar.json)
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import msal
    import requests
except ImportError:
    print("Missing dependencies. Run: pip install msal requests")
    sys.exit(1)

# --- Configuration ---

CONFIG = {
    "client_id": os.environ.get("OUTLOOK_CLIENT_ID", ""),
    "tenant_id": os.environ.get("OUTLOOK_TENANT_ID", "common"),
    "days_ahead": int(os.environ.get("CALENDAR_DAYS_AHEAD", "7")),
    "output_path": Path(
        os.environ.get("CALENDAR_OUTPUT_PATH", "~/.claude/calendar.json")
    ).expanduser(),
    "token_cache_path": Path("~/.cache/claude_calendar_token.json").expanduser(),
}

SCOPES = ["https://graph.microsoft.com/Calendars.Read"]
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"


# --- Token Cache ---

def load_cache() -> "msal.SerializableTokenCache":
    cache = msal.SerializableTokenCache()
    if CONFIG["token_cache_path"].exists():
        cache.deserialize(CONFIG["token_cache_path"].read_text())
    return cache


def save_cache(cache: "msal.SerializableTokenCache") -> None:
    if cache.has_state_changed:
        CONFIG["token_cache_path"].parent.mkdir(parents=True, exist_ok=True)
        CONFIG["token_cache_path"].write_text(cache.serialize())
        os.chmod(CONFIG["token_cache_path"], 0o600)


# --- Authentication ---

def get_token() -> str:
    if not CONFIG["client_id"]:
        print("ERROR: OUTLOOK_CLIENT_ID env var is not set.")
        print("Set it to your Azure AD app's Application (client) ID.")
        print("See the skill README for setup instructions.")
        sys.exit(1)

    authority = f"https://login.microsoftonline.com/{CONFIG['tenant_id']}"
    cache = load_cache()

    app = msal.PublicClientApplication(
        CONFIG["client_id"],
        authority=authority,
        token_cache=cache,
    )

    # Try silent (cached) auth first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            save_cache(cache)
            print(f"Authenticated (cached) as: {accounts[0].get('username', 'unknown')}")
            return result["access_token"]

    # Device code flow — MSAL handles SAML/ADFS/Okta federation automatically
    print("No cached token. Starting device code authentication...\n")
    flow = app.initiate_device_flow(scopes=SCOPES)

    if "user_code" not in flow:
        raise RuntimeError(
            f"Failed to start device code flow: {flow.get('error_description', str(flow))}"
        )

    # Prints: "To sign in, use a web browser to open https://microsoft.com/devicelogin
    # and enter the code XXXXXXXX to authenticate."
    print(flow["message"])
    print()

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(
            f"Authentication failed: {result.get('error_description', result.get('error', 'Unknown error'))}"
        )

    save_cache(cache)
    print("Authentication successful.\n")
    return result["access_token"]


# --- Calendar Fetch ---

def get_events(token: str) -> list:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=CONFIG["days_ahead"])

    url = f"{GRAPH_ENDPOINT}/me/calendarView"
    headers = {
        "Authorization": f"Bearer {token}",
        "Prefer": 'outlook.timezone="UTC"',
    }
    params = {
        "$select": "subject,start,end,location,isAllDay,bodyPreview,organizer",
        "$orderby": "start/dateTime",
        "startDateTime": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "$top": 100,
    }

    events = []
    while url:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        events.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
        params = {}  # nextLink already encodes params

    return events


# --- Format ---

def format_event(event: dict) -> dict:
    return {
        "title": event.get("subject") or "(No title)",
        "start": event.get("start", {}).get("dateTime"),
        "end": event.get("end", {}).get("dateTime"),
        "isAllDay": event.get("isAllDay", False),
        "location": event.get("location", {}).get("displayName") or "",
        "organizer": (
            event.get("organizer", {})
            .get("emailAddress", {})
            .get("name") or ""
        ),
        "bodyPreview": (event.get("bodyPreview") or "")[:300],
    }


# --- Main ---

def main():
    print(f"Claude Code Calendar Sync")
    print(f"Fetching next {CONFIG['days_ahead']} days of events...\n")

    token = get_token()
    raw_events = get_events(token)
    events = [format_event(e) for e in raw_events]

    output = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "range_days": CONFIG["days_ahead"],
        "event_count": len(events),
        "events": events,
    }

    CONFIG["output_path"].parent.mkdir(parents=True, exist_ok=True)
    CONFIG["output_path"].write_text(json.dumps(output, indent=2))

    print(f"Wrote {len(events)} events to {CONFIG['output_path']}\n")

    # Quick summary
    for e in events:
        if e["isAllDay"]:
            when = (e["start"] or "")[:10] + " (all day)"
        else:
            when = (e["start"] or "")[:16].replace("T", " ")
        print(f"  {when}  {e['title']}")


if __name__ == "__main__":
    main()
