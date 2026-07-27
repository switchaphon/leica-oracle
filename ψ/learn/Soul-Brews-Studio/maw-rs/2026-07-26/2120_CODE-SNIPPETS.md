# maw-rs Code Architecture & Implementation Patterns

**Date**: 2026-07-26  
**Branch**: alpha  
**Purpose**: Representative code samples and architectural patterns from maw-rs (Rust multi-agent orchestration CLI)

---

## 1. CLI Main Entry Point & Command Dispatch

### 1.1 Program Entrypoint (`crates/maw-cli/src/main.rs`)

The main binary uses a two-layer architecture: fast-path tmux attach detection at the binary level, then CLI dispatch through maw-cli library.

```rust
#[tokio::main(flavor = "multi_thread")]
async fn main() {
    let program = std::env::args().next();
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let argv = mawx_shim_argv(program.as_deref(), argv);
    std::process::exit(main_code_async(&argv).await);
}
```

**Key pattern**: Async runtime annotation on `main()` enables async dispatch without explicit runtime construction. `flavor = "multi_thread"` allows concurrent agent operations.

### 1.2 mawx Symlink Shim

maw ships with optional mawx symlink that auto-injects "x" subcommand:

```rust
fn mawx_shim_argv(program: Option<&str>, mut argv: Vec<String>) -> Vec<String> {
    let is_mawx = program.is_some_and(|program| {
        std::path::Path::new(program)
            .file_name()
            .and_then(OsStr::to_str)
            .unwrap_or(program)
            .starts_with("mawx")
    });
    if is_mawx {
        argv.insert(0, "x".to_owned());
    }
    argv
}
```

**Pattern**: `is_some_and()` (Rust 1.70+) chains Option predicate cleanly.

### 1.3 Fast-Path Tmux Attach

Before running the full CLI parser, check if argv is `maw a <session>` to attach directly:

```rust
fn maybe_exec_attach(argv: &[String]) -> Option<i32> {
    let mut client = TmuxClient::local();
    let alive_sessions = client.list_session_names();
    maybe_exec_attach_with(
        argv,
        std::io::stdout().is_terminal(),
        std::env::var_os("TMUX").is_some(),
        &alive_sessions,
        run_tmux_attach,
    )
}
```

**Pattern**: Dependency injection (closures as handlers) makes logic testable without side effects.

### 1.4 CLI Dispatch Router (`crates/maw-cli/src/core_impl/dispatcher.rs`)

Commands route through two dispatch tables: sync and async handlers. This separation allows async transport commands to coexist with sync-only operations.

```rust
enum DispatchTarget {
    Native(NativeHandler),
    AsyncNative(AsyncHandler),
    UnknownCommand,
}

const DISPATCH_01: &[DispatcherEntry] = &[
    DispatcherEntry { command: "--help", handler: Handler::Sync(usage_handler) },
    DispatcherEntry { command: "help", handler: Handler::Sync(usage_handler) },
    DispatcherEntry { command: "discord", handler: Handler::Async(run_discord_async) },
    #[cfg(test)]
    DispatcherEntry { command: "__async-dispatch-test", handler: Handler::Async(run_async_dispatch_test) },
];

fn dispatcher_target(command: &str) -> DispatchTarget {
    dispatcher_entries()
        .find(|entry| entry.command == command)
        .map_or(DispatchTarget::UnknownCommand, |entry| match entry.handler {
            Handler::Sync(handler) => DispatchTarget::Native(handler),
            Handler::Async(handler) => DispatchTarget::AsyncNative(handler),
        })
}
```

**Pattern**: Const dispatch table avoids runtime HashMap allocation. Separate sync/async allows testing both paths.

### 1.5 Run CLI (Synchronous & Async Entry Points)

```rust
pub fn run_cli(argv: &[String]) -> CliOutput {
    let Some(command) = argv.first().map(String::as_str) else {
        return usage_ok();
    };

    match dispatcher_target(command) {
        DispatchTarget::Native(handler) => {
            cli_dispatch_log_command(command, &argv[1..]);
            native_or_plugin_fallback(argv, || handler(&argv[1..]))
        }
        DispatchTarget::AsyncNative(handler) => native_or_plugin_fallback(argv, || {
            run_async_handler_blocking(handler, &argv[1..])
        }),
        DispatchTarget::UnknownCommand => dispatch_cli_plugin_or_unknown(argv, command),
    }
}

pub async fn run_cli_async(argv: &[String]) -> CliOutput {
    let Some(command) = argv.first().map(String::as_str) else {
        return usage_ok();
    };

    match dispatcher_target(command) {
        DispatchTarget::Native(handler) => {
            cli_dispatch_log_command(command, &argv[1..]);
            native_or_plugin_fallback(argv, || handler(&argv[1..]))
        }
        DispatchTarget::AsyncNative(handler) => {
            plugin_fallback_for_native_miss(argv, handler(argv[1..].to_vec()).await)
        }
        DispatchTarget::UnknownCommand => dispatch_cli_plugin_or_unknown(argv, command),
    }
}
```

**Key difference**: `run_cli` blocks on async handlers via `tokio::runtime::Builder`, while `run_cli_async` awaits natively. This allows the CLI to work both in async and sync contexts.

### 1.6 Async Handler Blocking Wrapper

Handles the case where sync commands need to run async logic:

```rust
fn run_async_handler_blocking(handler: AsyncHandler, args: &[String]) -> CliOutput {
    if tokio::runtime::Handle::try_current().is_ok() {
        return CliOutput {
            code: 1,
            stdout: String::new(),
            stderr: "cannot block_on inside runtime; call run_cli_async for async commands\n".to_owned(),
        };
    }

    let runtime = match tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
    {
        Ok(runtime) => runtime,
        Err(error) => {
            return CliOutput {
                code: 1,
                stdout: String::new(),
                stderr: format!("failed to start tokio runtime: {error}\n"),
            };
        }
    };
    runtime.block_on(handler(args.to_vec()))
}
```

**Error handling pattern**: Detects already-running runtime before attempting block_on (which would panic). Returns structured error instead.

---

## 2. Tmux Integration (crates/maw-tmux)

The tmux crate provides testable, deterministic tmux command construction and execution with a pluggable runner interface.

### 2.1 TmuxClient Architecture

```rust
/// Testable tmux client that delegates all execution to [`TmuxRunner`].
pub struct TmuxClient<R> {
    runner: R,
}

impl TmuxClient<CommandTmuxRunner> {
    /// Create a client backed by the local `tmux` binary.
    #[must_use]
    pub fn local() -> Self {
        Self::new(CommandTmuxRunner::new())
    }

    /// Create a client backed by the local `tmux` binary on a specific socket.
    #[must_use]
    pub fn local_with_socket(socket: impl Into<OsString>) -> Self {
        Self::new(CommandTmuxRunner::new().with_socket(socket))
    }
}
```

**Pattern**: Generic `TmuxClient<R>` where `R: TmuxRunner` allows injection of fake/mock runners for testing without live tmux.

### 2.2 Pane-to-Pane Message Sending

The core operation: send text to a remote agent pane with reliability confirmations.

```rust
impl<R> TmuxClient<R>
where
    R: TmuxRunner,
{
    /// Send literal text through `tmux send-keys -l`.
    pub fn send_keys_literal(&mut self, target: &str, text: &str) -> Result<(), TmuxError> {
        self.runner
            .run("send-keys", &tmux_send_keys_literal_args(target, text))
            .map(|_| ())
    }

    /// Send one Enter key through `tmux send-keys`.
    pub fn send_enter(&mut self, target: &str) -> Result<(), TmuxError> {
        self.runner
            .run("send-keys", &tmux_send_enter_args(target))
            .map(|_| ())
    }
}
```

**Pattern**: Separate methods for distinct operations (`send_keys_literal`, `send_enter`) rather than a single parameterized method. Clearer intent, easier to test.

### 2.3 Smart Text Submission with Confirmation

This addresses the user's send-keys reliability problem. Long/multiline text is buffered and pasted instead of sent directly:

```rust
/// Smart text sending: buffer for multiline/long payloads, literal send otherwise, then submit-confirm.
pub fn send_text(&mut self, target: &str, text: &str) -> Result<SendTextReport, TmuxError> {
    self.send_text_with_sleeper(target, text, std::thread::sleep)
}

fn send_text_with_sleeper<F>(
    &mut self,
    target: &str,
    text: &str,
    mut sleep: F,
) -> Result<SendTextReport, TmuxError>
where
    F: FnMut(std::time::Duration),
{
    self.exit_mode_if_needed(target)?;
    let used_buffer = text.contains('\n') || text.len() > 500;
    if used_buffer {
        self.load_buffer(text)?;
        self.paste_buffer(target)?;
    } else {
        self.send_keys_literal(target, text)?;
    }
    sleep(std::time::Duration::from_millis(SEND_SETTLE_MS));
    let (enter_attempts, warned_pending) =
        self.submit_with_confirm(target, text, &mut sleep)?;
    Ok(SendTextReport {
        used_buffer,
        enter_attempts,
        warned_pending,
    })
}
```

**Key constants** (defined at module top):
```rust
pub const SEND_SETTLE_MS: u64 = 1_500;
pub const SUBMIT_CONFIRM_MS: u64 = 700;
pub const SUBMIT_GRACE_MS: u64 = 300;
pub const MAX_SUBMIT_ATTEMPTS: u32 = 4;
const COOLDOWN_MS: u64 = 500;
const QUOTA_PER_MINUTE: u32 = 100;
const QUOTA_WINDOW_MS: u64 = 60_000;
```

**Why buffer?** Direct `send-keys` with newlines can get stuck in buffer in some tmux versions. Buffering works around this:
1. Exit any copy mode first
2. For multiline or >500 char payloads, use `tmux load-buffer` + `paste-buffer`
3. For short single-line, direct `send-keys -l`
4. After each, sleep to allow tmux to process
5. Retry Enter up to 4 times, checking pane state between attempts

### 2.4 Submission Confirmation Loop

```rust
fn submit_with_confirm<F>(
    &mut self,
    target: &str,
    text: &str,
    sleep: &mut F,
) -> Result<(u32, bool), TmuxError>
where
    F: FnMut(std::time::Duration),
{
    for attempt in 1..=MAX_SUBMIT_ATTEMPTS {
        self.send_enter(target)?;
        sleep(std::time::Duration::from_millis(SUBMIT_CONFIRM_MS));
        match self.submit_pending_state_after_grace(target, text, sleep) {
            PendingInputState::Cleared => return Ok((attempt, false)),
            PendingInputState::DifferentInput => return Ok((attempt, true)),
            PendingInputState::MatchesSent => {}
        }
    }
    Ok((MAX_SUBMIT_ATTEMPTS, true))
}

fn submit_pending_state_after_grace<F>(
    &mut self,
    target: &str,
    text: &str,
    sleep: &mut F,
) -> PendingInputState
where
    F: FnMut(std::time::Duration),
{
    let _confirm_state = self.pending_input_state(target, text);
    sleep(std::time::Duration::from_millis(SUBMIT_GRACE_MS));
    self.pending_input_state(target, text)
}
```

**Retries & state checking**: After sending Enter, wait for confirmation. Check the pane's current input line:
- **Cleared**: Shell prompt reappeared → success
- **DifferentInput**: User or other agent typed something else → abort
- **MatchesSent**: Input still shows what we sent → try again

### 2.5 CommandTmuxRunner: Process Adapter

```rust
/// Concrete tmux runner backed by `std::process::Command`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommandTmuxRunner {
    program: OsString,
    socket: Option<OsString>,
}

impl CommandTmuxRunner {
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    #[must_use]
    pub fn with_program(program: impl Into<OsString>) -> Self {
        Self {
            program: program.into(),
            socket: None,
        }
    }

    #[must_use]
    pub fn with_socket(mut self, socket: impl Into<OsString>) -> Self {
        self.socket = Some(socket.into());
        self
    }

    /// Return the exact argv vector this runner will execute.
    #[must_use]
    pub fn argv(&self, subcommand: &str, tmux_args: &[String]) -> Vec<OsString> {
        let mut command_line = vec![self.program.clone()];
        if let Some(socket) = &self.socket {
            command_line.push(OsString::from("-S"));
            command_line.push(socket.clone());
        }
        command_line.push(OsString::from(subcommand));
        command_line.extend(tmux_args.iter().map(OsString::from));
        command_line
    }
}

impl TmuxRunner for CommandTmuxRunner {
    fn run(&mut self, subcommand: &str, args: &[String]) -> Result<String, TmuxError> {
        self.run_command(subcommand, args, None)
    }

    fn run_with_stdin(
        &mut self,
        subcommand: &str,
        args: &[String],
        stdin: &[u8],
    ) -> Result<String, TmuxError> {
        self.run_command(subcommand, args, Some(stdin))
    }
}
```

**Pattern**: Builder-like API with `with_program()`, `with_socket()` for testable configuration.

### 2.6 Subprocess Execution with Error Capture

The critical method that actually runs tmux:

```rust
fn run_command(
    &self,
    subcommand: &str,
    args: &[String],
    stdin: Option<&[u8]>,
) -> Result<String, TmuxError> {
    let command_line = self.argv(subcommand, args);
    let (program, rest) = command_line
        .split_first()
        .expect("tmux command line must include a program because argv inserts it first");
    validate_tmux_program(program)?;
    validate_tmux_option_values(rest)?;
    
    let mut command = Command::new(program);
    command.args(rest);
    command.stdout(Stdio::piped()).stderr(Stdio::piped());
    if stdin.is_some() {
        command.stdin(Stdio::piped());
    }
    
    let mut child = command.spawn().map_err(|error| {
        TmuxError::new(format!(
            "failed to execute {}: {error}",
            program.to_string_lossy()
        ))
    })?;
    
    if let Some(stdin) = stdin {
        let mut child_stdin = child
            .stdin
            .take()
            .ok_or_else(|| TmuxError::new("failed to open tmux stdin"))?;
        child_stdin
            .write_all(stdin)
            .map_err(|error| tmux_program_io_error("write stdin for", program, &error))?;
    }
    
    let output = child
        .wait_with_output()
        .map_err(|error| tmux_program_io_error("collect output from", program, &error))?;
    
    if output.status.success() {
        return Ok(String::from_utf8_lossy(&output.stdout).into_owned());
    }
    
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_owned();
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_owned();
    let detail = if stderr.is_empty() { stdout } else { stderr };
    let code = output
        .status
        .code()
        .map_or_else(|| "signal".to_owned(), |code| code.to_string());
    
    if detail.is_empty() {
        Err(TmuxError::new(format!("tmux exited with status {code}")))
    } else {
        Err(TmuxError::new(format!(
            "tmux exited with status {code}: {detail}"
        )))
    }
}
```

**Key error-handling patterns**:
- Validation before spawn (prevent command injection)
- Capture both stdout & stderr
- Prefer stderr for error messages, fall back to stdout
- Preserve exit code in error message
- Handle signal termination vs. exit code

---

## 3. Transport & Messaging Layer (crates/maw-transport)

### 3.1 Peer-to-Peer Message Bodies

Agents send messages via HTTP. The transport layer constructs JSON bodies for `/api/send` and `/api/wake` endpoints:

```rust
/// Build the exact v26.6.13 `/api/send` JSON body: target, text, and optional inbox.
pub fn peer_send_body(target: &str, text: &str, inbox: Option<bool>) -> Result<String, String> {
    let target = serde_json::to_string(target).map_err(|error| error.to_string())?;
    let text = serde_json::to_string(text).map_err(|error| error.to_string())?;
    Ok(match inbox {
        Some(inbox) => format!(r#"{{"target":{target},"text":{text},"inbox":{inbox}}}"#),
        None => format!(r#"{{"target":{target},"text":{text}}}"#),
    })
}

#[cfg(test)]
mod tests {
    #[test]
    fn peer_send_body_keeps_wire_field_order_and_optional_inbox() {
        assert_eq!(
            peer_send_body("remote-oracle", "E1 signed capture", Some(true)).unwrap(),
            r#"{"target":"remote-oracle","text":"E1 signed capture","inbox":true}"#
        );
        assert_eq!(
            peer_send_body("remote-oracle", "hello", None).unwrap(),
            r#"{"target":"remote-oracle","text":"hello"}"#
        );
    }
}

pub fn peer_wake_body(target: &str, task: Option<&str>) -> Result<String, String> {
    let target = serde_json::to_string(target).map_err(|error| error.to_string())?;
    Ok(match task {
        Some(task) => {
            let task = serde_json::to_string(task).map_err(|error| error.to_string())?;
            format!(r#"{{"target":{target},"task":{task}}}"#)
        }
        None => format!(r#"{{"target":{target}}}"#),
    })
}
```

**Pattern**: Manual JSON construction (not serde) keeps field order deterministic for tests and wire protocol contracts. Tests pin exact wire format.

### 3.2 HttpTransportIo Trait

The async I/O interface that agents use to send:

```rust
impl HttpTransportIo for ReqwestHttpTransportIo {
    fn list_local_sessions(&mut self) -> Result<Vec<TmuxTransportSession>, String> {
        Ok(Vec::new())
    }

    fn get_all_sessions(
        &mut self,
        _local_sessions: &[TmuxTransportSession],
    ) -> Result<Vec<TransportSession>, String> {
        Ok(Vec::new())
    }

    fn send_peer_keys(
        &mut self,
        _source: &str,
        _target: &str,
        _message: &str,
    ) -> Result<bool, String> {
        Err("sync send_peer_keys is not supported by the async reqwest transport".to_owned())
    }

    fn post_peer_feed(
        &mut self,
        _url: &str,
        _method: &str,
        _body: &str,
        _timeout_ms: u64,
    ) -> Result<HttpPostResult, String> {
        Err("sync post_peer_feed is not supported by the async reqwest transport".to_owned())
    }

    fn timeout_for(&self, _transport: &str) -> u64 {
        self.timeout_ms
    }
}
```

**Pattern**: Trait defines both sync and async paths. ReqwestHttpTransportIo explicitly rejects sync methods with clear error messages.

---

## 4. Error Handling Idioms

### 4.1 TmuxError: Simple String-Wrapper

```rust
/// Error returned by an injected tmux runner.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TmuxError {
    pub message: String,
}

impl TmuxError {
    #[must_use]
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

impl fmt::Display for TmuxError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.message)
    }
}

impl Error for TmuxError {}
```

**Rationale**: `String`-based errors allow rich context. No enum variants = no matching on error types, just propagation. Suitable for I/O errors where recovery options are limited.

### 4.2 Result-Based Command Outcome

```rust
/// Outcome from a high-level `maw tmux send` action attempt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TmuxSendCommandOutcome {
    Sent,
    Throttled(SendThrottle),
}

pub fn send_command_to_pane(
    &mut self,
    tracker: &mut TmuxSendTracker,
    resolved: &str,
    command: &str,
    options: &TmuxSendCommandOptions,
    now_ms: u64,
) -> Result<TmuxSendCommandOutcome, TmuxError> {
    if command.is_empty() {
        return Err(TmuxError::new(
            "usage: maw tmux send <target> <command> [--literal] [--allow-destructive] [--force]",
        ));
    }
    match tracker.check(resolved, now_ms, options.force) {
        SendThrottle::Allowed => {}
        throttle => return Ok(TmuxSendCommandOutcome::Throttled(throttle)),
    }

    let destructive = check_destructive(command);
    if destructive.destructive && !options.allow_destructive {
        return Err(TmuxError::new(format!(
            "refusing to send: command matches destructive patterns:\n{}\n  pass --allow-destructive to bypass (review carefully first)",
            destructive
                .reasons
                .iter()
                .map(|reason| format!("  - {reason}"))
                .collect::<Vec<_>>()
                .join("\n")
        )));
    }

    let pane_current_command = self.display_pane_current_command(resolved)?;
    if is_claude_like_pane(Some(&pane_current_command)) && !options.force {
        return Err(TmuxError::new(format!(
            "refusing to send: pane '{resolved}' is running '{pane_current_command}' (claude-like).\n  injecting keys would collide with the AI's turn.\n  pass --force to override (you really want to type into a live claude pane)"
        )));
    }

    self.runner
        .run(
            "send-keys",
            &tmux_send_command_args(resolved, command, options.literal),
        )
        .map(|_| TmuxSendCommandOutcome::Sent)
}
```

**Pattern**: Distinguish between errors (Err) and expected non-error states (Ok). Throttling is not an error; it's an expected outcome.

### 4.3 Exit Mode Error Recovery (Benign vs. Fatal)

```rust
fn exit_mode_if_needed(&mut self, target: &str) -> Result<(), TmuxError> {
    // First attempt to exit copy mode. If tmux says "not in a mode", that's OK.
    match self.runner.run("send-keys", &tmux_exit_copy_mode_args(target)) {
        Ok(_) => Ok(()),
        Err(error) => {
            if error.message.contains("not in a mode") {
                Ok(())
            } else {
                Err(error)
            }
        }
    }
}
```

**Pattern**: Catch specific error conditions (substring match) and demote to success if benign. Propagate unexpected errors as-is.

### 4.4 Command Process Error Wrapping

```rust
fn run_command(...) -> Result<String, TmuxError> {
    // ...
    let output = child
        .wait_with_output()
        .map_err(|error| tmux_program_io_error("collect output from", program, &error))?;
    
    if output.status.success() {
        return Ok(String::from_utf8_lossy(&output.stdout).into_owned());
    }
    
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_owned();
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_owned();
    let detail = if stderr.is_empty() { stdout } else { stderr };
    let code = output
        .status
        .code()
        .map_or_else(|| "signal".to_owned(), |code| code.to_string());
    
    if detail.is_empty() {
        Err(TmuxError::new(format!("tmux exited with status {code}")))
    } else {
        Err(TmuxError::new(format!(
            "tmux exited with status {code}: {detail}"
        )))
    }
}

fn tmux_program_io_error(
    action: &str,
    program: &std::ffi::OsStr,
    error: &std::io::Error,
) -> TmuxError {
    TmuxError::new(format!(
        "failed to {action} {}: {error}",
        program.to_string_lossy()
    ))
}
```

**Layered errors**: I/O errors from process operations get wrapped with context ("failed to write stdin for"). Tmux exit errors include both status code and stderr.

---

## 5. Notable Rust Patterns

### 5.1 Dependency Injection with Generic Traits

TmuxClient works with any `TmuxRunner`:

```rust
pub trait TmuxRunner {
    fn run(&mut self, subcommand: &str, args: &[String]) -> Result<String, TmuxError>;
    fn run_with_stdin(
        &mut self,
        subcommand: &str,
        args: &[String],
        _stdin: &[u8],
    ) -> Result<String, TmuxError> {
        self.run(subcommand, args)
    }
}

pub struct TmuxClient<R: TmuxRunner> {
    runner: R,
}

// Tests inject FakeRunner
let runner = FakeRunner::with_responses(vec![Ok("output"), Err(TmuxError::new("failed"))]);
let mut client = TmuxClient::new(runner);
```

**Benefit**: Testable without live tmux. Production uses `CommandTmuxRunner`, tests use `FakeRunner`.

### 5.2 Builder Pattern with Generic Constructors

```rust
impl TmuxClient<CommandTmuxRunner> {
    #[must_use]
    pub fn local() -> Self {
        Self::new(CommandTmuxRunner::new())
    }

    #[must_use]
    pub fn local_with_socket(socket: impl Into<OsString>) -> Self {
        Self::new(CommandTmuxRunner::new().with_socket(socket))
    }
}

impl CommandTmuxRunner {
    #[must_use]
    pub fn new() -> Self { /* ... */ }

    #[must_use]
    pub fn with_program(program: impl Into<OsString>) -> Self { /* ... */ }

    #[must_use]
    pub fn with_socket(mut self, socket: impl Into<OsString>) -> Self { /* ... */ }
}
```

**Pattern**: Each `with_*` returns Self for chaining. `#[must_use]` warns if builder chain result isn't consumed.

### 5.3 Async/Sync Dual Paths

```rust
pub async fn run_cli_async(argv: &[String]) -> CliOutput {
    match dispatcher_target(command) {
        DispatchTarget::AsyncNative(handler) => {
            plugin_fallback_for_native_miss(argv, handler(argv[1..].to_vec()).await)
        }
        // ...
    }
}

pub fn run_cli(argv: &[String]) -> CliOutput {
    match dispatcher_target(command) {
        DispatchTarget::AsyncNative(handler) => {
            native_or_plugin_fallback(argv, || run_async_handler_blocking(handler, &argv[1..]))
        }
        // ...
    }
}

fn run_async_handler_blocking(handler: AsyncHandler, args: &[String]) -> CliOutput {
    if tokio::runtime::Handle::try_current().is_ok() {
        return CliOutput { code: 1, stderr: "cannot block_on inside runtime\n".to_owned(), .. };
    }
    let runtime = tokio::runtime::Builder::new_multi_thread().build()?;
    runtime.block_on(handler(args.to_vec()))
}
```

**Pattern**: Single dispatch table serves both sync and async callers. Async commands check if runtime exists before block_on.

### 5.4 Type-Level Test Serialization

```rust
#[cfg(test)]
fn cli_dispatch_test_env() -> (std::path::PathBuf, Vec<EnvVarRestore>) {
    let root = std::env::temp_dir().join(format!(
        "maw-rs-dispatch-audit-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map_or(0, |duration| duration.as_nanos())
    ));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(root.join("state").join("maw")).expect("state dir");
    
    let restores = [
        "HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "MAW_STATE_DIR", "MAW_HOME", "MAW_XDG"
    ]
    .into_iter()
    .map(EnvVarRestore::capture)
    .collect::<Vec<_>>();
    
    let home = root.join("home");
    std::env::set_var("HOME", &home);
    (root, restores)
}

#[cfg(test)]
impl Drop for EnvVarRestore {
    fn drop(&mut self) {
        if let Some(value) = self.value.take() {
            std::env::set_var(self.key, value);
        } else {
            std::env::remove_var(self.key);
        }
    }
}
```

**Pattern**: Use RAII (Drop impl) to restore env vars. Tests share a mutex to serialize env mutations. Captures env state at start, restores on panic recovery.

### 5.5 Saturating Arithmetic for Deadline Checks

```rust
if now_ms.saturating_sub(prev.last_ts) < COOLDOWN_MS {
    return SendThrottle::Cooldown { cooldown_ms: COOLDOWN_MS };
}
if now_ms.saturating_sub(prev.window_start) > QUOTA_WINDOW_MS {
    prev.count = 0;
    prev.window_start = now_ms;
}
```

**Pattern**: `saturating_sub` prevents underflow panic if clock skew happens or test clocks go backward. Treats underflow as 0 (diff = 0).

---

## 6. Testing Approach

### 6.1 Fake Runner for Deterministic Tests

```rust
#[cfg(test)]
pub struct FakeRunner {
    responses: VecDeque<Result<&'static str, TmuxError>>,
    calls: Vec<(String, Vec<String>)>,
}

impl FakeRunner {
    pub fn default() -> Self { /* empty responses */ }
    pub fn with_responses(responses: Vec<Result<&'static str, TmuxError>>) -> Self {
        Self {
            responses: responses.into(),
            calls: Vec::new(),
        }
    }
}

impl TmuxRunner for FakeRunner {
    fn run(&mut self, subcommand: &str, args: &[String]) -> Result<String, TmuxError> {
        self.calls.push((subcommand.to_owned(), args.clone()));
        self.responses
            .pop_front()
            .unwrap_or(Err(TmuxError::new("no responses")))
            .map(|s| s.to_owned())
    }
}
```

**Pattern**: Queue responses in FIFO order. Track calls for assertions. Zero allocation except Vec.

### 6.2 Error Path Tests

```rust
#[test]
fn command_runner_process_adapter_handles_success_stdin_and_errors_without_tmux() {
    let mut printf_runner = CommandTmuxRunner::with_program("/usr/bin/printf");
    assert_eq!(
        printf_runner
            .run("hello %s", &["world".to_owned()])
            .expect("printf succeeds"),
        "hello world"
    );

    let mut shell_runner = CommandTmuxRunner::with_program("/bin/sh");
    let error = shell_runner
        .run("-c", &["printf denied >&2; exit 7".to_owned()])
        .expect_err("shell exits non-zero");
    assert_eq!(error.message, "tmux exited with status 7: denied");

    let mut missing_runner = CommandTmuxRunner::with_program("/definitely/not/a/tmux");
    let error = missing_runner
        .run("list-sessions", &[])
        .expect_err("missing program");
    assert!(error.message.contains("failed to execute /definitely/not/a/tmux"));
}
```

**Pattern**: Test each error case: success, non-zero exit with stderr, missing binary. Verify error message format precisely.

### 6.3 Throttle & Cooldown Logic Tests

```rust
#[test]
fn send_action_empty_throttled_and_tmux_lookup_error_paths_are_safe() {
    let mut client = TmuxClient::new(FakeRunner::default());
    let mut tracker = TmuxSendTracker::default();
    let error = client
        .send_command_to_pane(
            &mut tracker,
            "%1",
            "",
            &TmuxSendCommandOptions::default(),
            1_000,
        )
        .expect_err("empty command rejected before tmux lookup");
    assert!(error.message.contains("usage: maw tmux send"));
    assert!(client.runner.calls.is_empty());  // Verify no tmux call made

    // Throttled state: no tmux call
    let mut client = TmuxClient::new(FakeRunner::default());
    let mut tracker = TmuxSendTracker::default();
    tracker.set(
        "%1",
        SendTrackerEntry {
            last_ts: 1_000,
            count: 1,
            window_start: 1_000,
        },
    );
    let outcome = client
        .send_command_to_pane(
            &mut tracker,
            "%1",
            "echo two",
            &TmuxSendCommandOptions::default(),
            1_100,  // Only 100ms elapsed: < COOLDOWN_MS (500)
        )
        .expect("cooldown reported without tmux lookup");
    assert_eq!(
        outcome,
        TmuxSendCommandOutcome::Throttled(SendThrottle::Cooldown { cooldown_ms: 500 })
    );
    assert!(client.runner.calls.is_empty());  // Verify no tmux call
}
```

**Pattern**: Verify early returns don't trigger unnecessary tmux calls. Use FakeRunner with empty responses to catch unintended tmux calls.

### 6.4 Async Dispatch Tests

```rust
#[cfg(test)]
mod async_dispatch_tests {
    use super::{run_cli_async, CliOutput, DispatchKind, dispatcher_status};

    #[tokio::test]
    async fn async_dispatch_entry_runs_on_tokio_runtime() {
        let output = run_cli_async(&args(&["__async-dispatch-test", "one", "two"])).await;

        assert_eq!(
            output,
            CliOutput {
                code: 0,
                stdout: "async:one,two\n".to_owned(),
                stderr: String::new(),
            }
        );
        assert_eq!(
            dispatcher_status("__async-dispatch-test"),
            DispatchKind::Native,
        );
    }
}
```

**Pattern**: `#[tokio::test]` provides runtime context. Test both output and dispatcher status classification.

---

## 7. Workspace Organization

### 7.1 Cargo.toml (Workspace)

```toml
[workspace]
members = [
    "crates/maw-matcher",
    "crates/maw-worktree",
    "crates/maw-transport",
    "crates/maw-schedule",
    "crates/maw-schedule-launchd",
    "crates/maw-schedule-runner",
    "crates/maw-tmux",
    "crates/maw-peer",
    "crates/maw-auth",
    "crates/maw-xdg",
    "crates/maw-plugin-manifest",
    "crates/maw-cli",
    "crates/maw-discord"
]
resolver = "2"

[workspace.dependencies]
tokio = { version = "1", features = ["rt-multi-thread", "macros", "sync", "time", "signal"] }

[workspace.lints.rust]
unsafe_code = "forbid"

[workspace.lints.clippy]
pedantic = { level = "warn", priority = -1 }
unwrap_used = "warn"
expect_used = "warn"
```

**Key choices**:
- Single **tokio** dependency shared across all crates (rt-multi-thread, macros for #[tokio::test])
- **forbid unsafe_code**: No unsafe blocks, crate stays pure Rust
- **pedantic lints** warn-by-default: Encourages idiomatic code patterns
- **unwrap/expect_used**: Forces explicit error handling except in clearly benign code (like test setup)

---

## 8. Summary Table: Key Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Fast-path attach** | main.rs | Avoid full CLI parse for common `maw a <session>` |
| **Dispatch table** | dispatcher.rs | Route to sync/async handlers via const lookup |
| **Generic TmuxClient<R>** | tmux/types.rs | Inject test runners without live tmux |
| **Smart send_text** | tmux/send.rs | Buffer + paste for reliability on unreliable send-keys |
| **Submission retries** | tmux/send.rs | Confirm Enter sent by polling pane state up to 4× |
| **String-based TmuxError** | tmux/types.rs | Simple error model; rich context in message |
| **Benign error recovery** | tmux/send.rs | Catch "not in a mode" as success, propagate others |
| **Saturating arithmetic** | tmux/types.rs | Prevent underflow panic on clock skew |
| **RAII EnvVarRestore** | dispatcher.rs | Restore test env on panic via Drop impl |
| **Fake runner in tests** | tmux tests | Deterministic test harness without live tmux |
| **Async dual paths** | dispatcher.rs | Support both sync and async command invocation |
| **Tokio multi-thread** | main.rs, Cargo.toml | Enable concurrent agent operations |

---

## 9. Key Takeaways for Reliability

1. **Tmux send-keys reliability** (the user's concern):
   - Long payloads → buffer + paste (workaround for tmux buffer issues)
   - Always exit copy mode first
   - Retry Enter up to 4 times
   - Confirm submission by polling pane state
   - Sleep between operations (1.5s settle, 700ms confirm)

2. **Error handling philosophy**:
   - Errors are values (enum outcomes, not just Err)
   - Catch specific error conditions (substring match) to demote benign failures
   - Wrap I/O errors with context
   - Avoid panicking on underflow (saturating_sub)

3. **Testing strategy**:
   - Inject test runners via generic trait bounds
   - Serialize env access in multi-threaded tests via mutex + RAII
   - Test error paths explicitly (missing binary, non-zero exit, empty output)
   - Verify no unintended tmux calls via fake runner call tracking

4. **Async/Sync coexistence**:
   - Single dispatch table serves both
   - Detect already-running runtime before block_on
   - Fail fast with clear error if nested
   - `run_cli_async` for true async, `run_cli` for sync fallback

