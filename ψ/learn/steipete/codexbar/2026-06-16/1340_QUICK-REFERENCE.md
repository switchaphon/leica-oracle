# CodexBar — Quick Reference

**Latest version**: Check releases at https://github.com/steipete/CodexBar/releases

## What is CodexBar?

CodexBar is a lightweight macOS menu bar app that displays AI coding-provider usage limits, credits, spend, and reset windows in real time. It tracks quotas across 53+ providers (Codex, OpenAI, Claude, Cursor, Gemini, Copilot, Grok, DeepSeek, Alibaba, AWS Bedrock, and many others) without storing passwords. Privacy-first: it reuses existing browser sessions, OAuth tokens, API keys, and local files from provider CLIs.

**Tagline**: "Every AI coding limit in your menu bar."

**Key insight**: Plan around provider resets instead of guessing when session/weekly/monthly quotas expire. Track spend and credits across multiple coding AI services in one place.

---

## Installation

### macOS App (Menu Bar)

#### Via Homebrew (Recommended)
```bash
brew install --cask codexbar
```

#### Direct Download
Download from: https://github.com/steipete/CodexBar/releases

#### First Launch
1. Open Settings → Providers
2. Enable providers you use
3. Sign into each provider (via OAuth, browser cookies, API key, or CLI)
4. Optional: Configure cost scanning (Settings → Codex/Claude)

### CLI (macOS/Linux)

#### macOS: From App
```bash
# After installing CodexBar.app, open Settings → Advanced → Install CLI
# OR manually:
ln -sf "/Applications/CodexBar.app/Contents/Helpers/CodexBarCLI" /usr/local/bin/codexbar
```

#### macOS/Linux: Homebrew
```bash
brew install steipete/tap/codexbar
```

#### macOS/Linux: Tarball Release
Download `CodexBarCLI-v<tag>-macos-arm64.tar.gz` or `CodexBarCLI-v<tag>-linux-aarch64.tar.gz` from GitHub Releases:
```bash
tar -xzf CodexBarCLI-v0.17.0-macos-arm64.tar.gz
./codexbar --version
./codexbar usage --format json
```

#### Arch Linux
```bash
yay -S codexbar-cli
```

### Requirements
- **App**: macOS 14+ (Sonoma)
- **CLI**: macOS 14+ or Linux (aarch64/x86_64)
- **Build from source**: Swift 6.2+

---

## Key Features

### Menu Bar Display
- **Per-provider tiles** showing usage bars, reset countdowns, and credit balances
- **Merge Icons mode** to combine all providers into one menu item with a switcher
- **Live status indicators** (incident badges) from provider status pages
- **Dynamic refresh** (default 5m; configurable to 1m–15m or manual)
- **No dock icon** — menu bar only, minimal footprint

### Provider Coverage

**Major coding providers:**
- Codex (OpenAI) — session, weekly, monthly usage + credits
- OpenAI — admin API spend/usage dashboards
- Claude — session/weekly usage, credits, plan info
- Cursor — plan, usage, billing resets
- Gemini — quota via CLI credentials
- Copilot — usage via device flow
- GitHub Copilot — gated session/monthly usage

**Code completion & IDE:**
- Devin — daily/weekly quotas
- Augment — credits tracking
- JetBrains AI — monthly credit quota
- Zed — plan + edit-prediction quota

**Inference API & voice:**
- z.ai — quota + MCP windows
- Kilo — credits + monthly reset
- Kiro — monthly credits
- AWS Bedrock — monthly budget + cost
- ElevenLabs — voice character credits
- Deepgram — token + speech/TTS usage
- OpenRouter, LiteLLM, Ollama — credit/spend tracking

**Other providers:**
- Mistral, DeepSeek, Venice, Moonshot, Doubao
- GroqCloud (Prometheus metrics), LLM Proxy
- MiniMax, Kimi, T3 Chat, Manus, Amp, Windsurf
- Perplexity, Alibaba (two plans), Synthetic, Chutes
- Poe (points), and more — see `docs/providers.md` for full list

### Usage Scanning & Cost Tracking
- **Local cost scans**: Parses `~/.codex` and `~/.claude` JSONL logs to calculate session/30-day token spend without API access
- **Admin API charts**: OpenAI and Claude admin keys enable spend/usage graphs in the menu
- **Web dashboards**: Optional Codex dashboard enrichment (code review remaining, daily breakdown, credits history)
- **Configurable windows**: Cost scan lookback (default 30 days)

### Multi-Account Support
- Store multiple Claude or Codex accounts in config
- Select per query with `--account <label>` or `--account-index <n>`
- Codex accounts enumerated per home + managed accounts
- Claude supports both session cookies and OAuth tokens

---

## Configuration

### Config File Location
- **New installs**: `~/.config/codexbar/config.json` (XDG)
- **Legacy**: `~/.codexbar/config.json` (still supported)
- **Override**: `CODEXBAR_CONFIG=/path/to/config.json`
- **File permissions**: `0600` (restricted to user only)

### Config Schema (JSON)

```json
{
  "version": 1,
  "providers": [
    {
      "id": "codex",
      "enabled": true,
      "source": "auto",
      "cookieSource": "auto",
      "cookieHeader": null,
      "apiKey": null,
      "enterpriseHost": null,
      "region": null,
      "workspaceID": null,
      "tokenAccounts": null
    }
  ]
}
```

### Key Config Fields
- **`id`** (required): provider identifier (e.g., `"codex"`, `"claude"`, `"openai"`)
- **`enabled`**: toggle provider on/off
- **`source`**: `auto|web|cli|oauth|api` — data source preference
- **`apiKey`**: raw API token for API-backed providers
- **`cookieSource`**: `auto` (browser import) | `manual` (use `cookieHeader`) | `off` (disabled)
- **`cookieHeader`**: HTTP `Cookie:` header value (e.g., `session=ABC; other=XYZ`)
- **`enterpriseHost`**: base URL override for proxy/custom endpoints
- **`region`**: regional variant (e.g., `minimax`)
- **`workspaceID`**: deployment ID, project ID, or workspace ID
- **`tokenAccounts`**: multi-account tokens (claude, codex, etc.)

### CLI Config Commands
```bash
codexbar config providers              # list all providers
codexbar config validate               # check config validity
codexbar config dump                   # print normalized config
codexbar config enable --provider grok # enable provider
codexbar config disable --provider cursor

# Store API key securely (sets restrictive permissions)
printf '%s' "$OPENAI_ADMIN_KEY" | codexbar config set-api-key --provider openai --stdin
printf '%s' "$ELEVENLABS_API_KEY" | codexbar config set-api-key --provider elevenlabs --stdin
```

### Manual Cookies

When automatic browser import isn't available, extract and paste the `Cookie:` header manually:

1. Open provider site in browser
2. Press F12 (DevTools) → Network tab
3. Perform a request on the provider site
4. Find any request, open its details
5. Copy the **`Cookie`** request header (not Set-Cookie)
6. Paste into Settings → Providers → [Provider] → Cookie
7. Validate: `codexbar usage --provider <id> --verbose`

Example config for manual cookies:
```json
{
  "id": "augment",
  "enabled": true,
  "cookieSource": "manual",
  "cookieHeader": "session=REDACTED; token=REDACTED"
}
```

---

## CLI Commands

### Default Usage
```bash
codexbar                    # text output, respects app toggles
codexbar --format json      # JSON output
codexbar --format json --pretty
```

### Usage Queries
```bash
codexbar usage                                     # default provider(s)
codexbar --provider claude                         # single provider
codexbar --provider both                           # two major providers
codexbar --provider all                            # all registered providers
codexbar --provider claude --account steipete@example.com
codexbar --provider claude --all-accounts          # all Claude accounts
codexbar --provider claude --account-index 1       # select by index
codexbar --source web                              # force web source
codexbar --source cli                              # force CLI source
codexbar --source api                              # force API source
```

### Cost Scanning
```bash
codexbar cost                                      # local cost (30-day default + today)
codexbar cost --days 90                            # custom window
codexbar cost --provider claude --format json
codexbar cost --refresh                            # ignore cache
```

### Server Mode (JSON over HTTP)
```bash
codexbar serve --port 8080                         # start localhost server
codexbar serve --refresh-interval 60               # cache TTL (seconds)
codexbar serve --request-timeout 30                # per-request deadline (0 = unlimited)

# Endpoints:
# GET /health
# GET /usage
# GET /usage?provider=claude
# GET /cost
# GET /cost?provider=both
```

### Cache Management
```bash
codexbar cache clear --cookies                    # clear cached browser cookies
codexbar cache clear --cookies --provider claude # single provider
codexbar cache clear --cost                       # clear cost scans
codexbar cache clear --all                        # cookies + cost
```

### Status & Diagnostics
```bash
codexbar --status                                  # include provider status pages
codexbar --verbose                                 # verbose logging
codexbar --log-level trace                         # trace-level logging
codexbar --json-output                             # JSONL on stderr (machine-readable)
codexbar --no-color                                # disable ANSI colors
```

### Sample Output

**Text (Claude example):**
```
== Claude Code 2.0.58 (web) ==
Session: 88% left [==========--]
Resets tomorrow at 1:00 AM
Weekly: 63% left [=======-----]
Pace: On pace | Expected 37% used | Runs out in 4d
Resets Sat at 6:00 AM
Sonnet: 95% left [===========-]
Account: user@example.com
Plan: Pro
```

**JSON (sample):**
```json
{
  "provider": "claude",
  "version": "2.0.58",
  "source": "web",
  "usage": {
    "primary": { "usedPercent": 12, "windowMinutes": 1440, "resetsAt": "2025-12-05T01:00:00Z" },
    "secondary": { "usedPercent": 37, "windowMinutes": 10080, "resetsAt": "2025-12-06T06:00:00Z" },
    "updatedAt": "2025-12-04T22:15:00Z"
  },
  "accountEmail": "user@example.com",
  "plan": "Pro"
}
```

### Exit Codes
- **0**: success
- **2**: provider missing (binary not on PATH)
- **3**: parse/format error
- **4**: CLI timeout
- **1**: unexpected failure

---

## Building from Source

### Requirements
- macOS 14+ or Linux
- Swift 6.2+
- Apple Developer account (optional; ad-hoc signing available)

### Build & Run
```bash
# Full build, test, and launch
./Scripts/compile_and_run.sh

# Also run test suite
./Scripts/compile_and_run.sh --test

# Package only (no launch)
./Scripts/package_app.sh

# Ad-hoc signing (no developer account)
CODEXBAR_SIGNING=adhoc ./Scripts/package_app.sh
```

### CLI Build
```bash
# Standalone CLI (without app)
swift build -c release --product CodexBarCLI
# Binary at: ./.build/release/CodexBarCLI

# After building the app, install CLI
./bin/install-codexbar-cli.sh
```

### Code Quality
```bash
make check        # SwiftFormat + SwiftLint
make format       # Auto-format
make test         # Run test suite
make docs-list    # List docs with summaries
```

### Code Structure
```
CodexBar/
├── Sources/CodexBarCore/        # Fetch logic (providers, parsing)
├── Sources/CodexBar/            # App UI (menu, preferences, widgets)
├── Sources/CodexBarWidget/      # macOS WidgetKit extension
├── Sources/CodexBarCLI/         # CLI binary
├── Sources/CodexBarClaudeWatchdog/  # Helper for stable PTY
├── Sources/CodexBarClaudeWebProbe/  # WebKit diagnostics
├── Tests/CodexBarTests/         # Unit + integration tests
└── Scripts/                     # Build, test, packaging
```

---

## macOS Permissions (Why They're Asked)

### Full Disk Access (Optional)
Required only to read Safari browser cookies/local storage. Alternatives:
- Use another supported browser (Chrome, Edge, Brave, Firefox)
- Configure manual cookies in Settings
- Use OAuth or API keys
- Use CLI-only sources where available

### Keychain Access (Prompted by macOS)
CodexBar accesses Keychain for:
1. Browser "Safe Storage" key (decrypt Chromium cookies)
2. OAuth/device-flow credential caching
3. Claude CLI Keychain bootstrapping

**To prevent prompts:**
1. Open **Keychain Access.app** → login keychain
2. Search for prompted item (e.g., "Claude Code-credentials")
3. Right-click → **Get Info** → **Access Control** tab
4. Add `CodexBar.app` under "Always allow access by these applications"
5. Relaunch CodexBar

**For browsers:**
- Find "Chrome Safe Storage", "Brave Safe Storage", etc.
- Add CodexBar to Access Control

**As last resort (disables all Keychain access):**
```bash
# Enable setting in Preferences → Advanced → Keychain access
# CodexBar will skip browser-cookie providers but CLI sources still work
```

### File/Folder Access
When CodexBar launches provider CLIs or reads local files, macOS may prompt for folder/volume access (Desktop, external drives). This is driven by the helper's working directory, not background disk scanning.

### NOT Requested
- Screen Recording
- Accessibility
- Passwords (cookies are reused; no stored passwords)

---

## Integration Examples

### GitHub Actions / CI
```bash
# Get usage as JSON in a GitHub Actions step
- name: Check Claude usage
  run: |
    codexbar --provider claude --format json --pretty > /tmp/usage.json
    cat /tmp/usage.json
```

### Zsh/Bash Alias
```bash
# Add to ~/.zshrc or ~/.bashrc
alias codex-usage='codexbar --provider codex --no-color'
alias claude-usage='codexbar --provider claude --format json --pretty'
```

### Automated Alerts
```bash
#!/bin/bash
USAGE=$(codexbar --provider codex --format json | jq '.usage.primary.usedPercent')
if (( $(echo "$USAGE > 80" | bc -l) )); then
  echo "Codex session at ${USAGE}%"
fi
```

### Web Dashboard (via serve)
```bash
# Start server
codexbar serve --port 8080 &

# Poll from another script/web client
curl -s http://localhost:8080/usage?provider=claude | jq .
```

---

## Comparison to Similar Tools

### CodexBar vs. ccusage
- **ccusage**: Cost tracking only (OpenAI/Claude token spend)
- **CodexBar**: Broader scope — 53+ providers, usage windows, credits, status, reset countdowns, cost, CLI + menu bar

### CodexBar vs. Provider Dashboards
- **Provider dashboards**: Web-only, slow, scattered across 50+ sites
- **CodexBar**: Single view, all providers at once, menu bar integration, CLI for automation

### CodexBar vs. Custom Scripts
- **Scripts**: Single provider, manual setup, no UI
- **CodexBar**: All providers, unified config, privacy-first (reuses existing auth), menu + CLI, status monitoring

### CodexBar vs. Consumption Trackers (Perplexity, Cursor, etc.)
- **In-app trackers**: Only for that service
- **CodexBar**: Aggregates across all your coding AI subscriptions

---

## Privacy & Security

### What CodexBar Does NOT Do
- Store passwords or credentials (reuses existing sessions)
- Crawl your filesystem (reads only known provider config/cache locations)
- Send data to external services (local parsing by default)
- Request unnecessary permissions (Full Disk Access only for Safari cookies)

### What It Does
- Reads browser cookies (opt-in; you choose which browser)
- Reads local provider config files (`~/.codex`, `~/.claude`, etc.)
- Uses OAuth tokens (stored in Keychain or config)
- Reuses existing API credentials from environment or config
- Caches parsed data locally (in CodexBar config file with `0600` permissions)

### Config File Security
- Stored at `~/.config/codexbar/config.json` or `~/.codexbar/config.json`
- Permissions: `0600` (user-only read/write)
- Contains: API keys, manual cookies, provider settings
- **Never commit to git or share publicly**

---

## Settings Overview

### Preferences → General
- **Refresh interval**: 1m, 2m, 5m (default), 15m, or manual
- **Display mode**: One icon per provider or Merge Icons (one menu item)
- **Icon display**: Show labels, bars, or both
- **Reset countdown style**: Countdown (e.g., "5h") or exact time (e.g., "2:30 PM")
- **Auto-select highest usage**: automatically show most-used provider on bar click
- **Notifications**: optional session/weekly reset alerts, confetti

### Preferences → Providers
- Toggle each provider on/off
- Configure provider-specific settings:
  - API key entry
  - Browser/manual/off cookie source
  - OAuth/API source selection
  - Multi-account setup
  - Workspace ID, deployment, region

### Preferences → Advanced
- **Install CLI**: symlink `codexbar` to `/usr/local/bin`
- **File logging**: enable logging to `~/Library/Logs/CodexBar/CodexBar.log`
- **Keychain access**: disable Keychain reads (last resort for keychain prompt issues)
- **Main thread hang detection**: debug slow refreshes

### Codex/Claude Cost Scan Settings
- **Enable cost scanning**: local JSONL log parsing
- **Window**: 7, 14, 30, or 90 days
- **Auto-refresh**: fetch latest logs on each usage refresh

---

## Troubleshooting

### Keychain Prompts on Every Launch
Check if one-time migration completed:
```bash
defaults read com.steipete.codexbar KeychainMigrationV1Completed
# Should output: 1
```

If not, reset and retry:
```bash
defaults delete com.steipete.codexbar KeychainMigrationV1Completed
# Relaunch CodexBar (migration runs once)
```

### Cookies Not Refreshing
1. Verify you're logged into the provider in that browser
2. Check Preferences → Providers → [Provider] → Cookie Source is "Automatic"
3. Ensure CodexBar has Full Disk Access if using Safari
4. Try "Manual" and copy the cookie header from DevTools

### CLI Not Found
```bash
# Check installation
which codexbar
/usr/local/bin/codexbar --version

# Manual install
ln -sf "/Applications/CodexBar.app/Contents/Helpers/CodexBarCLI" /usr/local/bin/codexbar
```

### No Usage Data After Enable
1. Make sure provider is toggled ON in Settings
2. Sign into the provider (OAuth, cookie, or API key)
3. Refresh manually: click menu bar icon or `codexbar --refresh`
4. Check app logs: Settings → Advanced → File logging, then tail `~/Library/Logs/CodexBar/CodexBar.log`

### App Won't Launch
Check crash logs:
```bash
ls -lt ~/Library/Logs/DiagnosticReports/CodexBar* | head -5
cat ~/Library/Logs/DiagnosticReports/CodexBar_*.crash
```

---

## Related Projects

- **Trimmy**: https://github.com/steipete/Trimmy — flatten shell snippets for pasting
- **MCPorter**: https://mcporter.dev — TypeScript MCP server toolkit
- **Oracle**: https://askoracle.dev — custom GPT-5 Pro with context
- **Win-CodexBar**: https://github.com/Finesssee/Win-CodexBar — Windows equivalent
- **codexbar-waybar**: Wayland desktop integration
- **CodexBar GNOME**: GNOME Shell extension
- **noctalia-codex-usage**: Quickshell plugin for quota display
- **showy-quota**: SketchyBar/tmux/Zellij integration (uses `codexbar serve`)

---

## Documentation & Resources

| Resource | Link |
|----------|------|
| **CLI Reference** | `docs/cli.md` |
| **Configuration** | `docs/configuration.md` |
| **Providers List** | `docs/providers.md` |
| **Architecture** | `docs/architecture.md` |
| **Development** | `docs/DEVELOPMENT.md` |
| **Release Process** | `docs/RELEASING.md` |
| **Widgets** | `docs/widgets.md` |
| **Status Polling** | `docs/status.md` |
| **Refresh Loop** | `docs/refresh-loop.md` |
| **UI Notes** | `docs/ui.md` |
| **Changelog** | `CHANGELOG.md` |
| **GitHub** | https://github.com/steipete/CodexBar |
| **Website** | https://codexbar.app |

---

## Quick Start Checklist

- [ ] Install CodexBar (Homebrew or direct download)
- [ ] Open Settings → Providers
- [ ] Enable providers you use
- [ ] Sign in to each (OAuth, browser cookies, API key, or CLI)
- [ ] Set refresh interval (default 5m is good)
- [ ] Optional: enable cost scanning (Codex/Claude)
- [ ] Click menu bar icon to view usage
- [ ] For CLI: `codexbar usage --format json`
- [ ] For automation: `codexbar serve` on localhost:8080

---

## License

MIT — Peter Steinberger (@steipete)

**Inspired by**: ccusage (MIT) — specifically cost tracking
