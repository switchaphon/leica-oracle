# Hermes Agent Testing Patterns

## 1. Test Structure

**Test suite: 673 Python files across 16 subfolders. Total: ~200K LOC of test code.**

Directory layout:
- `tests/gateway/` (173 files, 66K LOC) — platform adapters (Telegram, Discord, Slack, Matrix, API server)
- `tests/tools/` (149 files, 51K LOC) — tool execution, skill manager, code execution, MCP
- `tests/hermes_cli/` (119 files, 36K LOC) — CLI behaviors, commands, config parsing
- `tests/run_agent/` (55 files, 18K LOC) — agent loop, message handling, context compression
- `tests/agent/` (44 files, 19K LOC) — LLM adapters (Anthropic, OpenAI, Bedrock, etc.)
- `tests/cli/` (44 files, 9K LOC) — older CLI entry points
- `tests/integration/` (8 files) — batch runner, checkpoint resumption, voice channels
- `tests/e2e/` (1 file, +conftest) — full gateway pipeline command dispatch
- `tests/skills/`, `tests/plugins/`, `tests/cron/` — optional integrations

**Test-to-source coverage ratios (LOC test / LOC source):**
- **gateway**: 1.24× (most heavily tested)
- **run_agent**: 1.45× (agent loop critical path)
- **tools**: 1.10× (broad tool coverage)
- **agent**: 0.90× (LLM adapter coverage)
- **hermes_cli**: 0.70× (CLI underdeveloped)
- **skills**: 0.29× (marked as lightly tested)

Undertested: `skills/` directory (only 6 tests for 7K LOC), optional integrations (honcho, daytona, modal).

---

## 2. Test Framework & Runner

**Framework:** pytest 9.0+, pytest-asyncio, pytest-xdist (parallel `-n auto`)

**Configuration** (`pyproject.toml:131-136`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["integration: marks tests requiring external services"]
addopts = "-m 'not integration' -n auto"
```

**CI/CD** (`.github/workflows/tests.yml`):
- Single job runs all unit tests (excluding `integration/`, `e2e/`) on Ubuntu 3.11
- Separate e2e job runs `tests/e2e/` only (marked `@pytest.mark.asyncio`)
- **Python version**: 3.11 only (no 3.12 matrix)
- **Timeout**: 20min for unit tests, 10min for e2e
- **Coverage config**: None (no explicit `.coverage`, no CI report)

**Dependencies:**
- `pytest>=9.0.2,<10`
- `pytest-asyncio>=1.3.0,<2` (async test harness)
- `pytest-xdist>=3.0,<4` (parallel execution)
- No pytest-cov, no coverage thresholds enforced in CI

**Test isolation** (hermetic environment, `conftest.py:192-338`):
- All credential env vars (API keys, tokens, passwords) unset per test
- `HERMES_HOME` redirected to per-test tmpdir (prevents ~/.hermes leakage)
- TZ=UTC, LANG=C.UTF-8, PYTHONHASHSEED=0 (deterministic datetime/locale)
- AWS IMDS disabled (avoids 2s metadata service timeout)
- Plugin singleton reset between tests
- 30-second per-test timeout (SIGALRM on Unix, no-op on Windows)

---

## 3. Mocking & Fixtures Patterns

**LLM mocking strategy:**
- **Custom doubles** (no responses/respx/pytest-httpx). E.g., `restart_test_helpers.py:71-108` manually constructs `GatewayRunner` with:
  - `runner._update_runtime_status = MagicMock()`
  - `runner.hooks.emit = AsyncMock()`
  - `runner.session_store = MagicMock()` with `._entries = {}`
- Mock uses `unittest.mock` (standard library)
- LLM calls are stubbed at the adapter level, not the HTTP layer

**External service stubs:**
- **Telegram**: sys.modules mock (pre-test, `gateway/conftest.py:21-62`) provides fake `ChatType` constants, error classes
- **Discord**: comprehensive sys.modules mock (`gateway/conftest.py:65-142`) covering `discord.Intents`, `discord.app_commands` group/command registration
- **Platform adapters**: `RestartTestAdapter` (base class for Telegram mock) overrides `send()`, `connect()`, `disconnect()`, `get_chat_info()`

**Fixture patterns** (`conftest.py`):
- `_hermetic_environment` (autouse) — environment isolation
- `tmp_dir(tmp_path)` — per-test temp directory
- `mock_config()` — minimal hermes config dict (model, toolsets, terminal backend)
- `_ensure_current_event_loop()` (autouse) — creates event loop for sync tests calling `asyncio.get_event_loop().run_until_complete()`
- `_enforce_test_timeout()` (autouse) — 30s SIGALRM

**Shared fixtures per subsystem:**
- `tests/gateway/conftest.py` — telegram/discord sys.modules mocks
- `tests/run_agent/conftest.py` — 34 lines of undocumented helpers
- `tests/e2e/conftest.py` — 266 lines covering full gateway setup

**Snapshot testing:** NOT used. No pytest-snapshot, no golden files.

---

## 4. What They Test HARD (3 Most-Tested Modules)

### 4a. **gateway/api_server** (1.24× coverage ratio)
Heavy test focus on **OpenAI-compatible API server** multimodal routing.

Example: `tests/gateway/test_api_server.py:55-100` (ResponseStore LRU eviction):
```python
class TestResponseStore:
    def test_lru_eviction(self):
        store = ResponseStore(max_size=3)
        store.put("resp_1", {"output": "one"})
        store.put("resp_2", {"output": "two"})
        store.put("resp_3", {"output": "three"})
        store.put("resp_4", {"output": "four"})
        assert store.get("resp_1") is None  # evicted (least recently used)
        assert store.get("resp_2") is not None
        assert len(store) == 3
```
**Invariant defended**: LRU cache correctness (response chaining via `previous_response_id`).

173 gateway test files defend:
- Session routing across platforms (Telegram, Discord, Slack, Matrix, API server)
- Message queueing during agent busy state
- Approval/deny workflow authorization
- Multi-platform skill registration

### 4b. **tools/** (1.10× coverage)
149 files test **tool execution safety and skill mutation**.

Example: `tests/tools/test_skill_improvements.py:46-68` (fuzzy patch skill):
```python
def test_whitespace_trimmed_match(self):
    skill = "---\nname: ws-skill\n\n    def hello():\n        print(\"hi\")"
    _create_skill("ws-skill", skill)
    # Patch with no leading whitespace (LLM output shape)
    result = _patch_skill("ws-skill", "def hello():\n    print(\"hi\")", 
                          "def hello():\n    print(\"hello world\")")
    assert result["success"] is True
    content = (self.skills_dir / "ws-skill" / "SKILL.md").read_text()
    assert 'print("hello world")' in content
```
**Invariant defended**: Skill mutation is whitespace-agnostic (LLMs produce indentation variance).

Key test areas:
- Skill creation/patching with fuzzy matching (7 test files)
- Code execution modes (POSIX-only, Windows workarounds)
- File sync performance over SSH
- Security: symlink traversal, OSV package checks, hidden directory traversal
- MCP OAuth token refresh and cold-load cache expiry

### 4c. **run_agent** (1.45× coverage)
55 files test **agent loop orchestration and message lifecycle**.

Example: `tests/test_hermes_state.py:24-47` (session CRUD):
```python
def test_end_session_preserves_original_end_reason(self, db):
    """First end_reason wins — compression split must not be overwritten."""
    db.create_session(session_id="s1", source="cli")
    db.end_session("s1", end_reason="compression")
    first_ended_at = db.get_session("s1")["ended_at"]
    
    # Stale CLI holds old session_id and calls end_session() again
    time.sleep(0.01)
    db.end_session("s1", end_reason="resumed_other")
    
    session = db.get_session("s1")
    assert session["end_reason"] == "compression"  # First win, not overwritten
    assert session["ended_at"] == first_ended_at
```
**Invariant defended**: Session end reason is idempotent (prevents re-compression of already-compressed sessions).

Key test areas:
- SessionDB SQLite CRUD, FTS5 search, export
- Message append, tool_call_count increments
- Token count accumulation
- Context compression lifecycle

---

## 5. What They Test LIGHTLY or NOT AT ALL

### **Undertested Areas:**

**Skills auto-creation path**: `tests/skills/` has only 6 tests (telephony, memento cards, YouTube quiz, Google OAuth). **No test for the core create-from-experience path** that the framework markets as "self-improving". Skill fuzzy patching is tested, but not the full discovery→execution→patch→learn loop.

**Gateway multi-platform routing**: 173 gateway tests but **no parametrized routing tests** across >5 platforms. No test verifies message bounces correctly between Telegram→Discord→Matrix with same user. No test for platform fallback if one adapter disconnects.

**RL training pipeline (tinker-atropos)**: Only `tests/tools/test_rl_training_tool.py` (120 LOC) tests file handle cleanup and process termination. **No test for actual RL training, reward signal, policy gradient, or convergence**. The `tinker-atropos/` directory has 0 test files in the main codebase (tinker-atropos is vendored, not tested end-to-end).

Evidence:
- `/tests/skills/` — 6 test files, 2.1K LOC vs 7.2K source LOC (0.29× ratio)
- `/tests/integration/` — no RL training, only batch runner + daytona/modal + voice
- `/tinker-atropos/` — 0 test files (directory exists for inference only)
- `/tests/e2e/` — 1 file, command dispatch only, no skill→agent loop

**CLI parsing**: Only basic smoke tests. No parametrized testing of 400+ CLI flags. No property-based fuzz of config YAML malformations.

**Security testing gaps**:
- No prompt injection tests except `test_cron_prompt_injection.py` (cron-specific)
- No test for tool hallucination (agent asks for non-existent tool)
- No fuzzing of LLM output parsing (malformed JSON responses)
- Only `test_sql_injection.py` (column name + query parameterization)
- Only `test_worktree_security.py` + `test_symlink_prefix_confusion.py` (filesystem only)

---

## 6. Test Quality Signals

### **Integration Tests**
- `tests/integration/` (8 files): batch runner checkpointing, daytona/modal terminal backends, voice channels, web tool interactions
- No end-to-end agent task (e.g., "write code, test, refine" loop)
- No cross-platform skill sharing test (skill created in Telegram, used in Discord)

### **Property-Based Testing**
- **Not used.** No hypothesis. No QuickCheck-style generators.
- All tests use concrete fixtures and exhaustive case enumeration

### **Adversarial/Security Testing**
- **Limited.** Only regression tests, not proactive attack surface:
  - `test_cron_prompt_injection.py` — regex fuzzing for bypass patterns
  - `test_sql_injection.py` — assertion-only (no execution attack, only static checks)
  - `test_tirith_security.py` — Tirith-framework vulnerability scanning (external)
  - `test_worktree_security.py` — no Git command injection test, only symlink escape

### **Time-Sensitive Tests**
- `test_timezone.py` — 15.7K LOC of deterministic timezone/locale edge cases
- `test_hermes_logging.py` — handler lifecycle with mock clock (no freezegun)
- `test_hermes_state.py` — uses `time.sleep(0.01)` for idempotency checks
- No use of freezegun or pytest-freezegun

### **Flaky Test Patches**
- 34 `@pytest.mark.skipif` markers (platform/privilege checks)
- 0 `@pytest.mark.flaky` (no retries configured)
- CI timeout 20min (suggests some slow tests, no flake reporting)

**Flake evidence:**
- `tests/honcho_plugin/test_client.py` — 3 skipif markers (asyncio event loop issues)
- `tests/tools/test_ssh_environment.py` — entire file conditionally skipped if SSH key unavailable
- No recent history of "flaky test: reverted" commits in logs

---

## 7. The Philosophy of Their Test Suite

**What the test suite reveals about trust in stochastic behavior:**

The hermes-agent testing philosophy trades **breadth of LLM output validation** for **depth of system invariants**.

### They Test **Heavily**: 
- **Deterministic system paths** — session lifecycle, message queueing, skill mutation, API routing
- **Mocked LLM calls** — no real inference, only mock adapter responses
- **Configuration binding** — 10K+ LOC of config parsing, default handling, precedence
- **Platform adapters** — mock Telegram/Discord at the Python module level, assert send/receive correctness

### They Don't Test (Implicitly Trust LLM):
- **Tool use correctness** — no assertion that Claude actually uses the web_search tool when asked; only that the tool executes
- **Prompt quality** — no tests that check agent *reasoning*, only that it doesn't crash
- **Context window management** — compression is tested for correctness, but no test validates that it preserves semantic meaning

### Core Assumption:
> **"If the system harness works correctly and the LLM is called with the right tools/prompt, the LLM will do the right thing."**

This is pragmatic for an **agentic framework** — the framework can't predict LLM output, so it tests:
1. **Does the harness handle LLM stochasticity gracefully?** (retry logic, fallback, error classification)
2. **Does the harness correctly isolate bad outputs?** (tool sandbox, skill safety checks, prompt injection blocking)
3. **Do the system components compose correctly?** (adapter → session → agent loop → storage)

**Example of this philosophy in action:**
- `test_hermes_state.py` tests that session IDs survive compression — **NOT** that compression preserves conversation semantics (which only the LLM can judge)
- `tests/gateway/test_api_server.py` tests that `/v1/chat/completions` returns 200 with correct schema — **NOT** that the response is sensible
- `test_skill_improvements.py` tests that patches apply successfully — **NOT** that the patched skill works better than the original (depends on LLM feedback)

The suite is **prescriptive** (system must behave this way) but **not proscriptive** (we don't guard against bad LLM choices). This is the right engineering trade-off for an LLM-based system where the LLM is the source of truth.
