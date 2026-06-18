# CodexBar - Code Snippets & Patterns

**Explored**: `/Users/switchaphon/ghq/github.com/steipete/codexbar`  
**Date**: 2026-06-16  
**Focus**: Core architecture, API patterns, error handling, data models, auth/networking

---

## 1. Main Entry Point & App Initialization

### CodexBarApp (@main)

**File**: `Sources/CodexBar/CodexbarApp.swift`

Bootstraps the macOS menu bar app with dependency injection, logging, and platform-specific updater setup.

```swift
@main
struct CodexBarApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @State private var settings: SettingsStore
    @State private var store: UsageStore
    @State private var managedCodexAccountCoordinator: ManagedCodexAccountCoordinator
    @State private var codexAccountPromotionCoordinator: CodexAccountPromotionCoordinator

    init() {
        let env = ProcessInfo.processInfo.environment
        let storedLevel = CodexBarLog.parseLevel(UserDefaults.standard.string(forKey: "debugLogLevel")) ?? .verbose
        let level = CodexBarLog.parseLevel(env["CODEXBAR_LOG_LEVEL"]) ?? storedLevel
        CodexBarLog.bootstrapIfNeeded(.init(
            destination: .oslog(subsystem: "com.steipete.codexbar"),
            level: level,
            json: false))

        // Version/build info logging
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unknown"
        let build = Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "unknown"
        let gitCommit = Bundle.main.object(forInfoDictionaryKey: "CodexGitCommit") as? String ?? "unknown"
        CodexBarLog.logger(LogCategories.app).info(
            "CodexBar starting",
            metadata: [
                "version": version,
                "build": build,
                "git": gitCommit,
            ])

        // Core dependency setup
        let settings = SettingsStore()
        let managedCodexAccountCoordinator = ManagedCodexAccountCoordinator()
        let fetcher = UsageFetcher()
        let browserDetection = BrowserDetection(cacheTTL: BrowserDetection.defaultCacheTTL)
        let account = fetcher.loadAccountInfo()
        let store = UsageStore(fetcher: fetcher, browserDetection: browserDetection, settings: settings)

        self._settings = State(wrappedValue: settings)
        self._store = State(wrappedValue: store)
        // ... more initialization
    }

    @SceneBuilder
    var body: some Scene {
        // Hidden window to keep SwiftUI lifecycle alive for Settings toolbar
        WindowGroup("CodexBarLifecycleKeepalive") {
            HiddenWindowView()
        }
        .defaultSize(width: 20, height: 20)
        .windowStyle(.hiddenTitleBar)

        Settings {
            PreferencesView(
                settings: self.settings,
                store: self.store,
                // ...
            )
        }
    }
}
```

**Key Patterns**:
- Centralized logging via `CodexBarLog` with oslog subsystem
- Environment variable override for debug log level
- Dependency injection through `@State` properties
- Hidden SwiftUI window to maintain framework lifecycle while AppKit-based UI

---

## 2. Core Data Models: RateWindow & UsageSnapshot

**File**: `Sources/CodexBarCore/UsageFetcher.swift`

Data structures for representing provider quotas, rate limits, and usage state.

```swift
public struct RateWindow: Codable, Equatable, Sendable {
    public let usedPercent: Double
    public let windowMinutes: Int?
    public let resetsAt: Date?
    public let resetDescription: String?
    public let nextRegenPercent: Double?

    public var remainingPercent: Double {
        max(0, 100 - self.usedPercent)
    }

    // Backfill missing reset time from cached snapshot if current fetch didn't provide it
    public func backfillingResetTime(from cached: RateWindow?, now: Date = .init()) -> RateWindow {
        if self.resetsAt != nil { return self }
        guard let cachedReset = cached?.resetsAt, cachedReset > now else { return self }
        let windowMinutes = if let windowMinutes = self.windowMinutes, windowMinutes > 0 {
            windowMinutes
        } else {
            cached?.windowMinutes
        }
        return RateWindow(
            usedPercent: self.usedPercent,
            windowMinutes: windowMinutes,
            resetsAt: cachedReset,
            resetDescription: self.resetDescription ?? cached?.resetDescription,
            nextRegenPercent: self.nextRegenPercent)
    }
}

public struct NamedRateWindow: Codable, Equatable, Sendable {
    public let id: String
    public let title: String
    public let window: RateWindow
    /// Whether `window.usedPercent` reflects known quota usage (false = has reset metadata but no confirmed usage)
    public let usageKnown: Bool

    private enum CodingKeys: String, CodingKey {
        case id, title, window, usageKnown
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.id = try container.decode(String.self, forKey: .id)
        self.title = try container.decode(String.self, forKey: .title)
        self.window = try container.decode(RateWindow.self, forKey: .window)
        // Backcompat: missing usageKnown defaults to true for older cached payloads
        self.usageKnown = try container.decodeIfPresent(Bool.self, forKey: .usageKnown) ?? true
    }
}

public struct UsageSnapshot: Codable, Sendable {
    public let primary: RateWindow?
    public let secondary: RateWindow?
    public let tertiary: RateWindow?
    public let extraRateWindows: [NamedRateWindow]?
    public let providerCost: ProviderCostSnapshot?
    public let kiroUsage: KiroUsageDetails?
    public let ampUsage: AmpUsageDetails?
    public let zaiUsage: ZaiUsageSnapshot?
    public let minimaxUsage: MiniMaxUsageSnapshot?
    public let deepseekUsage: DeepSeekUsageSummary?
    public let mimoUsage: MiMoUsageSnapshot?
    public let openRouterUsage: OpenRouterUsageSnapshot?
    public let openAIAPIUsage: OpenAIAPIUsageSnapshot?
    public let claudeAdminAPIUsage: ClaudeAdminAPIUsageSnapshot?
    public let mistralUsage: MistralUsageSnapshot?
    public let deepgramUsage: DeepgramUsageSnapshot?
    public let poeUsage: PoeUsageHistorySnapshot?
    public let cursorRequests: CursorRequestUsage?
    public let subscriptionExpiresAt: Date?
    public let subscriptionRenewsAt: Date?
    public let updatedAt: Date
    public let identity: ProviderIdentitySnapshot?

    // ... custom Codable to handle backcompat migrations
}
```

**Key Patterns**:
- Extensible snapshot model to accommodate 50+ provider-specific data
- `usageKnown` flag to distinguish reset metadata from actual usage (important for UI)
- `backfillingResetTime()` recovers reset times from cache when API doesn't provide them
- Sendable conformance for thread-safe state storage
- Custom Codable for migration/backcompat

---

## 3. OAuth Credentials: Parsing & Storage

**File**: `Sources/CodexBarCore/Providers/Codex/CodexOAuth/CodexOAuthCredentials.swift`

Shows how OAuth tokens are loaded from user home, parsed, and refreshed.

```swift
public struct CodexOAuthCredentials: Sendable {
    public let accessToken: String
    public let refreshToken: String
    public let idToken: String?
    public let accountId: String?
    public let lastRefresh: Date?

    public var needsRefresh: Bool {
        guard let lastRefresh else { return true }
        let eightDays: TimeInterval = 8 * 24 * 60 * 60
        return Date().timeIntervalSince(lastRefresh) > eightDays
    }
}

public enum CodexOAuthCredentialsError: LocalizedError, Sendable {
    case notFound
    case decodeFailed(String)
    case missingTokens

    public var errorDescription: String? {
        switch self {
        case .notFound:
            "Codex auth.json not found. Run `codex` to log in."
        case let .decodeFailed(message):
            "Failed to decode Codex credentials: \(message)"
        case .missingTokens:
            "Codex auth.json exists but contains no tokens."
        }
    }
}

public enum CodexOAuthCredentialsStore {
    private static func authFilePath(
        env: [String: String] = ProcessInfo.processInfo.environment,
        fileManager: FileManager = .default) -> URL
    {
        CodexHomeScope
            .ambientHomeURL(env: env, fileManager: fileManager)
            .appendingPathComponent("auth.json")
    }

    public static func load(env: [String: String] = ProcessInfo.processInfo.environment) throws -> CodexOAuthCredentials {
        let url = self.authFilePath(env: env)
        guard FileManager.default.fileExists(atPath: url.path) else {
            throw CodexOAuthCredentialsError.notFound
        }

        let data = try Data(contentsOf: url)
        return try self.parse(data: data)
    }

    public static func parse(data: Data) throws -> CodexOAuthCredentials {
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw CodexOAuthCredentialsError.decodeFailed("Invalid JSON")
        }

        // Support legacy OPENAI_API_KEY format
        if let apiKey = json["OPENAI_API_KEY"] as? String,
           !apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        {
            return CodexOAuthCredentials(
                accessToken: apiKey,
                refreshToken: "",
                idToken: nil,
                accountId: nil,
                lastRefresh: nil)
        }

        // Parse tokens with snake_case/camelCase flexibility
        guard let tokens = json["tokens"] as? [String: Any] else {
            throw CodexOAuthCredentialsError.missingTokens
        }
        guard let accessToken = Self.stringValue(in: tokens, snakeCaseKey: "access_token", camelCaseKey: "accessToken"),
              let refreshToken = Self.stringValue(in: tokens, snakeCaseKey: "refresh_token", camelCaseKey: "refreshToken"),
              !accessToken.isEmpty
        else {
            throw CodexOAuthCredentialsError.missingTokens
        }

        return CodexOAuthCredentials(
            accessToken: accessToken,
            refreshToken: refreshToken,
            idToken: Self.stringValue(in: tokens, snakeCaseKey: "id_token", camelCaseKey: "idToken"),
            accountId: Self.stringValue(in: tokens, snakeCaseKey: "account_id", camelCaseKey: "accountId"),
            lastRefresh: Self.parseLastRefresh(from: json["last_refresh"]))
    }

    public static func save(
        _ credentials: CodexOAuthCredentials,
        env: [String: String] = ProcessInfo.processInfo.environment) throws
    {
        let url = self.authFilePath(env: env)

        // Preserve existing config structure, merge tokens in
        var json: [String: Any] = [:]
        if let data = try? Data(contentsOf: url),
           let existing = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        {
            json = existing
        }

        var tokens: [String: Any] = [
            "access_token": credentials.accessToken,
            "refresh_token": credentials.refreshToken,
        ]
        if let idToken = credentials.idToken {
            tokens["id_token"] = idToken
        }
        if let accountId = credentials.accountId {
            tokens["account_id"] = accountId
        }

        json["tokens"] = tokens
        json["last_refresh"] = ISO8601DateFormatter().string(from: Date())

        let data = try JSONSerialization.data(withJSONObject: json, options: [.prettyPrinted, .sortedKeys])
        let directory = url.deletingLastPathComponent()
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        try data.write(to: url, options: .atomic)
    }

    private static func parseLastRefresh(from raw: Any?) -> Date? {
        guard let value = raw as? String, !value.isEmpty else { return nil }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: value) { return date }
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: value)
    }

    private static func stringValue(
        in dictionary: [String: Any],
        snakeCaseKey: String,
        camelCaseKey: String) -> String?
    {
        if let value = dictionary[snakeCaseKey] as? String, !value.isEmpty {
            return value
        }
        if let value = dictionary[camelCaseKey] as? String, !value.isEmpty {
            return value
        }
        return nil
    }
}
```

**Key Patterns**:
- Safe file I/O with atomic writes
- Flexible JSON parsing (snake_case + camelCase variants)
- Legacy format support (direct API key fallback)
- Environment-aware path resolution
- Token refresh tracking with 8-day threshold
- Comprehensive error types that guide users to action

---

## 4. API Fetcher: Request/Response Flow

**File**: `Sources/CodexBarCore/Providers/Kimi/KimiUsageFetcher.swift`

Real-world example of multi-auth provider (JWT token + API key) with error handling and status code mapping.

```swift
public struct KimiUsageFetcher: Sendable {
    private static let log = CodexBarLog.logger(LogCategories.kimiAPI)
    private static let usageURL =
        URL(string: "https://www.kimi.com/apiv2/kimi.gateway.billing.v1.BillingService/GetUsages")!

    // Code API path (newer, OpenAI-compatible)
    public static func fetchCodeAPIUsage(
        apiKey: String,
        baseURL: URL = KimiSettingsReader.defaultCodeAPIBaseURL,
        now: Date = Date()) async throws -> KimiUsageSnapshot
    {
        guard !apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw KimiAPIError.missingAPIKey
        }

        guard let validatedBaseURL = ProviderEndpointOverrideValidator().validatedURL(baseURL.absoluteString) else {
            throw KimiAPIError.invalidRequest("Kimi Code API base URL must use HTTPS without user info")
        }

        let endpoint = self.codeAPIUsageEndpoint(baseURL: validatedBaseURL)
        var request = URLRequest(url: endpoint)
        request.httpMethod = "GET"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let response = try await ProviderHTTPClient.shared.response(for: request)
        let data = response.data
        guard response.statusCode == 200 else {
            let responseBody = String(data: data, encoding: .utf8) ?? "<binary data>"
            Self.log.error("Kimi Code API returned \(response.statusCode): \(responseBody)")
            throw self.codeAPIError(statusCode: response.statusCode)
        }

        return try self.parseCodeAPIUsage(from: data, now: now)
    }

    // JWT-based auth (original Kimi endpoint)
    public static func fetchUsage(authToken: String, now: Date = Date()) async throws -> KimiUsageSnapshot {
        // Extract session metadata from JWT payload
        let sessionInfo = self.decodeSessionInfo(from: authToken)

        var request = URLRequest(url: self.usageURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        request.setValue("kimi-auth=\(authToken)", forHTTPHeaderField: "Cookie")
        request.setValue("https://www.kimi.com", forHTTPHeaderField: "Origin")
        request.setValue("https://www.kimi.com/code/console", forHTTPHeaderField: "Referer")

        // Include session-specific headers decoded from JWT
        if let sessionInfo {
            if let deviceId = sessionInfo.deviceId {
                request.setValue(deviceId, forHTTPHeaderField: "x-msh-device-id")
            }
            if let sessionId = sessionInfo.sessionId {
                request.setValue(sessionId, forHTTPHeaderField: "x-msh-session-id")
            }
            if let trafficId = sessionInfo.trafficId {
                request.setValue(trafficId, forHTTPHeaderField: "x-traffic-id")
            }
        }

        let requestBody = ["scope": ["FEATURE_CODING"]]
        request.httpBody = try? JSONSerialization.data(withJSONObject: requestBody)

        let response = try await ProviderHTTPClient.shared.response(for: request)
        let data = response.data
        guard response.statusCode == 200 else {
            let responseBody = String(data: data, encoding: .utf8) ?? "<binary data>"
            Self.log.error("Kimi API returned \(response.statusCode): \(responseBody)")

            if response.statusCode == 401 || response.statusCode == 403 {
                throw KimiAPIError.invalidToken
            }
            if response.statusCode == 400 {
                throw KimiAPIError.invalidRequest("Bad request")
            }
            throw KimiAPIError.apiError("HTTP \(response.statusCode)")
        }

        let usageResponse = try JSONDecoder().decode(KimiUsageResponse.self, from: data)
        guard let codingUsage = usageResponse.usages.first(where: { $0.scope == "FEATURE_CODING" }) else {
            throw KimiAPIError.parseFailed("FEATURE_CODING scope not found in response")
        }

        return KimiUsageSnapshot(
            weekly: codingUsage.detail,
            rateLimit: codingUsage.limits?.first?.detail,
            updatedAt: now)
    }

    // JWT payload parsing (minimal; only need session metadata)
    private static func decodeSessionInfo(from jwt: String) -> SessionInfo? {
        let parts = jwt.split(separator: ".", maxSplits: 2)
        guard parts.count == 3 else { return nil }

        // Convert base64url (JWT) to standard base64
        var payload = String(parts[1])
            .replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")
        // Add padding if needed
        while payload.count % 4 != 0 {
            payload += "="
        }

        guard let payloadData = Data(base64Encoded: payload),
              let json = try? JSONSerialization.jsonObject(with: payloadData) as? [String: Any]
        else {
            return nil
        }

        return SessionInfo(
            deviceId: json["device_id"] as? String,
            sessionId: json["ssid"] as? String,
            trafficId: json["traffic_id"] as? String)
    }

    private static func codeAPIError(statusCode: Int) -> KimiAPIError {
        switch statusCode {
        case 400:
            .invalidRequest("Bad request")
        case 401:
            .invalidAPIKey
        case 403:
            .apiError("HTTP 403 (permission or quota denied)")
        default:
            .apiError("HTTP \(statusCode)")
        }
    }
}

public enum KimiAPIError: LocalizedError, Sendable, Equatable {
    case missingToken
    case invalidToken
    case missingAPIKey
    case invalidAPIKey
    case invalidRequest(String)
    case networkError(String)
    case apiError(String)
    case parseFailed(String)

    public var errorDescription: String? {
        switch self {
        case .missingToken:
            "Kimi auth token is missing. Please add your JWT token from the Kimi console."
        case .invalidToken:
            "Kimi auth token is invalid or expired. Please refresh your token."
        case .missingAPIKey:
            "Kimi Code API key is missing. Add it in Settings > Providers > Kimi or set KIMI_CODE_API_KEY."
        case .invalidAPIKey:
            "Kimi Code API key is invalid or expired. Please refresh your API key."
        case let .invalidRequest(message):
            "Invalid request: \(message)"
        case let .networkError(message):
            "Kimi network error: \(message)"
        case let .apiError(message):
            "Kimi API error: \(message)"
        case let .parseFailed(message):
            "Failed to parse Kimi usage data: \(message)"
        }
    }
}
```

**Key Patterns**:
- Multi-auth support (JWT + Bearer token + API key variants)
- JWT decoding without external libraries (base64url → standard base64 conversion)
- Status code → domain error mapping (401/403 → invalidToken, 400 → invalidRequest)
- Sendable error conformance for async contexts
- Structured logging with error context
- Graceful fallback for parsing errors (missing fields → ParseFailed)

---

## 5. Browser Cookie Access with Security Gating

**File**: `Sources/CodexBarCore/BrowserCookieAccessGate.swift`

Example of defensive security pattern: graceful degradation when Keychain prompts block access.

```swift
public enum BrowserCookieAccessGate {
    private struct State {
        var loaded = false
        var deniedUntilByBrowser: [String: Date] = [:]
    }

    private static let lock = OSAllocatedUnfairLock<State>(initialState: State())
    private static let defaultsKey = "browserCookieAccessDeniedUntil"
    private static let cooldownInterval: TimeInterval = 60 * 60 * 6
    private static let log = CodexBarLog.logger(LogCategories.browserCookieGate)

    // Check if browser cookie access is allowed (e.g., under tests, suppress if keychain required)
    static func cookieStoreAccessDecision(
        homeDirectories: [URL],
        processName: String = ProcessInfo.processInfo.processName,
        environment: [String: String] = ProcessInfo.processInfo.environment) -> BrowserCookieStoreAccessDecision
    {
        guard self.isRunningUnderTests(processName: processName, environment: environment),
              environment[self.allowTestCookieAccessEnvironmentKey] != "1"
        else {
            return .allowed
        }

        let defaultHomes = Set(BrowserCookieClient.defaultHomeDirectories().map(Self.normalizedPath))
        let usesDefaultHome = homeDirectories.contains { defaultHomes.contains(Self.normalizedPath($0)) }
        return usesDefaultHome ? .suppressed : .allowed
    }

    // Should attempt: check cooldown timer, then test keychain interaction
    public static func shouldAttempt(_ browser: Browser, now: Date = Date()) -> Bool {
        guard browser.usesKeychainForCookieDecryption else { return true }
        guard !KeychainAccessGate.isDisabled else { return false }

        let shouldCheckKeychain = self.lock.withLock { state in
            self.loadIfNeeded(&state)
            if let blockedUntil = state.deniedUntilByBrowser[browser.rawValue] {
                if blockedUntil > now {
                    self.log.debug("Cookie access blocked until \(blockedUntil.timeIntervalSince1970)")
                    return false
                }
                state.deniedUntilByBrowser.removeValue(forKey: browser.rawValue)
                self.persist(state)
            }
            return true
        }
        guard shouldCheckKeychain else { return false }

        // Test if keychain requires user interaction (would block main thread)
        let requiresInteraction = self.chromiumKeychainRequiresInteraction()
        return self.lock.withLock { state in
            self.loadIfNeeded(&state)
            if requiresInteraction {
                // Block for 6 hours after Keychain interaction required
                state.deniedUntilByBrowser[browser.rawValue] = now.addingTimeInterval(self.cooldownInterval)
                self.persist(state)
                self.log.info("Cookie access requires keychain interaction; suppressing for 6h")
                return false
            }
            return true
        }
    }

    // Record failure: block this browser for 6 hours
    public static func recordDenied(for browser: Browser, now: Date = Date()) {
        guard browser.usesKeychainForCookieDecryption else { return }
        let blockedUntil = now.addingTimeInterval(self.cooldownInterval)
        self.lock.withLock { state in
            self.loadIfNeeded(&state)
            state.deniedUntilByBrowser[browser.rawValue] = blockedUntil
            self.persist(state)
        }
        self.log.info(
            "Browser cookie access denied; suppressing",
            metadata: ["browser": browser.displayName, "until": "\(blockedUntil.timeIntervalSince1970)"])
    }

    // Preflight: check Keychain without prompting
    private static func chromiumKeychainRequiresInteraction() -> Bool {
        for label in self.safeStorageLabels {
            switch KeychainAccessPreflight.checkGenericPassword(service: label.service, account: label.account) {
            case .allowed:
                return false
            case .interactionRequired:
                return true
            case .notFound, .failure:
                continue
            }
        }
        return false
    }

    private static func loadIfNeeded(_ state: inout State) {
        guard !state.loaded else { return }
        state.loaded = true
        guard let raw = UserDefaults.standard.dictionary(forKey: self.defaultsKey) as? [String: Double] else {
            return
        }
        state.deniedUntilByBrowser = raw.compactMapValues { Date(timeIntervalSince1970: $0) }
    }

    private static func persist(_ state: State) {
        let raw = state.deniedUntilByBrowser.mapValues { $0.timeIntervalSince1970 }
        UserDefaults.standard.set(raw, forKey: self.defaultsKey)
    }
}
```

**Key Patterns**:
- Thread-safe state with `OSAllocatedUnfairLock`
- Graceful degradation: preflight check before blocking operation
- Cooldown timer: avoid repeated prompts for 6 hours after denial
- Per-browser gating (some browsers require Keychain, others don't)
- UserDefaults persistence for state recovery across app launches
- Platform-conditional compilation (`#if os(macOS)`)

---

## 6. Refresh Coordination: Generation-Based Coalescing

**File**: `Sources/CodexBar/UsageStore+Refresh.swift`

How to coordinate concurrent fetches across multiple providers, coalesce redundant requests, and handle cancellation.

```swift
extension UsageStore {
    /// Refresh with coalescing: wait for in-flight request if provider is already refreshing
    func refreshProvider(
        _ provider: UsageProvider,
        allowDisabled: Bool = false,
        coalesceIfRefreshing: Bool = false) async
    {
        // Wait for any in-flight refresh to complete
        while coalesceIfRefreshing,
              let existingState = self.providerRefreshCoordinator.coalescingState(for: provider)
        {
            switch await self.providerRefreshCoordinator.wait(for: provider, state: existingState) {
            case .cancelled:
                return
            case .retryRequired:
                // In-flight task was cancelled; start fresh fetch
                self.providerRefreshCoordinator.remove(existingState, for: provider)
                continue
            case .completed:
                // Fetch succeeded; no need to retry
                return
            }
        }

        // Begin new refresh request (replaces any previous generation)
        let request = self.providerRefreshCoordinator.beginReplacingRequest(for: provider)
        let task = Task { @MainActor [weak self] in
            guard let self else { return }
            var snapshotUpdatedAtBeforeRefresh: Date?
            var didStartRefresh = false

            // Wait for any predecessor refresh tasks to complete
            for predecessorState in request.predecessorStates {
                await predecessorState.waitForTaskCompletion()
            }

            // Check generation hasn't been cancelled
            if !Task.isCancelled, self.isCurrentProviderRefreshGeneration(provider, generation: request.generation) {
                snapshotUpdatedAtBeforeRefresh = self.snapshot(for: provider)?.updatedAt
                didStartRefresh = true
                await self.refreshProviderTracked(
                    provider,
                    allowDisabled: allowDisabled,
                    generation: request.generation)
            }

            // Publish outcome: did we get new data?
            let publishedNewSnapshot = didStartRefresh &&
                self.snapshot(for: provider)?.updatedAt != snapshotUpdatedAtBeforeRefresh
            let retryRequired = Task.isCancelled && !publishedNewSnapshot
            self.providerRefreshCoordinator.complete(
                request.state,
                for: provider,
                retryRequired: retryRequired)
        }
        request.state.install(task: task)
        _ = await self.providerRefreshCoordinator.wait(for: provider, state: request.state)
    }

    /// Check if generation hasn't been superseded by a newer refresh request
    func isCurrentProviderRefreshGeneration(_ provider: UsageProvider, generation: UInt64?) -> Bool {
        guard let generation else { return true }
        return self.providerRefreshCoordinator.isCurrent(generation, for: provider)
    }

    /// Core fetch logic with activity tracking
    private func refreshProviderTracked(
        _ provider: UsageProvider,
        allowDisabled: Bool,
        generation: UInt64) async
    {
        if self.providerRefreshCoordinator.beginActivity(for: provider) {
            self.refreshingProviders.insert(provider)
        }
        defer {
            if self.providerRefreshCoordinator.endActivity(for: provider) {
                self.refreshingProviders.remove(provider)
            }
        }
        await self.refreshProviderNow(
            provider,
            allowDisabled: allowDisabled,
            generation: generation)
    }

    /// Execute the actual fetch
    private func refreshProviderNow(
        _ provider: UsageProvider,
        allowDisabled: Bool,
        generation: UInt64) async
    {
        guard let spec = await self.providerRefreshSpec(provider) else { return }
        guard self.isCurrentProviderRefreshGeneration(provider, generation: generation) else { return }

        if !spec.isEnabled(), !allowDisabled {
            await self.clearDisabledProviderRefreshState(provider)
            return
        }

        // Fan-out handling for multi-account providers (Codex, Kilo token accounts)
        if provider == .codex, self.shouldFetchAllCodexVisibleAccounts() {
            await self.refreshCodexVisibleAccountsForMenu(generation: generation)
            return
        }

        // Keep provider fetch work off MainActor (avoid blocking menu responsiveness)
        let outcome = await withTaskGroup(
            of: ProviderFetchOutcome.self,
            returning: ProviderFetchOutcome.self)
        { group in
            group.addTask {
                await descriptor.fetchOutcome(context: fetchContext)
            }
            return await group.next()!
        }
        guard self.isCurrentProviderRefreshGeneration(provider, generation: generation) else { return }

        // Process outcome (snapshot update, error handling, etc.)
        // ...
    }
}
```

**Key Patterns**:
- Generation-based request cancellation (new request invalidates old generation)
- Coalescing: wait for in-flight fetch instead of starting redundant one
- Predecessor state tracking: if refresh B requested while A in-flight, B waits for A
- `Task.isCancelled` check: know if newer generation took over
- Activity count tracking: accurate `refreshingProviders` set for UI
- Off-MainActor fetch: non-blocking network/file I/O
- Retry-on-cancel: if cancelled but no snapshot published, retry once

---

## 7. Unit Test Patterns

**File**: `Tests/CodexBarTests/CopilotUsageModelsTests.swift`

Modern Swift Testing with inline JSON fixtures and granular assertions.

```swift
import Foundation
import Testing
@testable import CodexBarCore

struct CopilotUsageModelsTests {
    @Test
    func `decodes quota snapshots payload`() throws {
        let response = try Self.decodeFixture(
            """
            {
              "copilot_plan": "free",
              "assigned_date": "2025-01-01",
              "quota_reset_date": "2025-02-01",
              "quota_snapshots": {
                "premium_interactions": {
                  "entitlement": 500,
                  "remaining": 450,
                  "percent_remaining": 90,
                  "quota_id": "premium_interactions"
                },
                "chat": {
                  "entitlement": 300,
                  "remaining": 150,
                  "percent_remaining": 50,
                  "quota_id": "chat"
                }
              }
            }
            """)

        #expect(response.copilotPlan == "free")
        #expect(response.assignedDate == "2025-01-01")
        #expect(response.quotaResetDate == "2025-02-01")
        #expect(response.quotaSnapshots.premiumInteractions?.remaining == 450)
        #expect(response.quotaSnapshots.chat?.remaining == 150)
    }

    @Test
    func `decodes monthly and limited quota payload`() throws {
        let response = try Self.decodeFixture(
            """
            {
              "copilot_plan": "free",
              "monthly_quotas": {
                "chat": "500",
                "completions": 300
              },
              "limited_user_quotas": {
                "chat": 125,
                "completions": "75"
              }
            }
            """)

        // Verify cross-field derived state
        #expect(response.quotaSnapshots.premiumInteractions?.quotaId == "completions")
        #expect(response.quotaSnapshots.premiumInteractions?.entitlement == 300)
        #expect(response.quotaSnapshots.premiumInteractions?.remaining == 75)
        #expect(response.quotaSnapshots.premiumInteractions?.percentRemaining == 25)

        #expect(response.quotaSnapshots.chat?.quotaId == "chat")
        #expect(response.quotaSnapshots.chat?.entitlement == 500)
        #expect(response.quotaSnapshots.chat?.remaining == 125)
        #expect(response.quotaSnapshots.chat?.percentRemaining == 25)
    }

    @Test
    func `does not assume full quota when limited quotas are missing`() throws {
        let response = try Self.decodeFixture(
            """
            {
              "copilot_plan": "free",
              "monthly_quotas": {
                "chat": 500,
                "completions": 300
              }
            }
            """)

        // Explicit: missing limited_user_quotas means no remaining % can be derived
        #expect(response.quotaSnapshots.premiumInteractions == nil)
        #expect(response.quotaSnapshots.chat == nil)
    }

    @Test
    func `preserves missing date fields as nil`() throws {
        let response = try Self.decodeFixture(...)
        #expect(response.assignedDate == nil)
        #expect(response.quotaResetDate == nil)
    }

    @Test
    func `preserves explicit empty date fields`() throws {
        let response = try Self.decodeFixture(...)
        // Empty string should decode as empty, not nil
        #expect(response.assignedDate?.isEmpty == true)
        #expect(response.quotaResetDate?.isEmpty == true)
    }
}
```

**Key Patterns**:
- Multiline string literals for JSON fixtures (readable, maintainable)
- `#expect` macro over `XCTAssert` (Swift Testing framework)
- Backtick-quoted test names (readable in output)
- Test derived state: `percentRemaining = (remaining / entitlement) * 100`
- Test edge cases: missing optional fields, empty strings vs. nil, type coercion (`"500"` as Int)
- Grouped related tests in struct

---

## 8. Updater Pattern: Protocol-Based Abstraction

**File**: `Sources/CodexBar/CodexbarApp.swift`

Dependency injection for updater (Sparkle on macOS, no-op in debug/non-bundled builds).

```swift
@MainActor
protocol UpdaterProviding: AnyObject {
    var automaticallyChecksForUpdates: Bool { get set }
    var automaticallyDownloadsUpdates: Bool { get set }
    var isAvailable: Bool { get }
    var unavailableReason: String? { get }
    var updateStatus: UpdateStatus { get }
    func checkForUpdates(_ sender: Any?)
    func installUpdate()
}

final class DisabledUpdaterController: UpdaterProviding {
    var automaticallyChecksForUpdates: Bool = false
    var automaticallyDownloadsUpdates: Bool = false
    let isAvailable: Bool = false
    let unavailableReason: String?
    let updateStatus = UpdateStatus()

    init(unavailableReason: String? = nil) {
        self.unavailableReason = unavailableReason
    }

    func checkForUpdates(_ sender: Any?) {}
    func installUpdate() {}
}

#if canImport(Sparkle) && ENABLE_SPARKLE
import Sparkle

@MainActor
final class SparkleUpdaterController: NSObject, UpdaterProviding, SPUUpdaterDelegate {
    private lazy var controller = SPUStandardUpdaterController(
        startingUpdater: false,
        updaterDelegate: self,
        userDriverDelegate: nil)
    let updateStatus = UpdateStatus()
    let unavailableReason: String? = nil

    init(savedAutoUpdate: Bool) {
        super.init()
        let updater = self.controller.updater
        updater.automaticallyChecksForUpdates = savedAutoUpdate
        updater.automaticallyDownloadsUpdates = savedAutoUpdate
        self.controller.startUpdater()
    }

    var automaticallyChecksForUpdates: Bool {
        get { self.controller.updater.automaticallyChecksForUpdates }
        set { self.controller.updater.automaticallyChecksForUpdates = newValue }
    }

    var automaticallyDownloadsUpdates: Bool {
        get { self.controller.updater.automaticallyDownloadsUpdates }
        set { self.controller.updater.automaticallyDownloadsUpdates = newValue }
    }

    var isAvailable: Bool { true }

    func checkForUpdates(_ sender: Any?) {
        self.controller.checkForUpdates(sender)
    }

    func installUpdate() {
        guard let immediateInstallHandler else {
            self.controller.checkForUpdates(nil)
            return
        }
        immediateInstallHandler.install()
    }

    // Sparkle delegate methods
    nonisolated func updater(_ updater: SPUUpdater, didDownloadUpdate item: SUAppcastItem) {
        // Handle download completion
    }

    nonisolated func updater(
        _ updater: SPUUpdater,
        willInstallUpdateOnQuit item: SUAppcastItem,
        immediateInstallationBlock immediateInstallHandler: @escaping () -> Void) -> Bool
    {
        Task { @MainActor in
            self.immediateInstallHandler = ImmediateInstallHandler(immediateInstallHandler)
            self.updateStatus.isUpdateReady = true
        }
        return true
    }
}
#else
private func makeUpdaterController() -> UpdaterProviding {
    DisabledUpdaterController()
}
#endif

@MainActor
private func makeUpdaterController() -> UpdaterProviding {
    let bundleURL = Bundle.main.bundleURL
    let isBundledApp = bundleURL.pathExtension == "app"
    guard isBundledApp else {
        return DisabledUpdaterController(unavailableReason: "Updates unavailable in this build.")
    }

    if InstallOrigin.isHomebrewCask(appBundleURL: bundleURL) {
        return DisabledUpdaterController(
            unavailableReason: "Updates managed by Homebrew. Run: brew upgrade --cask steipete/tap/codexbar")
    }

    guard isDeveloperIDSigned(bundleURL: bundleURL) else {
        return DisabledUpdaterController(unavailableReason: "Updates unavailable in this build.")
    }

    let defaults = UserDefaults.standard
    let autoUpdateKey = "autoUpdateEnabled"
    let savedAutoUpdate = (defaults.object(forKey: autoUpdateKey) as? Bool) ?? true
    return SparkleUpdaterController(savedAutoUpdate: savedAutoUpdate)
}
```

**Key Patterns**:
- Protocol-based abstraction (`UpdaterProviding`) decouples implementation
- Conditional compilation gating (`#if canImport(Sparkle) && ENABLE_SPARKLE`)
- Factory function decides which updater at runtime
- Sparkling nonisolated delegate methods (safe from MainActor isolation)
- Graceful degradation: clear unavailable reasons guide users
- Homebrew detection: skip updates if managed by package manager

---

## 9. Observation Pattern for SwiftUI Refresh Tracking

**File**: `Sources/CodexBar/UsageStore.swift`

Structured observation tokens to minimize SwiftUI re-renders.

```swift
@MainActor
extension UsageStore {
    // Observation token for menu rendering: track all snapshot/error changes
    var menuObservationToken: Int {
        _ = self.snapshots
        _ = self.errors
        _ = self.lastSourceLabels
        _ = self.lastFetchAttempts
        _ = self.accountSnapshots
        _ = self.codexAccountSnapshots
        _ = self.kiloScopeSnapshots
        _ = self.tokenSnapshots
        _ = self.tokenErrors
        _ = self.tokenRefreshInFlight
        _ = self.credits
        _ = self.lastCreditsError
        _ = self.openAIDashboard
        _ = self.lastOpenAIDashboardError
        _ = self.openAIDashboardRequiresLogin
        _ = self.openAIDashboardAttachmentRevision
        _ = self.versions
        _ = self.isRefreshing
        _ = self.refreshingProviders
        _ = self.pathDebugInfo
        _ = self.statuses
        _ = self.probeLogs
        _ = self.historicalPaceRevision
        _ = self.planUtilizationHistoryRevision
        _ = self.providerStorageFootprints
        return 0
    }

    // Observation token for menu bar icon rendering: fewer properties
    var iconObservationToken: Int {
        _ = self.snapshots
        _ = self.errors
        _ = self.credits
        _ = self.lastCreditsError
        _ = self.openAIDashboard
        _ = self.lastOpenAIDashboardError
        _ = self.openAIDashboardRequiresLogin
        _ = self.refreshingProviders
        _ = self.statuses
        _ = self.historicalPaceRevision
        return 0
    }

    // Settings change observer: when settings change, invalidate caches & restart timer
    func observeSettingsChanges() {
        withObservationTracking {
            _ = self.backgroundWorkSettingsObservationToken
        } onChange: { [weak self] in
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.observeSettingsChanges()
                self.invalidateProviderAvailabilityCache()
                self.probeLogs = [:]
                guard self.startupBehavior.automaticallyStartsBackgroundWork else { return }
                self.startTimer()
                self.updateProviderRuntimes()
                await self.refreshHistoricalDatasetIfNeeded()
                await self.refreshForSettingsChange()
            }
        }
    }

    // Observe all settings that affect background refresh behavior
    var backgroundWorkSettingsObservationToken: Int {
        _ = self.settings.refreshFrequency
        _ = self.settings.statusChecksEnabled
        _ = self.settings.sessionQuotaNotificationsEnabled
        _ = self.settings.quotaWarningNotificationsEnabled
        _ = self.settings.quotaWarningThresholds
        _ = self.settings.usageBarsShowUsed
        _ = self.settings.costUsageEnabled
        _ = self.settings.mergeIcons
        _ = self.settings.debugLoadingPattern
        for implementation in ProviderCatalog.all {
            implementation.observeSettings(self.settings)
        }
        return 0
    }
}
```

**Key Patterns**:
- Granular observation tokens: menu (everything), icon (minimal), background work (settings)
- Touch properties to track them in observation context (dummy read forces inclusion)
- `withObservationTracking` + `onChange` loop for reactive updates
- Provider-specific observation via `observeSettings()` callback
- Invalidation on change: cache clearing, timer restart, async refresh
- Safe weak capture in async closure

---

## Summary: Key Architecture Insights

| Concept | Pattern | File(s) |
|---------|---------|---------|
| **Main Entry** | SwiftUI App + AppKit AppDelegate; lazy initialization; dependency injection | `CodexbarApp.swift` |
| **Data Models** | Codable snapshots; rich enums with associated values; Sendable for concurrency | `UsageFetcher.swift` |
| **Auth** | File-based (OAuth, API keys); safe atomic writes; flexible JSON parsing; backcompat layers | `CodexOAuthCredentials.swift` |
| **API Fetching** | Multi-auth (JWT + Bearer + API key); status code mapping; JWT self-parsing; error enums guide users | `KimiUsageFetcher.swift` |
| **Security** | Keychain gating; graceful degradation on denial; cooldown timer to avoid repeated prompts | `BrowserCookieAccessGate.swift` |
| **Concurrency** | Generation-based request coalescing; predecessor state tracking; off-MainActor fetches | `UsageStore+Refresh.swift` |
| **Testing** | Multiline JSON fixtures; Swift Testing macros; edge case coverage; derived state validation | `CopilotUsageModelsTests.swift` |
| **Dependency Injection** | Protocol abstraction (UpdaterProviding); conditional compilation; factory functions | `CodexbarApp.swift` |
| **Observation** | Granular tokens per render path; cascading re-runs on change; provider-specific callbacks | `UsageStore.swift` |

All code is **thread-safe** (Sendable), uses **structured concurrency** (async/await), and gracefully handles **partial failures** (missing auth → clear error message → guide to action).
