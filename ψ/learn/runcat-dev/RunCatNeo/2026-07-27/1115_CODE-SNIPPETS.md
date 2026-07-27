## RunCat Neo Custom Metrics - Complete Code Snippets and Integration Guide

Based on my exploration of the RunCatNeo codebase at `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/`, here are the essential code snippets and patterns for building custom metrics integrations:

---

### 1. Custom Metrics JSON Schema

**File**: `docs/CustomMetricsSchema.md`

The JSON file format that producers must write:

```json
{
  "title": "Claude Code",
  "symbol": "staroflife",
  "metricsBarValue": "5.4%",
  "metrics": [
    { "title": "Model",   "formattedValue": "Opus 4.7" },
    { "title": "Context", "formattedValue": "5.4%",  "normalizedValue": 0.054 },
    { "title": "5h",      "formattedValue": "16.4%", "normalizedValue": 0.164 },
    { "title": "7d",      "formattedValue": "1.0%",  "normalizedValue": 0.01  }
  ],
  "lastUpdatedDate": "2026-06-05T04:50:40Z"
}
```

**Key Schema Rules**:
- `title` (required, string): Card header
- `symbol` (optional, string): SF Symbol identifier (defaults to `chart.bar.horizontal.page.fill`)
- `metricsBarValue` (optional, string): Short text for menu bar (shown verbatim)
- `metrics` (required, array): Rows with `title`, `formattedValue`, optional `normalizedValue` (0-1)
- `lastUpdatedDate` (required, ISO 8601): Timestamp of when file was written

**Critical constraints**:
- Write atomically: write to temp file, then `mv` into place (avoids partial reads)
- Keep file under 1MB
- Use strict JSON (no comments or trailing commas)
- No minimum update cadence - RunCat watches filesystem events

---

### 2. How RunCat Reads and Watches JSON Files

**File**: `LocalPackage/Sources/Model/Services/CustomMetricsService.swift` (key excerpt)

RunCat uses `DispatchSource` file-system event watching with automatic bookmark management:

```swift
private func makeObserver(for source: CustomMetricsSource) -> Task<Void, Never> {
    Task {
        var currentBookmark = source.bookmark
        while !Task.isCancelled {
            do {
                // Create URL from security-scoped bookmark
                let (isStale, url) = try urlClient.create(currentBookmark, .withSecurityScope)
                if isStale, let refreshed = try? urlClient.bookmarkData(url, .withSecurityScope) {
                    currentBookmark = refreshed
                    persistRefreshedBookmark(refreshed, for: source.id)
                }
                
                guard urlClient.startAccessingSecurityScopedResource(url) else {
                    emitFailure(for: source)
                    try await Task.sleep(for: .seconds(5))  // Retry every 5s if file unreadable
                    continue
                }
                defer {
                    urlClient.stopAccessingSecurityScopedResource(url)
                }
                
                // Load initial snapshot
                loadSnapshot(from: url, for: source)
                
                // Watch for filesystem changes (.write, .rename, .delete, .extend events)
                let watchStream = fileWatcherClient.watch(url)
                for await _ in watchStream {
                    if Task.isCancelled { break }
                    loadSnapshot(from: url, for: source)
                }
                try? await Task.sleep(for: .milliseconds(200))
            } catch is CancellationError {
                return
            } catch {
                emitFailure(for: source)
                try? await Task.sleep(for: .seconds(5))
            }
        }
    }
}

private func loadSnapshot(from url: URL, for source: CustomMetricsSource) {
    do {
        let data = try dataClient.read(url)
        let snapshot = try snapshotDecoder.decode(CustomMetricsSnapshot.self, from: data)
        emitSuccess(snapshot: snapshot, for: source)
    } catch {
        emitFailure(for: source)
    }
}
```

**File Watcher Implementation**: `LocalPackage/Sources/DataSource/Dependencies/FileWatcherClient.swift`

```swift
public struct FileWatcherClient: DependencyClient {
    public var watch: @Sendable (URL) -> AsyncStream<Date>

    public static let liveValue = Self(
        watch: { url in
            AsyncStream<Date>(bufferingPolicy: .bufferingNewest(1)) { continuation in
                let descriptor = open(url.path, O_EVTONLY)
                guard descriptor >= 0 else {
                    continuation.finish()
                    return
                }
                let source = DispatchSource.makeFileSystemObjectSource(
                    fileDescriptor: descriptor,
                    eventMask: [.write, .rename, .delete, .extend],
                    queue: DispatchQueue.global(qos: .utility)
                )
                source.setEventHandler {
                    let data = source.data
                    continuation.yield(Date())
                    if data.contains(.rename) || data.contains(.delete) {
                        continuation.finish()  // Stop watching if file deleted/renamed
                    }
                }
                source.setCancelHandler {
                    close(descriptor)
                }
                source.resume()
                continuation.onTermination = { _ in
                    source.cancel()
                }
            }
        }
    )
}
```

**Key behaviors**:
- Watches only the newest pending event (burst writes → single re-read)
- Retries every 5 seconds if file becomes unreadable
- Automatically recovers when file is readable again
- Uses security-scoped bookmarks to survive sandbox restarts

---

### 3. Swift Data Models

**File**: `LocalPackage/Sources/DataSource/Entities/CustomMetrics/CustomMetric.swift`

```swift
public struct CustomMetric: Codable, Sendable, Equatable {
    public var title: String
    public var formattedValue: String
    public var normalizedValue: Double?

    public init(title: String, formattedValue: String, normalizedValue: Double? = nil) {
        self.title = title
        self.formattedValue = formattedValue
        self.normalizedValue = normalizedValue
    }
}
```

**File**: `LocalPackage/Sources/DataSource/Entities/CustomMetrics/CustomMetricsSnapshot.swift`

```swift
public struct CustomMetricsSnapshot: Codable, Sendable, Equatable {
    public var title: String
    public var symbol: String?
    public var metricsBarValue: String?
    public var metrics: [CustomMetric]
    public var lastUpdatedDate: Date

    public init(
        title: String,
        symbol: String? = nil,
        metricsBarValue: String? = nil,
        metrics: [CustomMetric] = [],
        lastUpdatedDate: Date
    ) {
        self.title = title
        self.symbol = symbol
        self.metricsBarValue = metricsBarValue
        self.metrics = metrics
        self.lastUpdatedDate = lastUpdatedDate
    }
}
```

The decoder uses ISO 8601 date strategy:
```swift
private var snapshotDecoder: JSONDecoder = {
    let decoder = JSONDecoder()
    decoder.dateDecodingStrategy = .iso8601
    return decoder
}()
```

---

### 4. Claude Code Integration Sample

**File**: `docs/samples/claude-code/runcat-statusline.py`

Full working example that writes to `~/.claude/runcat-usage.json`:

```python
#!/usr/bin/env python3
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(os.environ.get("RUNCAT_OUT_FILE", str(Path.home() / ".claude" / "runcat-usage.json")))

def pct(title, value):
    if value is None:
        return None
    return {
        "title": title,
        "formattedValue": f"{value:g}%",
        "normalizedValue": round(value / 100, 4)
    }

try:
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        payload = {}
except Exception:
    payload = {}

model = (payload.get("model") or {}).get("display_name") or "Claude Code"
ctx = (payload.get("context_window") or {}).get("used_percentage")
rate_limits = payload.get("rate_limits") or {}
five = (rate_limits.get("five_hour") or {}).get("used_percentage")
seven = (rate_limits.get("seven_day") or {}).get("used_percentage")

snapshot = {
    "title": "Claude Code",
    "symbol": "staroflife",
    "metrics": [m for m in [
        {"title": "Model", "formattedValue": model},
        pct("Context", ctx),
        pct("5h", five),
        pct("7d", seven),
    ] if m is not None],
    "lastUpdatedDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
if ctx is not None:
    snapshot["metricsBarValue"] = f"{ctx:g}%"

# Atomic write
OUT.parent.mkdir(parents=True, exist_ok=True)
fd, tmp = tempfile.mkstemp(prefix=".runcat-", dir=str(OUT.parent))
with os.fdopen(fd, "w", encoding="utf-8") as f:
    json.dump(snapshot, f, ensure_ascii=False)
os.replace(tmp, OUT)

print(model)
```

**Setup in `~/.claude/settings.json`**:
```json
{
  "statusLine": {
    "type": "command",
    "command": "/Users/YOU/.claude/runcat-statusline.py"
  }
}
```

**Key pattern**: Reads JSON from stdin (Claude Code passes payload), writes snapshot atomically using temp file + `os.replace()`.

---

### 5. Codex Integration Sample

**File**: `docs/samples/codex/runcat-hook.py` (excerpt)

Triggered via lifecycle hooks, parses session transcript for token counts:

```python
#!/usr/bin/env python3
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(os.environ.get("RUNCAT_OUT_FILE", str(Path.home() / ".codex" / "runcat-usage.json")))

def percentage_metric(title, used_percentage):
    if not isinstance(used_percentage, (int, float)):
        return None
    clamped_percentage = max(0.0, min(float(used_percentage), 100.0))
    normalized_value = clamped_percentage / 100
    formatted_percentage = f"{clamped_percentage:.1f}".rstrip("0").rstrip(".")
    return {
        "title": title,
        "formattedValue": f"{formatted_percentage}%",
        "normalizedValue": round(normalized_value, 4),
    }

def window_title(window_minutes):
    if not isinstance(window_minutes, (int, float)):
        return None
    if window_minutes % 1440 == 0:
        return f"{window_minutes / 1440:g}d"
    if window_minutes % 60 == 0:
        return f"{window_minutes / 60:g}h"
    return f"{window_minutes:g}m"

def latest_token_count(transcript_path):
    if not transcript_path:
        return None
    latest = None
    try:
        with Path(transcript_path).open(encoding="utf-8") as transcript:
            for line in transcript:
                try:
                    event = json.loads(line)
                except (json.JSONDecodeError, TypeError):
                    continue
                payload = event.get("payload") or {}
                if payload.get("type") == "token_count":
                    latest = payload
    except OSError:
        return None
    return latest

def write_snapshot(hook_input):
    model = hook_input.get("model", "Codex").strip() or "Codex"
    token_count = latest_token_count(hook_input.get("transcript_path"))
    
    metrics = [{"title": "Model", "formattedValue": model}]
    # Add context and rate limit metrics...
    
    snapshot = {
        "title": "Codex",
        "symbol": "camera.aperture",
        "metrics": metrics,
        "lastUpdatedDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    
    # Atomic write with error handling
    OUT.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(prefix=".runcat-", dir=str(OUT.parent))
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as output:
            json.dump(snapshot, output, ensure_ascii=False)
        os.replace(temporary_path, OUT)
    except Exception:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise
```

**Setup in `~/.codex/hooks.json`**:
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/Users/YOU/.codex/runcat-hook.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

### 6. Bitcoin Price Sample (Scheduled via launchd)

**File**: `docs/samples/bitcoin/update-bitcoin.sh`

Shell script fetching from public API, scheduled with launchd:

```bash
#!/bin/sh
set -eu

outputFile="${RUNCAT_OUT_FILE:-$HOME/.runcat/bitcoin.json}"
apiURL="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

# Fetch price from CoinGecko
price=$(curl -fsS --max-time 15 "$apiURL" | sed -nE 's/.*"usd" *: *([0-9]+(\.[0-9]+)?).*/\1/p')
if [ -z "$price" ]; then
    echo "Failed to extract the Bitcoin price from the CoinGecko response" >&2
    exit 1
fi

# Format for menu bar and display
metricsBarValue=$(awk -v price="$price" 'BEGIN {
    if (price >= 1000000) printf "$%.2fM", price / 1000000
    else if (price >= 1000) printf "$%.1fK", price / 1000
    else printf "$%.2f", price
}')
currentValue=$(awk -v price="$price" 'BEGIN { printf "$%.2f", price }')
lastUpdatedDate=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Atomic write
outputDirectory=$(dirname "$outputFile")
mkdir -p "$outputDirectory"
temporaryFile=$(mktemp "$outputDirectory/.bitcoin-XXXXXX")
cat > "$temporaryFile" <<EOF
{
  "title": "Bitcoin",
  "symbol": "bitcoinsign",
  "metricsBarValue": "$metricsBarValue",
  "metrics": [
    { "title": "Current", "formattedValue": "$currentValue" }
  ],
  "lastUpdatedDate": "$lastUpdatedDate"
}
EOF
mv "$temporaryFile" "$outputFile"
```

**LaunchAgent Configuration**: `docs/samples/bitcoin/dev.runcat.bitcoin-sample.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.runcat.bitcoin-sample</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOU/.runcat/update-bitcoin.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

**Key pattern**: Write to temp file with `mktemp`, then `mv` into final location (atomic). LaunchAgent runs every 600 seconds (10 minutes). Load with `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/dev.runcat.bitcoin-sample.plist`.

---

### 7. Configuration & Settings Patterns

**Custom Metrics Configuration** (`CustomMetricsConfiguration.swift` implied):
- Sources stored in UserDefaults
- Each source has UUID, displayName, symbol, fileURL, security-scoped bookmark, createdAt
- Bookmarks survive sandbox restarts and file relocations

**Error Handling**:
- If file becomes unreadable or JSON invalid: card shows "Last updated: Failed" (red)
- Metrics Bar shows `---` instead of value
- Settings UI shows yellow `⚠︎ Error Detected` label
- Automatic recovery: just fix the producer, no manual reset needed

**Metrics Bar Display**:
- Each source hidden by default (toggle in Metrics Bar UI)
- `metricsBarValue` rendered verbatim in monospaced digit font
- Prefixed with source symbol

---

### 8. Key Takeaways for Custom Integrations

**Atomic Write Pattern** (all samples use this):
```python
# Python
fd, tmp = tempfile.mkstemp(prefix=".runcat-", dir=str(OUT.parent))
with os.fdopen(fd, "w", encoding="utf-8") as f:
    json.dump(snapshot, f)
os.replace(tmp, OUT)

# Shell
tmpfile=$(mktemp "$dir/.prefix-XXXXXX")
cat > "$tmpfile" << EOF
{...}
EOF
mv "$tmpfile" "$outfile"
```

**Timestamp Format**: Always ISO 8601 UTC
```python
datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

**Normalized Values**: Clamp to 0-1 for progress bars (RunCat clamps before drawing)

**Environment Variable Override**: All samples check `RUNCAT_OUT_FILE` for custom output path

**File Watching**: RunCat reacts to `.write`, `.rename`, `.delete`, `.extend` events via DispatchSource — no polling required

---

**Files referenced in this report**:
- `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/docs/CustomMetricsSchema.md`
- `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/LocalPackage/Sources/Model/Services/CustomMetricsService.swift`
- `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/LocalPackage/Sources/DataSource/Dependencies/FileWatcherClient.swift`
- `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/LocalPackage/Sources/DataSource/Entities/CustomMetrics/CustomMetric.swift`
- `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/LocalPackage/Sources/DataSource/Entities/CustomMetrics/CustomMetricsSnapshot.swift`
- `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/docs/samples/claude-code/runcat-statusline.py`
- `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/docs/samples/codex/runcat-hook.py`
- `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/docs/samples/bitcoin/update-bitcoin.sh`
- `/Users/switchaphon/ghq/github.com/runcat-dev/RunCatNeo/docs/samples/bitcoin/dev.runcat.bitcoin-sample.plist`
