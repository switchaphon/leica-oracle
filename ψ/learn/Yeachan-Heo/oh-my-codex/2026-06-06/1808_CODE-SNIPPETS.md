# oh-my-codex: Code Architecture & Key Patterns

**Source**: `https://github.com/Yeachan-Heo/oh-my-codex`  
**Date Captured**: 2026-06-06  
**Focus**: Orchestration runtime, tmux multiplexing, hook system, team coordination

---

## 1. CLI Entry Point & Command Dispatch

### Main Runtime Entry (omx-runtime)

**File**: `crates/omx-runtime/src/main.rs`

Core CLI dispatcher with 5 major subcommands:
- `schema` — Print runtime contract (operation names, event names, schema version)
- `snapshot` — Dump complete runtime state (authority, dispatch, replay, readiness)
- `mux-contract` — Validate tmux adapter readiness
- `exec <json>` — Process a single RuntimeCommand, persist state
- `init <state-dir>` — Initialize fresh state directory

```rust
fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().skip(1).collect();
    let first = args.first().map(|s| s.as_str());
    
    match first {
        Some("exec") => {
            let json_input = second.ok_or("exec requires a JSON command argument")?;
            let state_dir = args.iter().find_map(|a| a.strip_prefix("--state-dir="));
            let compact = args.iter().any(|a| a == "--compact");
            let mut engine = match state_dir {
                Some(dir) => RuntimeEngine::load(dir)
                    .unwrap_or_else(|_| RuntimeEngine::new().with_state_dir(dir)),
                None => RuntimeEngine::new(),
            };

            let command: RuntimeCommand =
                serde_json::from_str(json_input).map_err(|e| format!("invalid JSON: {e}"))?;
            let event = engine.process(command).map_err(|e| e.to_string())?;

            if compact {
                engine.compact();
            }
            if state_dir.is_some() {
                engine.persist()?;
                engine.write_compatibility_view()?;
            }
            println!("{}", serde_json::to_string_pretty(&event)?);
            Ok(())
        }
        // ... other subcommands
    }
}
```

---

## 2. State Machine: RuntimeEngine

**File**: `crates/omx-runtime-core/src/engine.rs`

Orchestrator state machine that manages **authority**, **dispatch**, **mailbox**, and **replay** subsystems.

### Architecture

```rust
pub struct RuntimeEngine {
    authority: AuthorityLease,        // Who owns the session
    dispatch: DispatchLog,             // Dispatch request tracking (Pending → Notified → Delivered | Failed)
    mailbox: MailboxLog,               // Worker-to-worker messages
    replay: ReplayState,               // Request replay cursors
    event_log: Vec<RuntimeEvent>,      // Immutable audit trail
    state_dir: Option<PathBuf>,        // Persistent state location
}

impl RuntimeEngine {
    pub fn process(&mut self, command: RuntimeCommand) -> Result<RuntimeEvent, EngineError> {
        let event = match command {
            RuntimeCommand::AcquireAuthority { owner, lease_id, leased_until } => {
                self.authority.acquire(&owner, &lease_id, &leased_until)?;
                RuntimeEvent::AuthorityAcquired { owner, lease_id, leased_until }
            }
            RuntimeCommand::QueueDispatch { request_id, target, metadata } => {
                self.dispatch.queue(&request_id, &target, metadata.clone());
                RuntimeEvent::DispatchQueued { request_id, target, metadata }
            }
            RuntimeCommand::MarkDelivered { request_id } => {
                self.dispatch.mark_delivered(&request_id)?;
                RuntimeEvent::DispatchDelivered { request_id }
            }
            // ... other command handlers
        };
        self.event_log.push(event.clone());
        Ok(event)
    }

    /// Snapshot captures all subsystem states (immutable view for reads)
    pub fn snapshot(&self) -> RuntimeSnapshot {
        RuntimeSnapshot {
            schema_version: RUNTIME_SCHEMA_VERSION,
            authority: self.authority.to_snapshot(),
            backlog: self.dispatch.to_backlog_snapshot(),
            replay: self.replay.to_snapshot(),
            readiness: derive_readiness(&self.authority, &self.dispatch, &self.replay),
        }
    }

    /// Compact removes event log entries for delivered/failed dispatches
    pub fn compact(&mut self) {
        let terminal_ids: std::collections::HashSet<&str> = self
            .dispatch.records()
            .iter()
            .filter(|r| {
                r.status == crate::dispatch::DispatchStatus::Delivered
                    || r.status == crate::dispatch::DispatchStatus::Failed
            })
            .map(|r| r.request_id.as_str())
            .collect();

        self.event_log.retain(|event| match event {
            RuntimeEvent::DispatchQueued { request_id, .. }
            | RuntimeEvent::DispatchNotified { request_id, .. }
            | RuntimeEvent::DispatchDelivered { request_id }
            | RuntimeEvent::DispatchFailed { request_id, .. } => {
                !terminal_ids.contains(request_id.as_str())
            }
            _ => true,
        });
    }

    /// Persist writes snapshot + events + compatibility view (for legacy TS readers)
    pub fn persist(&self) -> Result<(), EngineError> {
        let dir = self.state_dir.as_ref().ok_or_else(|| {
            std::io::Error::new(std::io::ErrorKind::NotFound, "no state_dir configured")
        })?;
        std::fs::create_dir_all(dir)?;

        let lock_file = std::fs::File::create(dir.join("engine.lock"))?;
        FileExt::lock_exclusive(&lock_file)?;

        let snapshot_json = serde_json::to_string_pretty(&self.snapshot())?;
        std::fs::write(dir.join("snapshot.json"), snapshot_json)?;

        let events_json = serde_json::to_string_pretty(&self.event_log)?;
        std::fs::write(dir.join("events.json"), events_json)?;

        drop(lock_file);
        Ok(())
    }
}
```

**Key Pattern**: Event-sourcing via immutable event log. All state changes are recorded before persisted. Snapshots are derived views, not primary state.

---

## 3. Dispatch State Machine (FSM)

**File**: `crates/omx-runtime-core/src/dispatch.rs`

Tracks work-in-progress requests through a strict state machine:

```
Pending → Notified → Delivered (terminal)
       ↘           ↗
         Failed (terminal)
```

### DispatchRecord & State Transitions

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DispatchStatus {
    Pending,    // Queued, awaiting notification
    Notified,   // Notified to recipient, awaiting delivery confirmation
    Delivered,  // Recipient confirmed execution
    Failed,     // Could not deliver or execution failed
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DispatchRecord {
    pub request_id: String,
    pub target: String,
    pub status: DispatchStatus,
    pub created_at: String,         // ISO8601
    pub notified_at: Option<String>,
    pub delivered_at: Option<String>,
    pub failed_at: Option<String>,
    pub reason: Option<String>,
    pub metadata: Option<serde_json::Value>,
}

impl DispatchLog {
    pub fn queue(&mut self, request_id: impl Into<String>, target: impl Into<String>, metadata: Option<serde_json::Value>) {
        self.records.push(DispatchRecord {
            request_id: request_id.into(),
            target: target.into(),
            status: DispatchStatus::Pending,
            created_at: now_iso(),
            notified_at: None,
            delivered_at: None,
            failed_at: None,
            reason: None,
            metadata,
        });
    }

    pub fn mark_notified(&mut self, request_id: &str, channel: impl Into<String>) -> Result<(), DispatchError> {
        let record = self.find_mut(request_id)?;
        if record.status != DispatchStatus::Pending {
            return Err(DispatchError::InvalidTransition {
                request_id: request_id.to_string(),
                from: record.status.clone(),
                to: DispatchStatus::Notified,
            });
        }
        record.status = DispatchStatus::Notified;
        record.notified_at = Some(now_iso());
        record.reason = Some(channel.into());
        Ok(())
    }

    pub fn mark_delivered(&mut self, request_id: &str) -> Result<(), DispatchError> {
        let record = self.find_mut(request_id)?;
        if record.status != DispatchStatus::Notified {
            return Err(DispatchError::InvalidTransition {
                request_id: request_id.to_string(),
                from: record.status.clone(),
                to: DispatchStatus::Delivered,
            });
        }
        record.status = DispatchStatus::Delivered;
        record.delivered_at = Some(now_iso());
        Ok(())
    }

    /// Allow failed from both Pending (target resolution failure) and Notified (delivery failure)
    pub fn mark_failed(&mut self, request_id: &str, reason: impl Into<String>) -> Result<(), DispatchError> {
        let record = self.find_mut(request_id)?;
        if record.status != DispatchStatus::Pending && record.status != DispatchStatus::Notified {
            return Err(DispatchError::InvalidTransition {
                request_id: request_id.to_string(),
                from: record.status.clone(),
                to: DispatchStatus::Failed,
            });
        }
        record.status = DispatchStatus::Failed;
        record.failed_at = Some(now_iso());
        record.reason = Some(reason.into());
        Ok(())
    }

    pub fn to_backlog_snapshot(&self) -> BacklogSnapshot {
        let mut snapshot = BacklogSnapshot::default();
        for record in &self.records {
            match record.status {
                DispatchStatus::Pending => snapshot.pending += 1,
                DispatchStatus::Notified => snapshot.notified += 1,
                DispatchStatus::Delivered => snapshot.delivered += 1,
                DispatchStatus::Failed => snapshot.failed += 1,
            }
        }
        snapshot
    }
}
```

**Key Pattern**: Strict state machine with typed errors. Invalid transitions reject (fail-fast). Reasons (channel, error message) always recorded. Backlog snapshot aggregates counts for HUD rendering.

---

## 4. Authority Lease (Exclusive Ownership)

**File**: `crates/omx-runtime-core/src/authority.rs`

Implements exclusive session ownership with lease expiry:

```rust
pub struct AuthorityLease {
    owner: Option<String>,
    lease_id: Option<String>,
    leased_until: Option<String>,  // ISO8601 timestamp
    stale: bool,
    stale_reason: Option<String>,
}

pub enum AuthorityError {
    AlreadyHeldByOther { current_owner: String },
    OwnerMismatch { current_owner: String },
    NotHeld,
}

impl AuthorityLease {
    pub fn acquire(&mut self, owner: impl Into<String>, lease_id: impl Into<String>, leased_until: impl Into<String>) -> Result<(), AuthorityError> {
        let owner = owner.into();
        if let Some(ref current) = self.owner {
            if *current != owner {
                return Err(AuthorityError::AlreadyHeldByOther {
                    current_owner: current.clone(),
                });
            }
        }
        self.owner = Some(owner);
        self.lease_id = Some(lease_id.into());
        self.leased_until = Some(leased_until.into());
        self.stale = false;
        self.stale_reason = None;
        Ok(())
    }

    pub fn renew(&mut self, owner: impl AsRef<str>, lease_id: impl Into<String>, leased_until: impl Into<String>) -> Result<(), AuthorityError> {
        match &self.owner {
            None => Err(AuthorityError::NotHeld),
            Some(current) if current != owner.as_ref() => Err(AuthorityError::OwnerMismatch {
                current_owner: current.clone(),
            }),
            _ => {
                self.lease_id = Some(lease_id.into());
                self.leased_until = Some(leased_until.into());
                self.stale = false;
                self.stale_reason = None;
                Ok(())
            }
        }
    }

    pub fn mark_stale(&mut self, reason: impl Into<String>) {
        self.stale = true;
        self.stale_reason = Some(reason.into());
    }

    pub fn to_snapshot(&self) -> AuthoritySnapshot {
        AuthoritySnapshot {
            owner: self.owner.clone(),
            lease_id: self.lease_id.clone(),
            leased_until: self.leased_until.clone(),
            stale: self.stale,
            stale_reason: self.stale_reason.clone(),
        }
    }
}
```

**Key Pattern**: Lease expiry & staleness detection. Same owner can renew. Different owners rejected. Stale flag for heartbeat timeout.

---

## 5. Tmux Multiplexing Adapter

**File**: `crates/omx-mux/src/tmux.rs`

Protocol-adapter pattern: pluggable tmux operations abstracted as `MuxOperation` → `MuxOutcome` or `MuxError`.

### MuxTarget & Operations

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum MuxTarget {
    DeliveryHandle(String),  // "sess:0.1" — session:window.pane
    Detached,                 // Detached state (no pane)
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum MuxOperation {
    ResolveTarget { target: MuxTarget },
    SendInput { target: MuxTarget, envelope: InputEnvelope },
    CaptureTail { target: MuxTarget, visible_lines: usize },
    InspectLiveness { target: MuxTarget },
    Attach { target: MuxTarget },
    Detach { target: MuxTarget },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum MuxOutcome {
    TargetResolved { resolved_handle: String },
    InputAccepted { bytes_written: usize },
    TailCaptured { visible_lines: usize, body: String },
    LivenessChecked { alive: bool },
    Attached { handle: String },
    Detached { handle: String },
}
```

### TmuxAdapter Implementation

```rust
#[derive(Debug, Clone, Copy, Default)]
pub struct TmuxAdapter;

impl MuxAdapter for TmuxAdapter {
    fn adapter_name(&self) -> &'static str {
        "tmux"
    }

    fn execute(&self, operation: &MuxOperation) -> Result<MuxOutcome, MuxError> {
        match operation {
            MuxOperation::ResolveTarget { target } => self.do_resolve_target(target),
            MuxOperation::SendInput { target, envelope } => self.do_send_input(target, envelope),
            MuxOperation::CaptureTail { target, visible_lines } => {
                self.do_capture_tail(target, *visible_lines)
            }
            MuxOperation::InspectLiveness { target } => self.do_inspect_liveness(target),
            MuxOperation::Attach { target } => self.do_attach(target),
            MuxOperation::Detach { target } => self.do_detach(target),
        }
    }
}

impl TmuxAdapter {
    fn do_send_input(&self, target: &MuxTarget, envelope: &InputEnvelope) -> Result<MuxOutcome, MuxError> {
        let handle = resolve_target_handle(target)?;
        let text = envelope.normalized_text();

        // Send the literal text
        let args = build_send_keys_args(&handle, &text);
        run_tmux(&args)?;

        // Send enter presses per submit policy
        if let SubmitPolicy::Enter { presses, delay_ms } = &envelope.submit {
            for i in 0..*presses {
                if i > 0 && *delay_ms > 0 {
                    thread::sleep(Duration::from_millis(*delay_ms));
                }
                let enter_args = build_enter_key_args(&handle);
                let str_args: Vec<&str> = enter_args.iter().map(|s| s.as_str()).collect();
                run_tmux(&str_args)?;
            }
        }

        Ok(MuxOutcome::InputAccepted {
            bytes_written: text.len(),
        })
    }

    fn do_capture_tail(&self, target: &MuxTarget, visible_lines: usize) -> Result<MuxOutcome, MuxError> {
        let handle = resolve_target_handle(target)?;
        let args = build_capture_pane_args(&handle, visible_lines);
        let str_args: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
        let body = run_tmux(&str_args)?;

        Ok(MuxOutcome::TailCaptured { visible_lines, body })
    }
}

fn run_tmux(args: &[&str]) -> Result<String, MuxError> {
    let output = Command::new("tmux")
        .args(args)
        .output()
        .map_err(|e| MuxError::AdapterFailed(format!("failed to run tmux: {e}")))?;

    if output.status.success() {
        String::from_utf8(output.stdout)
            .map_err(|e| MuxError::AdapterFailed(format!("invalid utf-8 from tmux: {e}")))
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(MuxError::AdapterFailed(format!(
            "tmux {} failed: {}",
            args.first().unwrap_or(&""),
            stderr.trim()
        )))
    }
}
```

**Key Pattern**: Trait-based adapter. Operations are JSON-serializable. Error types include context. Newline normalization to prevent multiline injection.

---

## 6. Input Envelope & Submit Policy

**File**: `crates/omx-mux/src/types.rs`

Encapsulates text + submission strategy for controlled keyboard injection:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SubmitPolicy {
    None,
    Enter { presses: u8, delay_ms: u64 },
}

impl SubmitPolicy {
    pub fn enter(presses: u8, delay_ms: u64) -> Self {
        Self::Enter {
            presses: presses.max(1),
            delay_ms,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InputEnvelope {
    pub literal_text: String,
    pub submit: SubmitPolicy,
    pub replace_newlines_with_spaces: bool,
}

impl InputEnvelope {
    pub fn new(literal_text: impl Into<String>, submit: SubmitPolicy) -> Self {
        Self {
            literal_text: literal_text.into(),
            submit,
            replace_newlines_with_spaces: true,
        }
    }

    pub fn normalized_text(&self) -> String {
        if self.replace_newlines_with_spaces {
            self.literal_text
                .chars()
                .map(|ch| if ch == '\r' || ch == '\n' { ' ' } else { ch })
                .collect()
        } else {
            self.literal_text.clone()
        }
    }
}
```

**Key Pattern**: Newline sanitization prevents injection of unintended commands. Configurable enter count + delay for confirmation loops. Submit policy decoupled from text.

---

## 7. Mailbox: Worker-to-Worker Messaging

**File**: `crates/omx-runtime-core/src/mailbox.rs`

Asynchronous message delivery between workers with idempotency:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MailboxRecord {
    pub message_id: String,
    pub from_worker: String,
    pub to_worker: String,
    pub body: String,
    pub created_at: String,
    pub notified_at: Option<String>,
    pub delivered_at: Option<String>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct MailboxLog {
    records: Vec<MailboxRecord>,
}

impl MailboxLog {
    pub fn create(&mut self, message_id: impl Into<String>, from_worker: impl Into<String>, to_worker: impl Into<String>, body: impl Into<String>) {
        self.records.push(MailboxRecord {
            message_id: message_id.into(),
            from_worker: from_worker.into(),
            to_worker: to_worker.into(),
            body: body.into(),
            created_at: now_iso(),
            notified_at: None,
            delivered_at: None,
        });
    }

    pub fn mark_notified(&mut self, message_id: &str) -> Result<(), MailboxError> {
        let record = self.find_mut(message_id)?;
        if record.delivered_at.is_some() {
            return Err(MailboxError::AlreadyDelivered {
                message_id: message_id.to_string(),
            });
        }
        record.notified_at = Some(now_iso());
        Ok(())
    }

    pub fn mark_delivered(&mut self, message_id: &str) -> Result<(), MailboxError> {
        let record = self.find_mut(message_id)?;
        if record.delivered_at.is_some() {
            return Err(MailboxError::AlreadyDelivered {
                message_id: message_id.to_string(),
            });
        }
        record.delivered_at = Some(now_iso());
        Ok(())
    }
}
```

**Key Pattern**: Delivery idempotency (no double-delivery). Notified → Delivered path. Errors on already-delivered attempts.

---

## 8. Sparkshell: Command Output Summarization

**File**: `crates/omx-sparkshell/src/main.rs` + `codex_bridge.rs`

Lightweight CLI for capturing command output, detecting verbosity, and requesting summaries via local API.

### Main Execution Flow

```rust
fn run(args: Vec<String>) -> Result<(), SparkshellError> {
    let options = parse_input(&args)?;
    
    let execution_argv = match &options.target {
        SparkShellTarget::Command(command) => command.clone(),
        SparkShellTarget::Shell(script) => resolve_shell_argv(script),
        SparkShellTarget::TmuxPane { pane_id, tail_lines } => {
            let mut argv = vec!["tmux".to_string()];
            argv.extend(build_capture_pane_args(pane_id, *tail_lines));
            argv
        }
    };

    let raw_output = execute_command(&execution_argv)?;
    let redacted = redact_output(&raw_output);
    let output = if options.json { &redacted.output } else { &raw_output };
    
    let threshold = read_line_threshold();
    let line_count = combined_visible_lines(&output.stdout, &output.stderr);
    let evidence = build_evidence(&options, output);
    let cache_meta = handle_cache(&options, output, &evidence.raw_hash)?;

    if options.json {
        let summary = if options.since_last {
            since_last_summary(output, cache_meta.as_ref(), options.budget)
        } else if line_count <= threshold {
            compact_text(&combined_text(output), options.budget)
        } else if cache_meta.as_ref().is_some_and(|meta| meta.cache_hit) {
            "unchanged since previous observation".to_string()
        } else {
            summarize_output(&execution_argv, output)?
        };
        
        write_json_report(&options, output, &summary, &evidence, cache_meta, redacted.count)?;
        process::exit(output.exit_code());
    }

    if line_count <= threshold {
        write_raw_output(&output.stdout, &output.stderr)?;
        process::exit(output.exit_code());
    }

    match summarize_output(&execution_argv, output) {
        Ok(summary) => {
            let mut stdout = io::stdout().lock();
            stdout.write_all(compact_text(&summary, options.budget).as_bytes())?;
            if !summary.ends_with('\n') {
                stdout.write_all(b"\n")?;
            }
            stdout.flush()?;
        }
        Err(error) => {
            write_raw_output(&output.stdout, &output.stderr)?;
            eprintln!("omx sparkshell: summary unavailable ({error}); showing raw output instead");
        }
    }

    process::exit(output.exit_code());
}
```

### Summary API Bridge

```rust
pub fn summarize_output(command: &[String], output: &CommandOutput) -> Result<String, SparkshellError> {
    let prompt = build_summary_prompt(command, output);
    let model = resolve_model();
    let fallback_model = resolve_fallback_model();
    let timeout_ms = read_summary_timeout_ms();
    
    match request_summary(&prompt, &model, timeout_ms) {
        Ok(stdout) => normalize_summary(&stdout).ok_or_else(|| {
            SparkshellError::SummaryBridge(
                "local API returned no valid summary sections".to_string(),
            )
        }),
        Err(primary_error) => {
            let primary_message = primary_error.to_string();
            if fallback_model != model && should_retry_with_fallback(&primary_message) {
                match request_summary(&prompt, &fallback_model, timeout_ms) {
                    Ok(fallback_stdout) => normalize_summary(&fallback_stdout).ok_or_else(|| {
                        SparkshellError::SummaryBridge(
                            "local API fallback returned no valid summary sections".to_string(),
                        )
                    }),
                    Err(fallback_error) => Err(SparkshellError::SummaryBridge(format!(
                        "local API failed for primary model `{model}` ({primary_message}) and fallback model `{fallback_model}` ({fallback_error})"
                    ))),
                }
            } else {
                Err(SparkshellError::SummaryBridge(format!(
                    "local API summary request failed: {primary_message}"
                )))
            }
        }
    }
}

fn should_retry_with_fallback(stderr: &str) -> bool {
    let normalized = stderr.to_ascii_lowercase();
    [
        "quota",
        "rate limit",
        "429",
        "unavailable",
        "not available",
        "unknown model",
        "model not found",
        "no access",
        "capacity",
    ]
    .iter()
    .any(|needle| normalized.contains(needle))
}
```

**Key Pattern**: Adaptive summarization — raw output if small, cache if unchanged, summary via local API otherwise. Automatic fallback on quota/rate-limit errors. Platform-aware shell resolution (bash -lc on POSIX, pwsh/cmd on Windows).

---

## 9. Command Family Registry (sparkshell)

**File**: `crates/omx-sparkshell/src/registry/mod.rs`

Plugin registry for language-specific command handling:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CommandFamily {
    pub name: &'static str,
    pub pattern: &'static str,
    pub executables: &'static [&'static str],
    pub description: &'static str,
    pub what_it_does: &'static str,
}

const FAMILIES: [&CommandFamily; 11] = [
    &generic_shell::FAMILY,
    &git::FAMILY,
    &node_js::FAMILY,
    &python::FAMILY,
    &rust::FAMILY,
    &go::FAMILY,
    &ruby::FAMILY,
    &java_kotlin::FAMILY,
    &c_cpp::FAMILY,
    &csharp::FAMILY,
    &swift::FAMILY,
];

pub fn resolve_family(program: &str, args: &[String]) -> &'static CommandFamily {
    let normalized_program = normalize_program(program);
    let normalized_first_arg = args.first().map(|arg| normalize_program(arg));

    FAMILIES
        .iter()
        .copied()
        .find(|family| matches_family(family, normalized_program, normalized_first_arg))
        .unwrap_or(&generic_shell::FAMILY)
}

fn normalize_program(program: &str) -> &str {
    let basename = program.rsplit(['/', '\\']).next().unwrap_or(program);
    basename
        .strip_suffix(".exe")
        .or_else(|| basename.strip_suffix(".cmd"))
        .or_else(|| basename.strip_suffix(".bat"))
        .or_else(|| basename.strip_suffix(".ps1"))
        .unwrap_or(basename)
}
```

**Key Pattern**: Static family registry with dynamic resolution. Handles platform-specific extensions. Fallback to generic shell.

---

## 10. Hook System: Extensibility

**File**: `src/cli/hooks.ts` + `src/config/codex-hooks.ts`

Two-tier hook architecture: managed (CLI-driven) + extensible (plugin-driven).

### Hooks CLI Command

```typescript
export async function hooksCommand(args: string[]): Promise<void> {
  const subcommand = args[0] || 'status';
  switch (subcommand) {
    case 'init':
      await initHooks();
      return;
    case 'status':
      await statusHooks();
      return;
    case 'validate':
      await validateHooks();
      return;
    case 'test':
      await testHooks();
      return;
    default:
      throw new Error(`Unknown hooks subcommand: ${subcommand}`);
  }
}

async function testHooks(): Promise<void> {
  const cwd = process.cwd();
  const discovered = await discoverHookPlugins(cwd);

  const event = buildHookEvent('turn-complete', {
    source: 'native',
    context: {
      reason: 'omx-hooks-test',
    },
    session_id: 'omx-hooks-test',
    thread_id: `thread-${Date.now()}`,
    turn_id: `turn-${Date.now()}`,
  });

  const rawResult = await dispatchHookEvent(event, {
    cwd,
    event,
    env: {
      ...process.env,
      OMX_HOOK_PLUGINS: '1',
    },
    allowInTeamWorker: false,
  } as never);
  
  const result = normalizeDispatchResult(rawResult);
  
  console.log('hooks test dispatch complete');
  console.log(`plugins discovered: ${discovered.length}`);
  console.log(`plugins enabled: ${result.enabled ? 'yes' : 'no'}`);
  for (const pluginResult of result.results) {
    const label = pluginLabelFromResult(pluginResult);
    const status = pluginStatusFromResult(pluginResult);
    console.log(label, status);
  }
}
```

### Managed Hook Configuration

```typescript
export const MANAGED_HOOK_EVENTS = [
  "SessionStart",
  "PreToolUse",
  "PostToolUse",
  "UserPromptSubmit",
  "PreCompact",
  "PostCompact",
  "Stop",
] as const;

export interface ManagedHookEntry {
  matcher?: string;  // Regex matcher for hook trigger condition
  hooks: Array<{
    type: "command";
    command: string;
    statusMessage?: string;
    timeout?: number;
  }>;
}

export interface ManagedCodexHooksConfig {
  hooks: Record<ManagedHookEventName, ManagedHookEntry[]>;
}

export function buildManagedCodexNativeHookCommand(
  pkgRoot: string,
  optionsOrPlatform: HookCommandPlatform | ManagedCodexHookOptions = process.platform,
): string {
  const options = typeof optionsOrPlatform === "string"
    ? { platform: optionsOrPlatform }
    : optionsOrPlatform;
  const platform = options.platform ?? process.platform;
  const hookScript = platform === "win32"
    ? win32.join(pkgRoot, "dist", "scripts", "codex-native-hook.js")
    : join(pkgRoot, "dist", "scripts", "codex-native-hook.js");

  if (platform === "win32") {
    const codexHomeDir = options.codexHomeDir ?? dirname(pkgRoot);
    const shimPath = buildManagedCodexNativeHookWindowsShimPath(codexHomeDir);
    return `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ${quoteWindowsCommandPart(shimPath)}`;
  }

  return `${quoteCommandPart(process.execPath)} ${quoteCommandPart(hookScript)}`;
}

export function buildManagedCodexHooksConfig(
  pkgRoot: string,
  options: ManagedCodexHookOptions = {},
): ManagedCodexHooksConfig {
  const command = buildManagedCodexNativeHookCommand(pkgRoot, options);

  return {
    hooks: {
      SessionStart: [
        buildCommandHook(command, {
          matcher: "startup|resume|clear",
        }),
      ],
      PreToolUse: [
        buildCommandHook(command),
      ],
      PostToolUse: [
        buildCommandHook(command),
      ],
      UserPromptSubmit: [
        buildCommandHook(command),
      ],
      PreCompact: [
        buildCommandHook(command),
      ],
      PostCompact: [
        buildCommandHook(command),
      ],
      Stop: [
        buildCommandHook(command, {
          timeout: 30,
        }),
      ],
    },
  };
}
```

**Key Pattern**: 
- **Managed hooks**: Declarative, CLI-configurable, per-event matcher support.
- **Plugin hooks**: ESM modules with `onHookEvent(event, sdk)` signature.
- **Event types**: SessionStart, PreToolUse, PostToolUse, UserPromptSubmit, PreCompact, PostCompact, Stop.
- **Platform shim**: Windows uses PowerShell wrapper to pipe stdin/stdout.

---

## 11. API Daemon & Secret Redaction

**File**: `crates/omx-api/src/lib.rs`

Local API daemon for centralized LLM access with token rotation:

```rust
pub const DEFAULT_API_PORT: u16 = 14510;

pub struct ServerConfig {
    pub host: String,
    pub port: u16,
    pub backend: BackendMode,
    pub state_file: PathBuf,
    pub once: bool,
    pub daemon: bool,
    pub local_bearer_token: Option<String>,
}

pub struct DaemonState {
    pub pid: u32,
    pub host: String,
    pub port: u16,
    pub backend: BackendMode,
    pub started_at_unix: u64,
    #[serde(skip)]
    pub local_bearer_token: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub local_bearer_token_file: Option<PathBuf>,
}

impl DaemonState {
    pub fn base_url(&self) -> String {
        format!("http://{}:{}", self.host, self.port)
    }
}

pub fn redact_secrets(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    let mut redact_next = false;
    for (index, token) in input.split_whitespace().enumerate() {
        if index > 0 {
            out.push(' ');
        }
        let lower = token.to_ascii_lowercase();
        if redact_next
            || lower.starts_with("sk-")
            || lower.starts_with("sess-")
            || lower.starts_with("bearer")
            || lower.contains("api_key=")
            || lower.contains("apikey=")
            || lower.contains("authorization:")
        {
            out.push_str("[REDACTED]");
            redact_next =
                lower == "bearer" || lower.ends_with("bearer") || lower.contains("authorization:");
        } else {
            out.push_str(token);
            redact_next = false;
        }
    }
    redact_secret_markers(&redact_key_value_secret_fragments(
        &redact_json_secret_values(&out),
    ))
}

fn write_local_bearer_token(path: impl AsRef<Path>, token: &str) -> Result<()> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        let mut file = fs::OpenOptions::new()
            .create(true)
            .truncate(true)
            .write(true)
            .mode(0o600)
            .open(path)?;
        file.write_all(token.as_bytes())?;
        Ok(())
    }
    #[cfg(not(unix))]
    {
        fs::write(path, token)?;
        Ok(())
    }
}
```

**Key Pattern**: Secret patterns (sk-, sess-, bearer, api_key=, authorization:). Separate token file (600 on Unix). JSON secret value redaction. Hotswap via token file without daemon restart.

---

## 12. Pane Readiness & Confirmation Policy

**File**: `crates/omx-mux/src/types.rs`

Autopilot gate logic for safe command injection:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum PaneReadinessReason {
    Ok,
    MissingTarget,
    ScrollActive,
    PaneRunningShell,
    PaneHasActiveTask,
    PaneNotReady,
    TargetResolutionFailed(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PaneReadiness {
    pub reason: PaneReadinessReason,
    pub pane_target: Option<String>,
    pub pane_current_command: Option<String>,
    pub pane_capture: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ConfirmationPolicy {
    pub narrow_capture_lines: usize,         // 8 lines for narrow panes
    pub wide_capture_lines: usize,           // 80 lines for wide panes
    pub verify_delay_ms: u64,                // 250ms between checks
    pub verify_rounds: u8,                   // 3 confirmation attempts
    pub allow_active_task_confirmation: bool, // OK to inject if task running?
    pub require_ready_for_worker_targets: bool, // Strict readiness check
    pub non_empty_tail_lines: usize,         // 24 lines minimum in pane
    pub retry_submit_without_retyping: bool, // Retry enter if needed
}

impl Default for ConfirmationPolicy {
    fn default() -> Self {
        Self {
            narrow_capture_lines: 8,
            wide_capture_lines: 80,
            verify_delay_ms: 250,
            verify_rounds: 3,
            allow_active_task_confirmation: true,
            require_ready_for_worker_targets: true,
            non_empty_tail_lines: 24,
            retry_submit_without_retyping: true,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum DeliveryConfirmation {
    Confirmed,
    ConfirmedActiveTask,
    Unconfirmed,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InjectionPreflight {
    pub skip_if_scrolling: bool,
    pub require_running_agent: bool,
    pub require_ready: bool,
    pub require_idle: bool,
    pub capture_lines: usize,
}

impl Default for InjectionPreflight {
    fn default() -> Self {
        Self {
            skip_if_scrolling: true,
            require_running_agent: true,
            require_ready: true,
            require_idle: true,
            capture_lines: 80,
        }
    }
}
```

**Key Pattern**: Multi-layer readiness gates: scroll activity, task state, shell state, pane liveness. Configurable confirmation policy. Verify loop with delays. Unconfirmed delivery on preflight failure.

---

## 13. Cross-Cutting: Platform-Aware Shell Resolution

**File**: `crates/omx-sparkshell/src/exec.rs`

Safe, platform-aware command execution:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ShellPlatform {
    Windows,
    Posix,
}

fn current_platform() -> ShellPlatform {
    if cfg!(windows) {
        ShellPlatform::Windows
    } else {
        ShellPlatform::Posix
    }
}

fn resolve_shell_argv_for_platform(
    script: &str,
    platform: ShellPlatform,
    exists: impl Fn(&str) -> bool,
) -> Vec<String> {
    match platform {
        ShellPlatform::Posix => vec!["bash".to_string(), "-lc".to_string(), script.to_string()],
        ShellPlatform::Windows => {
            if exists("pwsh") {
                return vec![
                    "pwsh".to_string(),
                    "-NoLogo".to_string(),
                    "-NoProfile".to_string(),
                    "-Command".to_string(),
                    script.to_string(),
                ];
            }
            if exists("powershell.exe") {
                return vec![
                    "powershell.exe".to_string(),
                    "-NoLogo".to_string(),
                    "-NoProfile".to_string(),
                    "-Command".to_string(),
                    script.to_string(),
                ];
            }
            vec![
                std::env::var("ComSpec").unwrap_or_else(|_| "cmd.exe".to_string()),
                "/d".to_string(),
                "/s".to_string(),
                "/c".to_string(),
                script.to_string(),
            ]
        }
    }
}

pub fn execute_command(argv: &[String]) -> Result<CommandOutput, SparkshellError> {
    if argv.is_empty() {
        return Err(SparkshellError::InvalidArgs(
            "usage: omx-sparkshell <command> [args...]".to_string(),
        ));
    }

    let mut command = build_command(&argv[0], &argv[1..]);
    let Output { status, stdout, stderr } = command.output()?;

    Ok(CommandOutput { status, stdout, stderr })
}
```

**Key Pattern**: Platform detection at compile-time flags. Shell preference hierarchy (pwsh → powershell.exe → cmd.exe on Windows). POSIX: bash -lc (login shell, rc files). ComSpec fallback.

---

## Summary: Key Architectural Patterns

### 1. **Event Sourcing**
   - Immutable event log as primary audit trail
   - Snapshots derived from log for readiness checks
   - Compact operation removes terminal events

### 2. **State Machine FSM**
   - Dispatch: Pending → Notified → Delivered | Failed
   - Authority: None → Held (with lease) → Stale
   - Strict transitions, typed errors, reason always recorded

### 3. **Trait-Based Adapters**
   - MuxAdapter trait for tmux protocol abstraction
   - JSON-serializable operations + outcomes
   - Error types include context (InvalidTarget, AdapterFailed)

### 4. **Exclusive Ownership with Leasing**
   - Authority lease with expiry timestamp
   - Staleness detection separate from ownership
   - Idempotent renewal for same owner

### 5. **Adaptive Summarization**
   - Line count threshold → decide raw vs summary
   - Cache hit → skip API call
   - Automatic fallback on quota/rate-limit

### 6. **Multi-Layer Autopilot Gates**
   - Readiness: liveness, scrolling, task state
   - Confirmation policy: verify rounds, delays
   - Preflight checks prevent premature injection

### 7. **Hook Extensibility**
   - Managed (CLI-driven) vs Plugin (ESM modules)
   - Event dispatch with per-plugin isolation
   - Platform-aware shim (Windows PowerShell wrapper)

### 8. **Secret Hygiene**
   - Pattern-based redaction (sk-, sess-, bearer, api_key=)
   - Token file (600 on Unix) separate from daemon state
   - JSON secret value scanning

---

**End of Capture**
