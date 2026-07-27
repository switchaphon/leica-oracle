# RunCat Neo: Quick Reference

## What is RunCat Neo?

RunCat Neo is a cute, animated cat running in your macOS menubar that visualizes CPU usage through animation speed — the busier your CPU, the faster the cat runs. It's a next-generation rewrite of the original RunCat, providing:

- **Visual CPU monitoring** — one glance shows system load
- **Rich system metrics** — CPU, memory, storage, battery, network status
- **Custom metrics dashboard** — display any data you can write to a JSON file
- **Customizable runners** — beyond cats, use any runner animation from the Runner Gallery
- **Multi-language support** — English, Japanese, Chinese (Simplified & Traditional), Korean, French, German, Spanish, Russian, Vietnamese

## Installation

**App Store (recommended)**
- Requires macOS 26 or later
- Download: https://apps.apple.com/us/app/runcat-neo/id6757801838
- Simple one-click installation with automatic updates

*Note: Homebrew and DMG distributions are not mentioned in the documentation; App Store is the primary distribution channel.*

## Custom Metrics Overview

RunCat Neo can watch any local JSON file and render it as a dashboard card that updates in real-time. The app uses filesystem events to detect changes — never polling the file and never making network calls. Perfect for tracking Claude Code usage, GPU temps, Bitcoin prices, GitHub stats, or anything you can write to a file.

**Setup workflow:**
1. Create a script that writes JSON to a file (e.g., `~/.yourapp/runcat-metrics.json`)
2. Open RunCat Neo → Settings → Metrics → Custom Metrics → "Add Custom Metrics Source"
3. Select your JSON file
4. The card appears on the dashboard immediately and updates whenever the file changes

## JSON Schema for Custom Metrics

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | **Yes** | Card header (e.g., "Claude Code", "Bitcoin") |
| `symbol` | string | No | SF Symbol identifier shown next to title. Defaults to `chart.bar.horizontal.page.fill` |
| `metricsBarValue` | string | No | Short text shown in the Metrics Bar (menubar item). Keep it short; longer strings are truncated. Hidden by default — user toggles visibility in Metrics Bar settings. Renders as `---` if omitted. |
| `metrics` | array | **Yes** | Array of metric rows. Empty array allowed. |
| `lastUpdatedDate` | string | **Yes** | ISO 8601 timestamp (e.g., `"2026-06-05T04:50:40Z"`). Shown as relative time ("3 min ago") at card footer. |

### Metric Row Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | **Yes** | Row label |
| `formattedValue` | string | **Yes** | Display string (include units, %, $, etc.). Shown as-is; no app-side formatting. |
| `normalizedValue` | number | No | Value between 0–1. When present, a progress bar is drawn below the row. Clamped to `[0, 1]`. |

### Example JSON

```json
{
  "title": "Claude Code",
  "symbol": "staroflife",
  "metricsBarValue": "5.4%",
  "metrics": [
    { "title": "Model", "formattedValue": "Opus 4.7" },
    { "title": "Context", "formattedValue": "5.4%", "normalizedValue": 0.054 },
    { "title": "5h", "formattedValue": "16.4%", "normalizedValue": 0.164 },
    { "title": "7d", "formattedValue": "1.0%", "normalizedValue": 0.01 }
  ],
  "lastUpdatedDate": "2026-06-05T04:50:40Z"
}
```

### Key Display Rules

- **Producer-side formatting is intentional** — no rounding, units, or suffixes applied by RunCat
- `normalizedValue` is clamped to `[0, 1]` before rendering
- Progress bars always use the accent color (no conditional coloring based on value)
- Empty `metrics` array shows only title and last-updated time
- `metricsBarValue` renders in monospaced digits
- **Write atomically** — write to a temp file in the same directory, then `mv` it into place to avoid partial reads
- Keep file size modest (well under 1MB)

## Available SF Symbols

SF Symbols (Symbols from Apple) are used as card icons. Common examples found in samples:

- `staroflife` — star (used in Claude Code sample)
- `bitcoinsign` — Bitcoin symbol (used in Bitcoin sample)
- `chart.bar.horizontal.page.fill` — default, horizontal bar chart
- Any other valid SF Symbol identifier works; see [Apple's SF Symbols](https://developer.apple.com/sf-symbols/) for the full catalog

*Symbol availability depends on your macOS version. Use the SF Symbols app (macOS 12.1+) to browse and test identifiers.*

## Sample Integrations in Docs

### 1. Claude Code Status Line Sample
**Location:** `docs/samples/claude-code/`

Displays model name, context window usage, and rate limits from Claude Code sessions.

**Setup:**
1. Copy `runcat-statusline.py` to `~/.claude/runcat-statusline.py` and make executable
2. Register in `~/.claude/settings.json`:
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "/Users/YOU/.claude/runcat-statusline.py"
     }
   }
   ```
3. Add `~/.claude/runcat-usage.json` as a custom metrics source in RunCat
4. Script runs on every Claude Code turn, writes usage snapshot

**Output:** Model, Context %, 5-hour rate limit, 7-day rate limit

**Environment variable:** `RUNCAT_OUT_FILE` — override output path

### 2. Codex Lifecycle Hook Sample
**Location:** `docs/samples/codex/`

Reads Codex session transcripts and writes model, context, rate limits.

**Setup:**
1. Copy `runcat-hook.py` to `~/.codex/runcat-hook.py` and make executable
2. Register in `~/.codex/hooks.json` `Stop` hook array
3. Add `~/.codex/runcat-usage.json` as custom metrics source
4. Codex calls the hook after each turn

**Requires:** Codex hooks feature enabled (enabled by default in current releases)

**Output:** Model name, Context window usage %, rate limit windows (5h, 7d, etc.)

**Note:** Parses Codex session transcripts; may need adjustment if transcript format changes between releases

### 3. Bitcoin Price Sample
**Location:** `docs/samples/bitcoin/`

Fetches current Bitcoin price from CoinGecko public API (no auth), updates every 10 minutes via `launchd`.

**Setup:**
1. Copy `update-bitcoin.sh` to `~/.runcat/update-bitcoin.sh` and make executable
2. Copy `dev.runcat.bitcoin-sample.plist` to `~/Library/LaunchAgents/`, update home path
3. Run `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/dev.runcat.bitcoin-sample.plist`
4. Add `~/.runcat/bitcoin.json` as custom metrics source

**Output:** Current Bitcoin price in USD (e.g., `$61,888.04`)

**Customization:** Edit API URL and `awk` formatting to use different cryptocurrencies or currencies. Modify `StartInterval` in plist to change update frequency (default: 10 minutes).

**To stop:** `launchctl bootout gui/$(id -u)/dev.runcat.bitcoin-sample`

## How to Write Your Own Custom Metric Source

### Prerequisites
- A script or program (Python, shell, Node, Go, etc.)
- Ability to write JSON to a file on disk
- Understanding of the schema above

### Basic Pattern

```python
#!/usr/bin/env python3
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

OUTPUT_PATH = Path.home() / ".yourapp" / "runcat.json"

# Generate your metric data
snapshot = {
    "title": "Your Metric",
    "symbol": "chart.bar.fill",  # pick any SF Symbol
    "metricsBarValue": "42%",
    "metrics": [
        {"title": "Item 1", "formattedValue": "value"},
        {"title": "Item 2", "formattedValue": "50%", "normalizedValue": 0.50},
    ],
    "lastUpdatedDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}

# Write atomically
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
fd, tmp = tempfile.mkstemp(dir=str(OUTPUT_PATH.parent))
with os.fdopen(fd, "w") as f:
    json.dump(snapshot, f, ensure_ascii=False)
os.replace(tmp, OUTPUT_PATH)
```

### Triggering Updates

**On-demand:** Script runs when an event occurs
- Claude Code statusLine command (runs every turn)
- Codex lifecycle hook (after each turn)
- Custom script you invoke manually or via cron/launchd

**Scheduled:** Use `launchd` to run periodically
- Copy the bitcoin sample's plist and adjust paths and interval
- Modify `StartInterval` (seconds) for update frequency

**Filesystem events:** RunCat reacts to file changes; no polling needed

### Key Implementation Details

1. **Atomic writes** — write to temp file, then `mv` to final location
2. **ISO 8601 timestamps** — use `"2026-06-05T04:50:40Z"` format
3. **Clamped values** — `normalizedValue` is clamped to `[0, 1]`, but you can write any value
4. **Strict JSON** — no comments, no trailing commas
5. **File size** — keep under 1MB
6. **Permissions** — ensure the file remains readable by RunCat
7. **Environment variable** — check `RUNCAT_OUT_FILE` env var to allow user customization

## Troubleshooting

### Card Shows Nothing
- Confirm the JSON file is being written. Run your script manually and check the file:
  ```bash
  cat ~/.yourapp/runcat.json | python3 -m json.tool  # Python
  ```
- Verify valid JSON (no trailing commas, no comments)
- Confirm `metrics` array is not empty (or populate it with at least one row)

### Card Stays at Same Values
- Check the file's modification time (`ls -l`). If it's not updating, your producer script isn't running
- For scheduled updates, verify launchd agent is loaded: `launchctl print gui/$(id -u)/your.agent.name`
- For event-driven updates (Claude Code, Codex), confirm the trigger tool is configured correctly

### Card Footer Shows "Last updated: Failed" (Red)
- File became unreadable (deleted, moved, or permission revoked)
- Check file exists: `ls ~/.yourapp/runcat.json`
- Check readable: `cat ~/.yourapp/runcat.json` (should print JSON)
- RunCat retries every 5 seconds; fix and the card recovers automatically on next successful read
- In settings, you'll see a yellow `⚠︎ Error Detected` label next to the source

### File Never Appears (Scheduled via launchd)
- Run the script manually to see errors
- Check launchd configuration: paths must be absolute, match your home directory
- Verify the plist is in the right location: `~/Library/LaunchAgents/`
- Load it manually: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/your.plist`
- Check system logs: `log stream --predicate 'process == "launchd"' --level debug`

### Symbol Not Displaying
- Verify the SF Symbol identifier is valid for your macOS version
- Use the SF Symbols app to browse and test names
- Common typos: `staroflife` (not `star`), `bitcoinsign` (not `bitcoin`)

### Permission Issues
- RunCat uses security-scoped bookmarks; once added, access survives sandbox restarts
- If you delete and re-add a source, RunCat re-bookmarks it
- Ensure the file lives in a location the app can read (home directory, /tmp, etc.)

## Configuration Options

### General Settings
**Update Interval** — frequency at which RunCat samples system metrics

Available options:
- 3 seconds (high frequency, more CPU usage)
- 5 seconds (default, balanced)
- 10 seconds (lower frequency, lower CPU usage)

**Launch at Login** — toggle whether RunCat starts automatically when you log in

### Metrics Settings
- Toggle visibility of built-in metrics (CPU, memory, storage, battery, network)
- Manage custom metrics sources

### Metrics Bar Settings
- Toggle visibility of individual custom metrics in the menu bar
- Customize which sources appear in the menu bar next to the runner icon
- Each source's `metricsBarValue` is shown in a dedicated menu-bar item (if enabled)

### Runner Settings
- Switch between available runners (cat, other characters from Runner Gallery)
- Custom runners are managed in the [Runner Gallery](https://runcat-dev.github.io/RunnerGallery/), not in RunCat itself

## File Locations

- **Bookmarks:** RunCat stores security-scoped file bookmarks in `~/Library/Preferences/com.kyome22.RunCatNeo.plist` (managed by the app; you don't edit this)
- **Logs:** Check Console.app (filter for "RunCatNeo") for debug output
- **Sample outputs:** Typically stored in user home subdirectories:
  - Claude Code: `~/.claude/runcat-usage.json`
  - Codex: `~/.codex/runcat-usage.json`
  - Bitcoin: `~/.runcat/bitcoin.json`

## Architecture & Tech Stack

- **Language:** Swift 6.2
- **Framework:** SwiftUI
- **macOS minimum:** 26.3+
- **Xcode requirement:** 26.5+ (for development)
- **Architecture pattern:** LUCA (Layered Unidirectional Cycle Architecture) — strict separation between UI, business logic, and data layers
- **Open source:** Licensed under Apache 2.0

## Resources

- **Documentation:** https://github.com/runcat-dev/RunCatNeo
- **JSON Schema reference:** docs/CustomMetricsSchema.md
- **Sample integrations:** docs/samples/ (Claude Code, Codex, Bitcoin)
- **Custom runners:** https://runcat-dev.github.io/RunnerGallery/
- **Contributors & community:** https://runcat-dev.github.io

---

**This reference captures the essential setup, schema, samples, and troubleshooting info needed to integrate RunCat Neo custom metrics into any workflow. The atomic write pattern and filesystem event-driven updates make it lightweight and reliable for any data source you maintain.**
