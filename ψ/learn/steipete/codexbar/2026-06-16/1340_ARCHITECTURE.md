# CodexBar Architecture

**Date**: 2026-06-16  
**Scope**: macOS 14+, Swift 6.2+, 58 AI provider integrations  
**Theme**: "Every AI coding limit in your menu bar"

## Executive Summary

CodexBar is a sophisticated macOS menu bar application that aggregates usage metrics from 58+ AI coding providers (Codex, Claude, OpenAI, Cursor, Gemini, etc.). It displays real-time usage, reset countdowns, credit balances, and spending data with privacy-first design (browser cookies reused, no passwords stored).

The architecture separates **fetch + parse logic** (CodexBarCore) from **state + UI** (CodexBar app), supporting multiple distribution channels: menu bar app, CLI tool, WidgetKit extension, and watchdog processes.

---

## Directory Structure & Organization

```
Sources/
├── CodexBarCore/
│   ├── Config/                    # Configuration loading, validation, persistence
│   ├── Providers/                 # 58 provider integrations (one subdir per provider)
│   │   ├── Claude/                # Claude API, OAuth, web scraping, PTY probe
│   │   ├── OpenAI/                # OpenAI Admin API, web dashboard parsing
│   │   ├── Codex/                 # Codex OAuth, RPC client, managed accounts
│   │   ├── Cursor/                # Browser cookie parsing
│   │   ├── [50 more providers]    # Alibaba, Gemini, Copilot, Kimi, Warp, etc.
│   ├── Host/                      # System integration (process launch, PTY, file I/O)
│   │   ├── Process/               # Process spawning, exit handling
│   │   └── PTY/                   # PTY management for CLI interactions
│   ├── OpenAIWeb/                 # Web scraping for OpenAI dashboard
│   ├── Logging/                   # OSLog-based structured logging
│   ├── CostUsageFetcher.swift     # Unified fetcher orchestrating all providers
│   ├── UsageFetcher.swift         # Top-level fetch dispatcher, caching
│   ├── WidgetSnapshot.swift       # Shared state snapshot for WidgetKit
│   └── [Core models & utilities]
│
├── CodexBar/                      # App UI, state management, menu bar
│   ├── UsageStore.swift           # Central @Observable state machine
│   ├── StatusItemController.swift # Menu bar icon & popover control
│   ├── SettingsStore.swift        # User preferences, config persistence
│   ├── CodexbarApp.swift          # SwiftUI entry point
│   ├── PreferencesView.swift      # Settings UI (providers, display, etc.)
│   └── [100+ supporting views & coordinators]
│
├── CodexBarWidget/                # WidgetKit extension (iOS/macOS)
│   ├── CodexBarWidgetProvider.swift
│   └── CodexBarWidgetViews.swift
│
├── CodexBarCLI/                   # Command-line tool
│   └── [CLI subcommand handlers]
│
├── CodexBarClaudeWatchdog/        # Helper: keeps Claude PTY session alive
│
└── CodexBarClaudeWebProbe/        # Helper: diagnoses Claude web fetches

Tests/ & TestsLinux/               # Swift Testing suite (~40 test files)
```

---

## Core Abstractions & Their Relationships

### Layer 1: Data Models (Codable, Sendable)

**RateWindow & NamedRateWindow**
- Represents usage quota windows (session, weekly, monthly)
- Fields: `usedPercent`, `windowMinutes`, `resetsAt`, `resetDescription`, `nextRegenPercent`
- Used by all 58 providers; provider-specific fields in specialized structs

**UsageSnapshot** (Main aggregation struct)
- Container for all usage metrics fetched in one cycle
- Holds: primary/secondary/tertiary RateWindow, provider-specific usage (Kiro, z.ai, MiniMax, etc.), identity metadata, timestamp
- Codable for persistence; Sendable for async safety

**ProviderIdentitySnapshot**
- Email, organization, login method for account context
- Used in menu display ("Claude • user@example.com" + scoped views)

**Provider-Specific Models**
- `ClaudeUsageSnapshot`: primary + secondary + opus windows + extra rate windows
- `OpenAIAPIUsageSnapshot`: credit-based usage tracking
- `CursorRequestUsage`: request limit data
- `MiniMaxUsageSnapshot`: token-based plus credit windows
- `KiroUsageDetails`, `ZaiUsageSnapshot`, `AmpUsageDetails`, etc. — each provider's specialized format

**ProviderCostSnapshot**
- Shared cost breakdown: API spend, cost per hour/day/month, historical trends
- Used by OpenAI, Claude Admin API, OpenRouter, LiteLLM, Bedrock, etc.

### Layer 2: Fetch & Parse (Core logic in CodexBarCore)

**UsageFetcher** (`UsageFetcher.swift`)
- Top-level dispatcher: coordinates all 58 provider fetchers
- Handles: parallelism, retries, timeout management, caching invalidation
- Returns `UsageSnapshot` (or provider-specific snapshots)
- Key methods:
  - `loadAccountInfo()` → AccountInfo (user identity for CLI)
  - `loadProviderUsage(for:settings:)` → UsageSnapshot

**ProviderDescriptor & ProviderMetadata**
- Registry of all 58 providers with metadata (displayName, cliName, defaultEnabled, status URLs, etc.)
- Enables dynamic provider list and settings UI construction
- Defined in `ProviderDescriptor.swift`; registry in `ProviderDescriptorRegistry` (generated)

**Per-Provider Fetcher Pattern** (each provider subdir)
- Example: `ClaudeUsageFetcher` (protocol: `ClaudeUsageFetching`)
  - Tries multiple data sources in order: API, CLI, OAuth, web scraping
  - Returns `ClaudeUsageSnapshot` with parsed windows and identity
  - Errors: `claudeNotInstalled`, `parseFailed`, `oauthFailed`
- Each provider has:
  - Data source abstraction (e.g., `ClaudeUsageDataSource`)
  - Error types specific to auth/availability
  - Session management (cookies, OAuth tokens, CLI sessions)

**CostUsageScanExecutor**
- Scans local Codex & Claude JSONL logs to extract token usage + cost
- Parses provider-specific log formats (e.g., `~/.codex/output.json`)
- Enables offline cost tracking without API calls

**BrowserCookieAccessGate & KeychainAccessGate**
- Gating mechanisms for privacy-sensitive operations
- Can be disabled in settings (e.g., "Disable Keychain access")
- Browser cookie imports require Full Disk Access consent
- Keychain caching for decryption keys + OAuth credentials

### Layer 3: State Management (CodexBar app)

**UsageStore** (`UsageStore.swift` + 30 extensions)
- Central observable state machine (Swift Observation framework)
- Holds: `snapshots: [UsageProvider: UsageSnapshot]`, refresh state, error tracking
- Key responsibilities:
  - Coordinates background refresh loops (timer-based, menu interaction-triggered)
  - Caches snapshots with TTL
  - Manages fetch cancellation + timeout handling
  - Tracks stale/error states per provider
  - Publishes widget snapshot to app group container
  - Monitors memory pressure + clears caches under stress
  - Logs usage pace (for historical trend analysis)

**SettingsStore** (`SettingsStore.swift` + 20 extensions)
- Persists user preferences to `~/.config/codexbar/config.json` (or legacy `~/.codexbar/`)
- Manages: provider toggles, API keys, refresh cadence, display preferences, menu style
- Validates config on load (e.g., endpoint overrides)
- Detects & reconciles provider availability (e.g., Claude CLI installed?)
- Publishes changes to UsageStore to trigger refresh

**Config** (CodexBarConfig.swift & related)
- Strongly typed config structure matching JSON schema
- Validation: API key format, URL overrides, token account settings
- Supports environment variable override of config paths
- Restrictive file permissions (0o600) for config files containing secrets

### Layer 4: UI & Menu Bar (CodexBar app)

**CodexbarApp** (Main SwiftUI scene)
- Initializes SettingsStore, UsageStore, AppDelegate
- Passes stores to status item controller
- Registers app lifecycle handlers (launch at login, Sparkle updates)
- Sets up logging level from defaults or env vars

**StatusItemController** (`StatusItemController.swift` + 40 extensions)
- Owns NSStatusItem (menu bar presence)
- Builds & updates popover menu from UsageStore snapshots
- Coordinates: icon rendering, animation, menu recycling, smart updates
- Key extensions:
  - `+Menu`: constructs NSMenu from provider snapshots
  - `+MenuCardItems`: individual provider "tiles" in popover
  - `+IconPerf`: optimizes icon updates (batching, caching size)
  - `+MenuRefreshScheduling`: coordinates timing of menu rebuilds
  - `+Animation`: animates icon meter changes
  - `+Shutdown`: cleanup on app exit

**IconRenderer** (`IconRenderer.swift`)
- Renders real-time usage meter as template image
- Icon size: 16x16 on macOS menu bar
- Shows: usage bar (filled color), error indicator (red X), incident badge
- Caching: icon templates with size fingerprinting

**MenuCardView** (`MenuCardView.swift` + extensions)
- SwiftUI view representing one provider's "tile" in the popover menu
- Shows: provider icon, display name, primary usage bar, reset countdown, secondary/tertiary windows, cost/spend info
- Provider-specific views: MiniMax card (2-tier window display), Kiro card (monthly credit breakdown)
- Click-to-copy overlays for tokens/emails

**PreferencesView** (`PreferencesView.swift` + panes)
- Settings window with tabs: General, Providers, Display, Advanced, About, Debug
- Providers pane: enable/disable toggles, API key input, cookie/auth method selection
- Display pane: icon style (per-provider or merged), label/bar/reset-time display preferences
- Advanced: refresh cadence, quota warnings, Keychain access toggle

---

## Entry Points & Initialization Flow

### macOS App Entry Point

```
@main CodexbarApp
    ↓
CodexbarApp.init()
    • Parse debug log level from defaults/env
    • Initialize Logging, MainThreadHangWatchdog
    • Create SettingsStore (loads config from ~/.config/codexbar/config.json)
    • Create UsageFetcher
    • Load AccountInfo (for CLI identity)
    • Create UsageStore (with fetcher + browserDetection + settings)
    • Create coordinators (ManagedCodexAccountCoordinator, CodexAccountPromotionCoordinator)
    • Configure AppDelegate
    ↓
AppDelegate
    • Create StatusItemController (wires stores)
    • Set up Sparkle auto-update
    • Install notification listeners (session quota, weekly reset confetti)
    • Register keyboard shortcuts
    ↓
StatusItemController
    • Observe UsageStore for snapshot changes
    • Render menu bar icon
    • Show popover on click
    • Schedule background refreshes
```

### CLI Entry Point

```
main (CodexBarCLI)
    ↓
Command parser (Commander)
    ├── codexbar usage --provider <name>
    ├── codexbar cost --provider <name>
    ├── codexbar serve (HTTP server for external consumers)
    ├── codexbar config providers (list provider settings)
    └── codexbar config set-api-key --provider <name> --stdin
    ↓
UsageFetcher (same as app)
    ↓
Output: JSON or human-readable text
```

### WidgetKit Entry Point

```
CodexBarWidget
    ↓
CodexBarWidgetProvider (timeline-based)
    • Reads WidgetSnapshot from app group container
    • Updates on timer (15-30 min cadence)
    ↓
CodexBarWidgetViews (lock screen + notification widgets)
```

---

## Data Flow: Refresh Loop

### Background Refresh Cycle

```
User clicks menu bar icon or timer fires (1m/2m/5m/15m preset)
    ↓
UsageStore.refresh(force: .userInitiated)
    ↓
UsageFetcher.loadProviderUsage(for: provider, settings:)
    ↓
Per-provider fetcher (e.g., ClaudeUsageFetcher):
  1. Try API source (e.g., Claude API endpoint)
  2. Fall back to CLI source (e.g., `claude tokens`)
  3. Fall back to web source (e.g., browser cookies)
  4. Parse response → UsageSnapshot (or provider-specific snapshot)
    ↓
CostUsageFetcher (optional, if cost tracking enabled):
    • Scan local JSONL logs
    • Parse token usage per model
    • Calculate cost from token * price_per_1k
    ↓
Snapshot cached in UsageStore
    ↓
StatusItemController observes change
    ↓
Render icon (IconRenderer):
    • Calculate usage percent from primary RateWindow
    • Fill color: green (0-50%), yellow (50-80%), red (80-100%)
    • Update menu bar display
    ↓
Update popover menu (on demand, or if open):
    • Rebuild MenuCardView list from snapshots
    • Animate progress bars
    • Update reset countdowns
    ↓
Publish WidgetSnapshot to app group (for widgets)
```

### Error Handling & Fallbacks

- **Timeout**: 12s for auto-probe (CLI), 24s for manual (browser), 60s for retry
- **Network errors**: Preserve cached snapshot, dim icon with error indicator
- **Parse failures**: Log details, mark provider as errored, allow manual re-run
- **Missing credentials**: Show inline settings prompt in menu

---

## Key Design Decisions

### 1. Privacy-First Architecture

- **No password storage**: Reuse browser cookies (opt-in), OAuth tokens (cached in Keychain), CLI sessions
- **Gating mechanisms**: BrowserCookieAccessGate, KeychainAccessGate allow user to disable risky operations
- **Offline fallback**: Can read local config/logs without network
- **Keychain prompt minimization**: Pre-authorize CodexBar in Keychain Access UI to avoid repeated prompts

### 2. Multi-Layered Fallback Strategy

Example (Claude):
1. API: `~/.claude/config.json` API endpoint + OAuth cached token
2. CLI: `claude tokens` command via PTY → parse output
3. Web: Decrypt browser cookies (Chrome/Safari) + scrape dashboard JavaScript
4. Fallback: Show cached value with age indicator

Each layer is independent; higher layers mask lower-layer failures.

### 3. Swift 6 Strict Concurrency

- All core data models are `Sendable` (no unsafeTransfer except where justified)
- `UsageStore` is `@Observable` (main thread bound)
- Fetchers use async/await, avoiding callbacks
- Logging via `nonisolated(unsafe)` static providers to work around Sendable constraints
- Preference: explicit `@MainActor` hops over `@MainActor` class decorators

### 4. Provider Registry (Generated Code)

- `ProviderDescriptor.swift` is hand-written, extensible
- `ProviderDescriptorRegistry` is code-generated from descriptors
- Enables: dynamic UI (provider toggles), CLI argument completion, metadata-driven config validation
- Adding a provider: define ProviderDescriptor, generator updates registry

### 5. Snapshot Caching & TTL

- UsageStore caches per-provider snapshots with default TTL: 3 min (short for interactive feel)
- Background refresh on timer: 1/2/5/15 min presets (user-configurable)
- Invalidation triggers: app launch, menu interaction, manual refresh, provider toggled on
- Stale data: icon dimmed, menu shows "Last updated X min ago"

### 6. Modular Provider Architecture

Each provider (58 total):
- Minimal `ProviderDescriptor` entry (metadata)
- `*UsageFetcher` (protocol + struct implementing `UsageFetching`)
- `*UsageSnapshot` (data model)
- Optional: `*CookieStore`, `*TokenStore`, `*OAuthFlow`
- Zero coupling: one provider failure doesn't block others

### 7. Cross-Cutting Concerns

**Logging**: Structured OSLog (com.steipete.codexbar subsystem) with categories
- `app`, `fetchcore`, `claudeUsage`, `openaiUsage`, etc.
- Production: filtered to `.notice` level (minimal overhead)
- Debug: `.debug` or `.verbose` via CODEXBAR_LOG_LEVEL env var

**Memory Pressure**: UsageStore clears old snapshots when system memory pressure > .moderate (Darwin API)

**Keychain Prompt Coordination**: Defers Keychain UI to specific user actions (login, OAuth refresh), not background fetches

---

## Dependencies (Direct & Transitive)

### Direct (Package.swift)

| Dependency | Purpose | Usage |
|---|---|---|
| **Sparkle** (2.9.1+) | Auto-update framework | App updates via GitHub releases |
| **Commander** (0.2.1+) | CLI argument parsing | CodexBarCLI subcommands |
| **swift-crypto** (3.0.0+) | Cryptographic operations | Cookie encryption/decryption |
| **swift-log** (1.12.0+) | Structured logging | OSLog bridging |
| **KeyboardShortcuts** (2.4.0+) | Keyboard shortcut management | Menu bar hotkey (cmd+shift+A) |
| **Vortex** (revision) | Visual effects library | Confetti overlay (weekly reset celebration) |
| **SweetCookieKit** (0.4.1+) | Browser cookie parsing | Chrome, Safari, Brave, Edge cookie import |

### Transitive

- **Foundation**: Core Swift stdlib (async/await, Codable, URLSession, FileManager, ProcessInfo)
- **AppKit**: macOS UI (NSStatusItem, NSMenu, NSWindow, NSApplication)
- **SwiftUI**: Modern UI framework (Views, State, Observation)
- **Security**: Keychain API (SecKeychain, SecKeychainItem)
- **Darwin**: System metrics (memory pressure, process monitoring)

### No External Dependencies (Vendored)

- **CostUsage** (vendored copy): Local cost calculation for Codex/Claude logs
- Some helper protocols/utilities are locally defined (BoundedTaskJoin, AutoreleasePoolCompat)

---

## Framework & Patterns

### SwiftUI + Observation (Not Combine)

- `@Observable` for state (UsageStore, SettingsStore)
- No @Published, no .onReceive
- Automatic tracking of property accesses
- Clean, compiler-guaranteed memory model

### Actor-Based Concurrency

- Fetchers are value types with `@Sendable` closures
- UsageStore operations must go through @MainActor methods
- Background fetch tasks explicitly hop to main thread for state updates

### Type Safety

- Enums for provider IDs (UsageProvider, IconStyle)
- Strongly typed config (CodexBarConfig struct)
- No stringly-typed magic strings in UI code

### Separation of Concerns

1. **Core** (CodexBarCore): fetch, parse, cache logic — testable, no UI dependencies
2. **App** (CodexBar): state management, UI, user interaction
3. **CLI** (CodexBarCLI): command-line interface to Core
4. **Widget** (CodexBarWidget): read-only view of shared snapshot
5. **Helpers** (Watchdog, WebProbe): isolated utilities for special tasks

---

## Testing Strategy

### Test Targets

| Target | Location | Coverage |
|---|---|---|
| **CodexBarLinuxTests** | TestsLinux/ | ~40 tests (Swift Testing framework) |
| **CodexBarTests** | Tests/ | macOS-only tests (fixtures, mocks) |

### Test Fixtures

- `Tests/CodexBarTests/Fixtures/`: example provider responses (JSON, JSONL, CLI output)
- Parser tests: round-trip Codable, edge cases (malformed JSON, missing fields)
- Fetch tests: mock HTTPClient, verify fallback logic
- Widget snapshot tests: verify app group communication

---

## Performance Considerations

### Icon Rendering

- Rendered on demand, cached with size fingerprint
- Batches multiple icon updates into single NSStatusItem.button.image assignment
- Avoids re-rendering on every pixel change of meter

### Menu Card Recycling

- StatusItemController reuses NSMenuItem objects across menu rebuilds
- Identifies stable providers (not being toggled on/off) and preserves NSView references
- Improves popover responsiveness under rapid refresh cycles

### Fetch Parallelism

- Up to 8 concurrent provider fetches (BoundedTaskJoin)
- Timeout per fetch is strict (12-60s) to avoid cascade delays
- Failed fetches don't block others

### Memory Pressure Relief

- Clears snapshot cache when Darwin reports .moderate or higher
- Limits WidgetSnapshot size (only includes visible providers)

---

## Configuration & Customization

### Config File Locations

Primary: `~/.config/codexbar/config.json`  
Legacy fallback: `~/.codexbar/config.json`

### Config Schema

```json
{
  "providers": {
    "claude": { "enabled": true, "apiKey": "...", "useWebCookies": false },
    "codex": { "enabled": true, "oauthToken": "..." },
    ...
  },
  "ui": {
    "displayMode": "perProvider|merged",
    "showLabels": true,
    "showBars": true,
    "resetTimeStyle": "countdown|absolute"
  },
  "refresh": {
    "cadenceSeconds": 300,
    "autoStartup": true
  }
}
```

### API Key Management

- Stored with restrictive permissions (0o600)
- Never logged
- Supports piping via stdin: `printf '%s' "$KEY" | codexbar config set-api-key --provider claude --stdin`
- Supports environment variable override (provider-specific: `CLAUDE_API_KEY`, etc.)

---

## Security & Privacy

### Threat Model

1. **Local attacker**: Can read config file (0o600 protects API keys from other users)
2. **Remote attacker**: Cannot intercept (URLSession uses TLS, cookies encrypted in Keychain)
3. **App sandbox**: Not sandboxed (menu bar apps rarely are); Full Disk Access required for browser cookies

### Protections

- Browser cookies: decrypted on-demand, never stored in memory longer than fetch
- OAuth tokens: cached in Keychain (protected by OS)
- API keys: stored in config with restrictive perms, optional Keychain cache
- No analytics, no remote telemetry

---

## Extension Points for Contributors

### Adding a New Provider

1. Create `Sources/CodexBarCore/Providers/{ProviderName}/` subdir
2. Implement `ProviderDescriptor` (metadata: display name, CLI name, auth method)
3. Implement `*UsageFetcher` + `*UsageSnapshot` (protocol-driven, multiple sources)
4. Implement `*CookieStore` or `*TokenStore` if applicable
5. Add descriptor to `ProviderDescriptorRegistry`
6. Add localized strings to `Localizable.xcstrings`
7. Add provider icon to `Resources/` (16x16 template, dark/light variants)
8. Write tests (parser edge cases, fallback ordering)

### Custom Provider Endpoint Override

Settings → Advanced → Provider Overrides:
```
{ "openai": { "endpoint": "https://custom-proxy.local" } }
```

Resolved at fetch time, validated before use.

---

## Deployment & Distribution

### macOS App

- Code-signed ad-hoc or with Apple developer certificate
- Distributed via GitHub Releases (.dmg), Homebrew cask, direct download
- Sparkle handles auto-updates (GitHub API polling)

### CLI

- Built as universal binary (arm64 + x86_64)
- Distributed via Homebrew (steipete/tap/codexbar), AUR, direct tarball download
- Installed to `/usr/local/bin/codexbar` or `/opt/homebrew/bin/codexbar`

### Localization

- 21-language support (English, Simplified/Traditional Chinese, French, German, Spanish, Japanese, Korean, etc.)
- Shared `.xcstrings` catalog (app + website use same strings)
- RTL support for Arabic, Hebrew

---

## File Paths & Directory Structure Summary

| Path | Purpose |
|---|---|
| `~/.config/codexbar/config.json` | User config (primary) |
| `~/.codexbar/config.json` | User config (legacy, fallback) |
| `~/.config/codexbar/` | App group container (widgets, logs) |
| `~/.codex/output.json` | Codex session logs (cost scanning) |
| `~/.claude/config.json` | Claude CLI config (auth discovery) |
| `~/.claude/` | Claude logs, sessions |
| Browser cookie files | Chrome/Safari/Brave/Edge data dirs (FDAccess required) |
| Keychain | OAuth tokens, browser decryption keys, Codex API keys |

---

## Related Documentation

- [docs/architecture.md](../../../docs/architecture.md) — Original brief version
- [docs/providers.md](../../../docs/providers.md) — Per-provider implementation details & auth flows
- [docs/refresh-loop.md](../../../docs/refresh-loop.md) — Detailed fetch scheduler behavior
- [docs/ui.md](../../../docs/ui.md) — Icon rendering, menu layout, accessibility
- [docs/DEVELOPMENT.md](../../../docs/DEVELOPMENT.md) — Build setup, dev loop, debugging
- [docs/cli.md](../../../docs/cli.md) — CLI reference

---

## Summary: Key Takeaways

1. **Modular provider system**: 58 providers as pluggable fetchers with fallback chains; one provider failure doesn't cascade
2. **Privacy-first**: Reuses existing auth (cookies, OAuth, CLI) rather than storing passwords
3. **Multi-platform**: Single Core library serving app, CLI, widget, and helper processes
4. **Swift 6 idioms**: Strict concurrency, Observation, actor-based async/await
5. **Robust fetch architecture**: Parallel fetches with timeout, automatic fallbacks, snapshot caching
6. **User-centric design**: Settings for every major behavior, extensive debug logging, transparent error reporting

The codebase prioritizes correctness (Swift 6 strict concurrency) and robustness (explicit error handling, fallback chains, memory pressure relief) over clever shortcuts.
