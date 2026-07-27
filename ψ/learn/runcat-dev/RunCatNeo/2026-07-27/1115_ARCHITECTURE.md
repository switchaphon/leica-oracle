# RunCat Neo Architecture

## Project Overview

**RunCat Neo** is a modern macOS menu-bar application that animates a cute running cat in the status bar to reflect system load. The project demonstrates a comprehensive example of building a native macOS app with Swift 6 using the **LUCA architecture** pattern, emphasizing testability, clear separation of concerns, and external integration via a file-watching Custom Metrics system.

**Key Facts:**
- **Language:** Swift 6.2 (with `ExistentialAny` future feature enabled)
- **Platform:** macOS 26.3+ (built with Xcode 26.5+)
- **Architecture:** LUCA (strict layering: DataSource ← Model ← UserInterface)
- **Build System:** Xcode with embedded Swift Package Manager (SPM)
- **Available:** App Store

## Directory Structure

```
RunCatNeo/
├── RunCatNeo.xcodeproj/           # Xcode project shell (minimal config)
├── RunCatNeo/                     # App entry point
│   ├── RunCatNeoApp.swift         # @main App struct, wires scenes
│   └── AppIcon.icon/
├── LocalPackage/                  # All source code as SPM package
│   ├── Package.swift              # SPM manifest (three library targets)
│   ├── Sources/
│   │   ├── DataSource/            # Leaf layer: entities, dependencies, repositories
│   │   │   ├── DependencyClient.swift
│   │   │   ├── Dependencies/      # 13 dependency clients (thin, testable wrappers)
│   │   │   │   ├── FileWatcherClient.swift       # DispatchSource file monitoring
│   │   │   │   ├── AppStateClient.swift          # Global state via AllocatedUnfairLock
│   │   │   │   ├── DataClient.swift              # FileManager.contents(atPath:)
│   │   │   │   ├── URLClient.swift               # Bookmarks & security-scoped access
│   │   │   │   ├── UserDefaultsClient.swift      # Settings persistence
│   │   │   │   ├── DateClient.swift
│   │   │   │   ├── UUIDClient.swift
│   │   │   │   ├── NSAppClient.swift
│   │   │   │   ├── NSWorkspaceClient.swift       # App lifecycle, sleep/wake
│   │   │   │   ├── SystemInfoObserverClient.swift
│   │   │   │   ├── SMAppServiceClient.swift
│   │   │   │   ├── FileManagerClient.swift
│   │   │   │   └── LoggingSystemClient.swift
│   │   │   ├── Entities/
│   │   │   │   ├── AppState.swift                # Global state: async streams for metrics
│   │   │   │   ├── AsyncStreamBundle.swift       # Type wrapper for async streams
│   │   │   │   ├── CustomMetrics/
│   │   │   │   │   ├── CustomMetricsSnapshot.swift    # JSON-decoded file content
│   │   │   │   │   ├── CustomMetricsSource.swift      # File reference with bookmark
│   │   │   │   │   ├── CustomMetricsBundle.swift
│   │   │   │   │   ├── CustomMetric.swift
│   │   │   │   │   └── CustomMetricsConfiguration.swift
│   │   │   │   ├── Metrics/
│   │   │   │   │   ├── Metrics.swift
│   │   │   │   │   ├── RingBuffer.swift
│   │   │   │   │   ├── SystemMetricsConfiguration.swift
│   │   │   │   │   ├── MetricsBarConfiguration.swift
│   │   │   │   │   └── UpdateInterval.swift
│   │   │   │   ├── Runner/
│   │   │   │   ├── Events/
│   │   │   │   └── Error types (RCNError)
│   │   │   └── Repositories/
│   │   │       ├── UserDefaultsRepository.swift  # Repository pattern over client
│   │   │       ├── LaunchAtLoginRepository.swift
│   │   │       └── ApplicationSupportRepository.swift
│   │   ├── Model/                  # Business logic layer
│   │   │   ├── AppDelegate.swift   # App lifecycle, service initialization
│   │   │   ├── AppDependencies.swift     # Dependency injection container
│   │   │   ├── Composable.swift         # State management protocol
│   │   │   ├── Services/
│   │   │   │   ├── CustomMetricsService.swift   # File watching & reconciliation
│   │   │   │   ├── SystemMetricsService.swift   # CPU, memory collection
│   │   │   │   ├── RunnerService.swift          # Animation frame sequencing
│   │   │   │   └── LogService.swift
│   │   │   ├── Stores/
│   │   │   │   ├── Dashboard.swift
│   │   │   │   ├── RunnerBar.swift
│   │   │   │   ├── MetricsBar.swift
│   │   │   │   ├── CustomMetricsSettings.swift
│   │   │   │   ├── MetricsSettings.swift
│   │   │   │   ├── RunnerSettings.swift
│   │   │   │   ├── GeneralSettings.swift
│   │   │   │   ├── DonationSettings.swift
│   │   │   │   └── [other settings stores]
│   │   │   ├── Extensions/
│   │   │   └── [helper code]
│   │   └── UserInterface/           # SwiftUI layer (no logic)
│   │       ├── Scenes/
│   │       │   ├── RunnerBarScene.swift
│   │       │   ├── MetricsBarScene.swift
│   │       │   └── SettingsWindowScene.swift
│   │       ├── Views/
│   │       │   ├── RunnerBar/
│   │       │   │   └── Dashboard/     # Dashboard card view hierarchy
│   │       │   ├── MetricsBar/
│   │       │   ├── Settings/
│   │       │   └── [leaf views]
│   │       ├── Resources/
│   │       │   ├── Media.xcassets/
│   │       │   │   ├── Colors/
│   │       │   │   ├── Runners/         # Cat, Dog, Coffee, Mochi, etc. (keyframes)
│   │       │   │   └── Symbols/
│   │       │   └── Localization/
│   │       └── Extensions/
│   └── Tests/
│       ├── DataSourceTests/
│       └── ModelTests/
├── docs/
│   ├── CustomMetricsSchema.md       # JSON file format spec
│   ├── samples/
│   │   ├── claude-code/             # Claude Code statusLine integration
│   │   │   ├── README.md
│   │   │   └── runcat-statusline.py
│   │   ├── codex/                   # Codex lifecycle hook integration
│   │   │   ├── README.md
│   │   │   └── runcat-hook.py
│   │   └── bitcoin/                 # launchd shell script sample
│   │       ├── README.md
│   │       ├── update-bitcoin.sh
│   │       └── dev.runcat.bitcoin-sample.plist
│   ├── privacy_policy.md
│   └── [other docs]
├── ARCHITECTURE.md                  # LUCA architecture rules
├── CLAUDE.md                        # Claude Code guidance
├── CODING_STYLE.md                  # Line-level style conventions
├── CONTRIBUTING.md                  # PR/issue templates, localization policy
├── README.md
└── LICENSE (Apache 2.0)
```

## Entry Points

1. **App Launch:** `RunCatNeo/RunCatNeoApp.swift`
   - `@main` App struct
   - Instantiates `AppDelegate` via `@NSApplicationDelegateAdaptor`
   - Composes three SwiftUI `Scene`s: `RunnerBarScene`, `MetricsBarScene`, `SettingsWindowScene`

2. **App Lifecycle:** `LocalPackage/Sources/Model/AppDelegate.swift`
   - Called on `applicationDidFinishLaunching`
   - Initializes `AppDependencies.shared`
   - Creates and starts three services: `CustomMetricsService`, `SystemMetricsService`, `RunnerService`
   - Sets up task group to handle:
     - Sleep/wake notifications
     - System info updates
     - Graceful shutdown

## The Custom Metrics System

### How It Works

The Custom Metrics feature allows any external tool (Claude Code, Codex, scripts, etc.) to write a JSON file that RunCat watches and renders as a dashboard card. The system is **file-driven, not API-based**: RunCat never makes network calls; the producer is responsible for keeping the file up to date.

### Architecture Flow

```
External Tool (e.g. Claude Code)
    ↓ writes JSON atomically to disk
    ↓
~/.claude/runcat-usage.json (or user-selected path)
    ↓ FileWatcherClient monitors with DispatchSource
    ↓
CustomMetricsService.makeObserver() → async Task loop
    ↓ reads & decodes JSON
    ↓
CustomMetricsSnapshot entity
    ↓ emitted into AppState.metrics stream
    ↓
Dashboard store receives via `for await` loop
    ↓
SwiftUI Views render CustomMetricsBundle
```

### JSON Schema

**File Format:** Strict JSON (no comments, no trailing commas)

**Location:** User selects via picker in Settings → Metrics → Custom Metrics → "Add Custom Metrics Source"

**Write Pattern:** Write to temporary file in same directory, then `mv` (atomic) to final location. This prevents RunCat reading half-written content.

**Example JSON:**
```json
{
  "title": "Claude Code",
  "symbol": "staroflife",
  "metricsBarValue": "67%",
  "metrics": [
    { "title": "Model",   "formattedValue": "Opus 4.7" },
    { "title": "Context", "formattedValue": "67%",  "normalizedValue": 0.67 },
    { "title": "5h",      "formattedValue": "3%",   "normalizedValue": 0.03 },
    { "title": "7d",      "formattedValue": "3%",   "normalizedValue": 0.03 }
  ],
  "lastUpdatedDate": "2026-06-07T05:55:36Z"
}
```

**Schema Details:**

| Field             | Type              | Required | Description |
|-------------------|-------------------|----------|---|
| `title`           | string            | yes      | Card header |
| `symbol`          | SF Symbol name    | no       | Icon next to title; defaults to `chart.bar.horizontal.page.fill` |
| `metricsBarValue` | string            | no       | Short label in dedicated Metrics Bar (menu bar item); max width enforced |
| `metrics`         | array<Metric>     | yes      | Rows displayed; empty array allowed |
| `lastUpdatedDate` | ISO 8601 string   | yes      | Timestamp of last update; shown as relative time |

Each metric row:
- `title`: label
- `formattedValue`: display string (units, symbols, formatting applied by producer)
- `normalizedValue` (optional): value in [0, 1] for progress bar rendering

### CustomMetricsService Implementation

**File:** `LocalPackage/Sources/Model/Services/CustomMetricsService.swift`

**Key Methods:**

1. **`addSource(of:)`** — User adds a file
   - Validates file is readable
   - Decodes JSON to extract `title`, `symbol`
   - Creates security-scoped bookmark (survives sandbox restarts)
   - Persists `CustomMetricsSource` to UserDefaults

2. **`startMonitoring()`** — Called on app launch and wake-up
   - Calls `reconcile()` to diff desired vs. current observers
   - Sets up `customMetricsReconcileObserver` task
   - Listens to `customMetricsConfigurationChanges` stream
   - On change, adds/removes file watchers as needed

3. **`makeObserver(for:)`** — Creates long-lived async Task per source
   - Resolves bookmark → URL (handles stale bookmarks)
   - Calls `fileWatcherClient.watch(url)` → `AsyncStream<Date>` via `DispatchSource`
   - On each file-system event (.write, .rename, .extend, .delete):
     - Calls `loadSnapshot(from:for:)`
     - If file deleted (.rename or .delete event), stream terminates
   - On read errors: emits failure state, retries every 5 seconds
   - Loop cancels cleanly on task cancellation

4. **`loadSnapshot(from:for:)`** — Reads & decodes one file
   - Uses `DataClient.read(url)` → `Data`
   - Decodes with `JSONDecoder` (ISO 8601 date strategy)
   - Calls `emitSuccess()` or `emitFailure()`
   - Updates `AppState.metrics.customMetricsBundles` array

5. **`stopMonitoring()`** — Called on sleep or app termination
   - Cancels all file-watcher tasks
   - Clears `customMetricsBundles`

**Error Handling:**
- File unreadable (deleted, moved) → Card shows "Last updated: Failed" in red
- Invalid JSON → Card keeps previous snapshot, shows failed state
- Recovery is automatic: when file becomes readable, next read succeeds

### How FileWatcherClient Works

**File:** `LocalPackage/Sources/DataSource/Dependencies/FileWatcherClient.swift`

Wraps macOS `DispatchSource.makeFileSystemObjectSource`:
```swift
public var watch: @Sendable (URL) -> AsyncStream<Date>
```

- Opens file descriptor with `O_EVTONLY`
- Monitors events: `.write`, `.rename`, `.delete`, `.extend`
- Returns `AsyncStream<Date>` (buffers newest only) that yields on each event
- Stream finishes on `.rename` or `.delete`
- Handles descriptor cleanup via cancel handler

**Key feature:** Events collapse into a single re-read (bufferingNewest(1) policy). Rapid file writes don't queue; only the latest change matters.

### Security & Bookmarks

- **Sandboxing:** Files outside app bundle require user-granted access via file picker
- **Bookmarks:** `URLClient.bookmarkData(url, .withSecurityScope)` creates persistent bookmarks
- **Recovery:** On sandbox restarts, bookmark is resolved back to URL
- **Stale detection:** `URLClient.create(bookmark, .withSecurityScope)` returns `(isStale, URL)`; if stale, refreshed bookmark is re-persisted

## statusLine Integration with Claude Code

Claude Code's `statusLine` is a command that runs **after each turn** to update terminal status info. RunCat provides a Python sample that writes the Custom Metrics JSON.

### Setup Flow

1. **Copy Sample:**
   ```bash
   cp docs/samples/claude-code/runcat-statusline.py ~/.claude/
   chmod +x ~/.claude/runcat-statusline.py
   ```

2. **Register in `~/.claude/settings.json`:**
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "/Users/YOU/.claude/runcat-statusline.py"
     }
   }
   ```

3. **Configure in RunCat:**
   - Open RunCat Settings → Metrics → Custom Metrics
   - Click "Add Custom Metrics Source"
   - Select `~/.claude/runcat-usage.json`
   - Card appears on dashboard

### What the Script Does

**File:** `docs/samples/claude-code/runcat-statusline.py`

- Reads JSON from stdin (Claude Code's `statusLine` input)
- Extracts:
  - Model name (`model.display_name`)
  - Context window usage percentage
  - 5-hour rate limit usage
  - 7-day rate limit usage
- Writes snapshot JSON with `lastUpdatedDate` timestamp
- Writes atomically: temp file → `os.replace()`
- Prints model name to stdout (for terminal status line)

**Customization:**
- Modify `snapshot = {...}` dict to change card layout, title, symbol
- Override `RUNCAT_OUT_FILE` env var to change output path
- Merge with existing statusLine script by combining both into one

### Why File-Based?

- **No API dependency:** RunCat never needs to know Claude Code's format
- **Offline-friendly:** Works without network; producer drives cadence
- **Low coupling:** Claude Code, Codex, scripts, etc. all write the same JSON
- **Extensibility:** Users can build custom producers without rebuilding RunCat

## Plugin & Sample Architecture

### Sample Structure

Each sample in `docs/samples/` demonstrates integration with a different tool:

1. **Claude Code** (`claude-code/`)
   - Python script as statusLine hook
   - Reads Claude Code's runtime metrics (model, context, rate limits)
   - Writes model name to terminal status line

2. **Codex** (`codex/`)
   - Python hook for Codex lifecycle events
   - Similar schema to Claude Code sample
   - Triggered on Codex start/stop

3. **Bitcoin** (`bitcoin/`)
   - Shell script scheduled via launchd `.plist`
   - Fetches Bitcoin price from CoinGecko public API
   - Demonstrates external API integration

### Writing a Custom Integration

A producer must:
1. Write to a JSON file matching the schema
2. Include `lastUpdatedDate` (ISO 8601)
3. Write atomically (temp file + rename)
4. Encode formatting + units in `formattedValue` (RunCat renders verbatim)
5. Optionally provide `normalizedValue` in [0, 1] for progress bars

No RunCat rebuild needed; user just adds the file path in settings.

## Dependencies & Build System

### Swift Package Manifest

**File:** `LocalPackage/Package.swift`

```swift
// Swift 6.2, macOS 26+
platforms: [.macOS(.v26)]
swiftSettings: [.enableUpcomingFeature("ExistentialAny")]

// Three library targets with one-way layering
products: [
  .library(name: "DataSource", targets: ["DataSource"]),
  .library(name: "Model", targets: ["Model"]),
  .library(name: "UserInterface", targets: ["UserInterface"]),
]

// Runtime dependencies
dependencies: [
  .package(url: "https://github.com/apple/swift-async-algorithms.git", exact: "1.1.5"),
  .package(url: "https://github.com/apple/swift-log.git", exact: "1.14.0"),
  .package(url: "https://github.com/cybozu/LicenseList.git", exact: "2.5.0"),
  .package(url: "https://github.com/Kyome22/AllocatedUnfairLock.git", exact: "1.0.0"),
  .package(url: "https://github.com/Kyome22/SystemInfoKit.git", exact: "7.2.0"),
]
```

### External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `swift-async-algorithms` | 1.1.5 | `AsyncAlgorithms.share()` for stream sharing |
| `swift-log` | 1.14.0 | Structured logging (Logging API) |
| `AllocatedUnfairLock` | 1.0.0 | Lock-based AppState synchronization |
| `SystemInfoKit` | 7.2.0 | CPU, memory, thermal info |
| `LicenseList` | 2.5.0 | Open-source license display |

### Build & Test

- **Build:** `xcodebuild build -scheme RunCatNeo -destination 'platform=macOS,arch=arm64'`
- **Test:** `xcodebuild test -scheme LocalPackage-Package -destination 'platform=macOS,arch=arm64'`
- **Tests:** Swift Testing (`@Test`, `#expect`); live in `DataSourceTests/`, `ModelTests/`
- **No UI tests, no linter configured**

### Deployment

- **Distribution:** App Store (macOS 26+)
- **CI:** GitHub Actions on tag pushes only (`.github/workflows/test.yml`)
- **Versioning:** `Bundle.bundleVersion` (set in Xcode build settings)

## Notable Patterns

### 1. LUCA Architecture

**Three-layer dependency structure with strict rules:**

```
UserInterface  →  Model  →  DataSource
(imports)        (imports)  (imports nothing)
```

**Responsibilities:**
- **DataSource (leaf):** Entities, Dependencies (thin wrappers), Repositories (compositions)
- **Model (middle):** Services (long-lived workers), Stores (view-models), AppDependencies
- **UserInterface (top):** SwiftUI Scenes, Views, Assets; zero logic

**Benefit:** DataSource and Model are fully testable without asset bundles or SwiftUI.

### 2. DependencyClient Protocol

**Design:**
```swift
public protocol DependencyClient: Sendable {
    static var liveValue: Self { get }
    static var testValue: Self { get }
}
```

**Pattern:**
- Each system API (UserDefaults, FileManager, NSWorkspace, FileWatcher) gets a `DependencyClient`
- `liveValue` wraps the real API
- `testValue` provides a no-op or stub implementation
- Clients are **never tested themselves**; they're untested boundaries

**Rule:** DependencyClient methods must be **one direct call** to the underlying API. Logic belongs in `Service` or `Store`, which are tested.

### 3. Composable & Store Pattern

**Protocol:**
```swift
@MainActor
public protocol Composable: AnyObject {
    associatedtype Action: Sendable
    var action: (Action) async -> Void { get }
    func reduce(_ action: Action) async
}
```

**Pattern:**
- Each Store (view-model) conforms to `Composable`
- Marked `@MainActor @Observable` for SwiftUI integration
- Views call `store.send(Action)` to mutate state
- `reduce()` implements action-to-state transitions (pure, testable)
- `action` closure forwards to parent (for cross-screen communication)

**Example:**
```swift
@MainActor @Observable
final class Dashboard: Composable {
    enum Action { case task(String), settingsButtonTapped, ... }
    var action: (Action) async -> Void
    
    func reduce(_ action: Action) async {
        switch action {
        case .settingsButtonTapped:
            nsAppClient.activate(true)
        ...
        }
    }
}
```

### 4. AppState & AsyncStreamBundle

**Global state holder:**
```swift
public struct AppState: Sendable {
    public var metrics = AsyncStreamBundle<Metrics>()
    public var customMetricsObservers = [UUID: Task<Void, Never>]()
    ...
}
```

**AsyncStreamBundle wrapper:**
```swift
public struct AsyncStreamBundle<T>: Sendable {
    public let stream: any AsyncShareStream<T>
    public private(set) var latestValue: T?
    
    public mutating func send(_ value: T) {
        latestValue = value
        continuation.yield(value)
    }
}
```

**Usage:**
- Services emit into streams (`.send(value)`)
- Stores subscribe via `for await value in stream { ... }`
- Always have latest snapshot via `.latestValue`
- Shared across multiple subscribers

### 5. Repository Pattern

Repositories compose dependency clients into higher-level queries:

```swift
public struct UserDefaultsRepository: Sendable {
    private var userDefaultsClient: UserDefaultsClient
    
    public var customMetricsConfiguration: CustomMetricsConfiguration {
        get {
            guard let data = userDefaultsClient.data(.customMetricsConfiguration),
                  let value = try? JSONDecoder().decode(...) else { return .empty }
            return value
        }
        nonmutating set { /* encode & persist */ }
    }
}
```

**Benefit:** One-liner getters/setters hide JSON codec and default logic.

### 6. Sendable Everywhere

All entities, dependencies, and closures conform to `Sendable`. Combined with `@MainActor` on Stores and SwiftUI views, this gives compiler-verified thread safety without runtime locks (except `AllocatedUnfairLock` for AppState access).

### 7. File Watching via DispatchSource

CustomMetrics avoids polling. Instead:
- Each monitored file gets a `DispatchSource.makeFileSystemObjectSource`
- Events (.write, .rename, .delete, .extend) trigger async stream yields
- `FileWatcherClient.watch()` returns `AsyncStream<Date>` for async/await integration
- Memory cleanup via `setCancelHandler`

### 8. Atomic File Writes

Producer guideline: never write directly to the target path. Instead:
```bash
temp=$(mktemp -p "$(dirname "$TARGET")")
# write to $temp
mv "$temp" "$TARGET"  # atomic rename
```

Prevents RunCat reading half-written content.

### 9. Security-Scoped Bookmarks

Files outside the app bundle require persistent access. The app:
1. User picks file via NSSavePanel/NSOpenPanel
2. App calls `URLClient.bookmarkData(url, .withSecurityScope)`
3. Bookmark is persisted to UserDefaults
4. On resume, bookmark resolves to URL; stale bookmarks are refreshed

Survives app restart and sandbox restrictions.

### 10. No Resource References in Model Layer

**Rule:** Model cannot import `UserInterface` or reference `Asset Catalog` / `String Catalog`.

**Pattern:** Views map semantic constants to resources:
```swift
// Model: pure enum
enum Something { case mode1, mode2 }

// View: maps to resource
let image = Image(something == .mode1 ? "icon-mode1" : "icon-mode2")
```

This keeps Model testable without asset bundles.

## Testing Strategy

**Test Targets:**
- `DataSourceTests/` — Entity + Dependency tests (mock out clients)
- `ModelTests/` — Service + Store tests (use AppDependencies.testDependencies(...))

**Example:** Override a dependency for a test:
```swift
let deps = AppDependencies.testDependencies(
    userDefaultsClient: .testValue  // stub UserDefaults
)
let service = CustomMetricsService(deps)
// test service.addSource(...), service.startMonitoring(), etc.
```

**No UI tests; no linter configured** (contributors rely on code review).

## Git & Contribution Workflow

**Repository Structure:**
- One PR per concern
- PR/issue templates in `.github/`
- `CONTRIBUTING.md` defines process
- Localization follows string catalog pattern
- Feature requests evaluated on cost/benefit

**Key Docs:**
- `CLAUDE.md` — Guidance for Claude Code users
- `ARCHITECTURE.md` — Layer rules, design patterns
- `CODING_STYLE.md` — Line-level conventions (naming, comments, formatting)
- `CONTRIBUTING.md` — PR workflow, templates, localization policy

---

## Summary

RunCat Neo is a textbook example of **layered architecture with external integration**. The Custom Metrics system exemplifies a **file-driven, decoupled design** where external tools (Claude Code, Codex, scripts) write JSON without any API dependency. The LUCA layering ensures testability and clear separation: DataSource provides thin wrappers and entities, Model contains logic in Services and Stores, UserInterface is a pure rendering layer. File watching is implemented with zero polling via DispatchSource, and global state flows through AsyncStreamBundle, enabling reactive updates across the app. Security-scoped bookmarks handle sandboxing gracefully, and atomic file writes prevent corruption.

This architecture scales from a simple menu-bar app to a complex dashboard with multiple integrations—all without tight coupling to any external tool.
