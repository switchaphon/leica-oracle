# Hermes Agent — API Surface Document

**Project:** NousResearch/hermes-agent  
**Date:** 2026-04-20  
**Scope:** Integration surfaces for external systems communicating with Hermes

This document catalogs the points where external systems can integrate with Hermes Agent: CLI commands, MCP server/client modes, ACP (Agent Client Protocol), messaging platforms, plugins, tools, skills, webhooks, cron, and Python embedding.

---

## 1. CLI Public Surface

**Entry point:** `hermes` command (alias: `python cli.py` or direct module invocation)  
**Parser setup:** `hermes_cli/main.py` lines 6335–7820 (argparse subparsers)  
**Command execution callbacks:** `hermes_cli/main.py` lines 1021–6272 (`cmd_*` functions)

### Major Command Groups

#### Chat & Sessions
- `hermes` → Interactive REPL (default; no subcommand)
- `hermes chat` → Direct chat query (`-q`, `--prompt`)
- `hermes sessions list` → List recent sessions
- `hermes sessions export` → Export session history (JSON/markdown)
- `hermes sessions delete <session_id>` → Remove a session
- `hermes sessions prune` → Delete old sessions (`--source`, `--days`)

#### Model & Auth
- `hermes model [provider:model]` → Switch active model
- `hermes login <provider>` → Authenticate to external services (`--scope`)
- `hermes logout <provider>` → Remove stored credentials
- `hermes auth add` → Pool credentials (`--label`, `--portal-url`, `--inference-url`)
- `hermes auth list` → List pooled credentials
- `hermes auth remove <provider>` → Remove pooled credential

#### Gateway & Messaging Platforms
- `hermes gateway run` → Start messaging gateway (Telegram, Discord, Slack, etc.)
- `hermes gateway start` → Start as background service
- `hermes gateway stop` → Stop background service
- `hermes gateway status` → Check platform health (`--deep`)
- `hermes gateway setup` → Interactive platform configuration wizard
- `hermes setup` → Full system setup wizard

#### Skills & Toolsets
- `hermes tools` → Configure enabled tools
- `hermes skills browse` → Browse Skills Hub (categories, filters)
- `hermes skills search <query>` → Search for skills (`--limit`)
- `hermes skills install <identifier>` → Install a skill from registry
- `hermes skills list` → Show installed skills
- `hermes skills tap` → Manage skill sources (GitHub repos)

#### Plugins
- `hermes plugins install <url|name>` → Add a plugin
- `hermes plugins list` → Show installed plugins
- `hermes plugins enable <name>` → Activate a plugin
- `hermes plugins disable <name>` → Deactivate a plugin
- `hermes plugins remove <name>` → Uninstall a plugin

#### Memory & Context
- `hermes memory` → View and manage persistent memory (`--export`, `--import`)

#### Scheduled Tasks
- `hermes cron list` → List all scheduled jobs (`--all` for disabled)
- `hermes cron create` → Add a new scheduled task (`--name`, `--deliver`)
- `hermes cron edit <job_id>` → Modify schedule or prompt
- `hermes cron pause <job_id>` → Suspend a job
- `hermes cron resume <job_id>` → Resume a paused job
- `hermes cron run <job_id>` → Trigger immediately
- `hermes cron remove <job_id>` → Delete a job

#### Webhooks
- `hermes webhook subscribe <name>` → Register webhook route (`--channel`, `--description`)
- `hermes webhook list` → Show active subscriptions
- `hermes webhook remove <name>` → Unsubscribe
- `hermes webhook test <name>` → Send test payload

#### MCP Integration
- `hermes mcp add <name>` → Register MCP server (`--command`, `--url`, `--auth`)
- `hermes mcp list` → Show configured servers
- `hermes mcp test <name>` → Verify connectivity
- `hermes mcp remove <name>` → Deregister server

#### System Commands
- `hermes config set <key> [value]` → Set config option
- `hermes config show` → Display current config
- `hermes config migrate` → Upgrade config schema
- `hermes status` → Show agent health
- `hermes doctor` → Diagnose issues (dependencies, config, auth)
- `hermes version` → Display version info
- `hermes update` → Upgrade to latest release
- `hermes backup` → Create encrypted backup archive
- `hermes import <zipfile>` → Restore from backup

---

## 2. MCP Server Mode

**Hermes as MCP server** — exports tools to external MCP clients.  
**Entry:** `hermes mcp serve` (planned; currently tools exposed via ACP only)  
**Module:** `tools/mcp_tool.py` (currently MCP *client* only; server mode being added)

### Current State: MCP Client Only

Hermes consumes external MCP servers via the config:

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    timeout: 120
  github:
    url: "https://mcp-server.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

**Client code:** `tools/mcp_tool.py` lines 1–300 (connection + discovery)

- Stdio transport: `command` + `args` (spawn subprocess)
- HTTP/StreamableHTTP: `url` + optional `headers` and auth
- Tool discovery: MCP `ListTools` → agent registry injection with namespace prefix
- Authentication: `oauth` and `header` modes for paid MCP endpoints
- Sampling: MCP servers can request LLM completions back to Hermes (configurable limits)

**MCP Configuration:** `hermes_cli/mcp_config.py` lines 1–400 (parsing, validation, auth setup)

---

## 3. MCP Client Mode

**Config file:** `~/.hermes/config.yaml` → `mcp_servers` section  
**Client implementation:** `tools/mcp_tool.py` lines 100–600 (async client loop)

### Authentication Methods

1. **OAuth** (`--auth oauth`)
   - Redirects to provider OAuth endpoint
   - Stores refresh token in `~/.hermes/secrets/mcp-<name>.json`
   - Automatic token refresh before expiration

2. **Header-based** (`--auth header`)
   - Static bearer token or custom header in request
   - Stored in config or env var (e.g., `MCP_<NAME>_TOKEN`)

3. **Environment variables** (default)
   - Resolved from shell env; no persistent storage
   - Suitable for ephemeral containers

### Tool Namespacing

MCP tools are prefixed with their server name:

- Server `github` with tool `search_issues` → `github:search_issues` (internal)
- Display name: "Search Issues (github)" in UI

**Namespace collision resolution:** Last-registered server wins (reload order: bundled → user → config)

---

## 4. ACP (Agent Client Protocol) Server

**Purpose:** Editor integration (VS Code, Zed, JetBrains, Cursor, Windsurf)  
**Server code:** `acp_adapter/server.py` (full ACP 0.9.0 spec)  
**Lifecycle entry:** `acp_adapter/entry.py` (server startup)

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| `HermesACPAgent` | `acp_adapter/server.py:95` | Main ACP agent class (subclass of `acp.Agent`) |
| `SessionManager` | `acp_adapter/session.py` | Manages editor session state, tool calls, streaming |
| `MessageHandler` | `acp_adapter/events.py` | Converts agent events → ACP protocol messages |
| Permissions | `acp_adapter/permissions.py` | Command approval callback (approval workflow) |

### ACP Messages Handled

- `initialize()` → Returns agent capabilities (models, tools, MCP servers)
- `new_session()` → Create new chat session
- `load_session(session_id)` → Restore saved conversation
- `fork_session()` → Branch conversation
- `send(session_id, prompt, mode)` → Process user query (`mode` = `chat`, `task`, `architect`)
- `set_session_model()` → Switch LLM mid-session
- `set_session_config_option()` → Update session settings
- `cancel_task()` → Interrupt current work
- `list_sessions()` → Browse saved chats
- `/slash` commands → Exposed via `_SLASH_COMMANDS` dict (`/help`, `/model`, `/memory`, `/tools`)

### Streaming Protocol

Agent responses stream as protocol events:
- `message_chunk` — LLM text tokens (progressive rendering)
- `tool_call_start` / `tool_call_complete` — Tool execution events
- `step_complete` — Full turn finished
- `usage` — Token count + cost estimate

---

## 5. Gateway: Messaging Platform Adapters

**Base class:** `gateway/platforms/base.py` line 887 (`BasePlatformAdapter`)  
**Directory:** `gateway/platforms/` (27 adapters)  
**Factory:** `gateway/run.py` (`_create_adapter()`)  
**Config:** `~/.hermes/config.yaml` → `platforms` section

### Supported Platforms (15+)

| Platform | File | Status |
|----------|------|--------|
| Telegram | `telegram.py` | Full support (groups, channels, PM, media) |
| Discord | `discord.py` | Full (threads, slash commands, reactions) |
| Slack | `slack.py` | Full (threads, message updates, blocks) |
| WhatsApp | `whatsapp.py` | Full (via WhatsApp Business API) |
| Signal | `signal.py` | Full (via signald daemon) |
| Weixin (WeChat) | `weixin.py` | Full (groups, official accounts, mini programs) |
| WeChat Enterprise | `wecom.py` | Full (message callbacks, approvals) |
| Feishu (Lark) | `feishu.py` | Full (doc creation, file management) |
| DingTalk | `dingtalk.py` | Full (robot messages, card interaction) |
| Mattermost | `mattermost.py` | Full (self-hosted Slack alternative) |
| Matrix | `matrix.py` | Full (Synapse homeserver) |
| QQ Bot | `qqbot/` | Full (QQ groups and DMs) |
| Email | `email.py` | Limited (inbound IMAP) |
| SMS | `sms.py` | Limited (Twilio provider) |
| Home Assistant | `homeassistant.py` | Limited (notification delivery only) |
| Webhook | `webhook.py` | Generic HTTP POST subscriptions |
| BlueBubbles | `bluebubbles.py` | iMessage relay from macOS |

### Required Methods (All Adapters)

```python
class BasePlatformAdapter(ABC):
    def __init__(self, config: PlatformConfig, platform: Platform):
        """Parse config, initialize state."""
    
    async def connect(self) -> bool:
        """Establish connection. Return True on success."""
    
    async def disconnect(self) -> None:
        """Stop listeners, close connections."""
    
    async def send(self, chat_id: str, text: str, **opts) -> SendResult:
        """Send text message. Return success/failure + message_id."""
    
    async def send_typing(self, chat_id: str) -> None:
        """Send typing indicator (ephemeral)."""
    
    async def send_image(self, chat_id: str, url: str, caption: str) -> SendResult:
        """Send image from URL."""
    
    async def get_chat_info(self, chat_id: str) -> dict:
        """Return {name, type, chat_id, members...}."""
    
    async def handle_message(self, event: MessageEvent) -> None:
        """Process inbound message (called by adapter internally)."""
```

### Optional Methods

- `send_document(chat_id, file_path, caption)` — File attachment
- `send_voice(chat_id, file_path)` — Audio message
- `send_video(chat_id, file_path, caption)` — Video
- `send_animation(chat_id, file_path, caption)` — GIF/animation
- `send_image_file(chat_id, file_path, caption)` — Local image

### Adding a New Platform

See `gateway/platforms/ADDING_A_PLATFORM.md` (8,826 bytes). Key steps:

1. **Create adapter** → `gateway/platforms/<platform>.py`, subclass `BasePlatformAdapter`
2. **Add enum** → `gateway/config.py`, extend `Platform` enum
3. **Register in factory** → `gateway/run.py`, add case in `_create_adapter()`
4. **Add auth map** → `gateway/run.py`, if using custom auth (OAuth, tokens)
5. **Add CLI setup** → `hermes_cli/main.py`, subcommand for platform-specific config
6. **Implement message routing** → Use `self.build_source()` for session keys
7. **Handle media** → Use `cache_image_from_bytes()`, `cache_audio_from_bytes()` for attachments
8. **Logging** → Redact secrets in all log output

---

## 6. Plugin System

**Plugin storage:** `~/.hermes/plugins/<name>/` (user), `<repo>/plugins/<name>/` (bundled)  
**Manifest:** Each plugin requires `plugin.yaml` + `__init__.py`  
**Discovery:** `hermes_cli/plugins.py` lines 1–300  
**Hook execution:** `hermes_cli/plugins.py` lines 400–600 (`invoke_hook()`)

### Plugin Manifest (`plugin.yaml`)

```yaml
name: my-plugin
version: 1.0.0
description: What this plugin does
author: Your Name
requires_env:
  - SOME_API_KEY
  - secret_token: "OPTIONAL_SECRET"
provides_tools:
  - custom_tool_name
provides_hooks:
  - pre_llm_call
  - post_tool_call
```

### Plugin Entry Point (`__init__.py`)

```python
def register(ctx: PluginContext):
    """Called once during plugin load."""
    ctx.register_tool(my_tool)
    ctx.on("pre_llm_call", my_hook_handler)
```

### Valid Hooks

| Hook | Fired When | Signature |
|------|-----------|-----------|
| `pre_tool_call` | Before tool execution | `(tool_name, args, **kwargs)` |
| `post_tool_call` | After tool returns | `(tool_name, result, **kwargs)` |
| `transform_tool_result` | Transform tool output | `(result: str) -> str` |
| `pre_llm_call` | Before model inference | `(messages, model, **kwargs)` |
| `post_llm_call` | After model response | `(response, **kwargs)` |
| `transform_terminal_output` | Reformat terminal output | `(output: str) -> str` |
| `pre_api_request` | Before HTTP request | `(method, url, **kwargs)` |
| `post_api_request` | After HTTP response | `(response, **kwargs)` |
| `on_session_start` | Session begins | `(session_id, **kwargs)` |
| `on_session_end` | Session closes | `(session_id, **kwargs)` |
| `on_session_finalize` | Before persistence | `(session_id, messages, **kwargs)` |
| `on_session_reset` | Clear session | `(session_id, **kwargs)` |

### Plugin Loading

1. Bundled plugins (`<repo>/plugins/*/`) + excluded subdirs (`memory/`, `context_engine/`)
2. User plugins (`~/.hermes/plugins/*/`)
3. Project plugins (`./.hermes/plugins/*/`, opt-in via `HERMES_ENABLE_PROJECT_PLUGINS`)
4. Pip entry-point plugins (exposed via `hermes_agent.plugins` entry group)

Later sources override earlier ones (name collisions).

---

## 7. Tool & Toolset Interface

**Tool registry:** `tools/` directory (40+ built-in tools)  
**Tool schema:** Pydantic models + docstring introspection  
**Discovery:** `hermes_cli/tools_config.py` (registry enumeration)

### Standard Tool Pattern

```python
# In tools/custom_tool.py
from typing import Annotated
from pydantic import BaseModel, Field

class CustomToolInput(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(10, description="Max results")

def custom_tool(input: Annotated[CustomToolInput, "Tool name"]) -> str:
    """Tool description.
    
    Long description for system prompt (markdown).
    """
    # implementation
    return result
```

### Tool Schema Generation

1. **Docstring parsing** → Extract description
2. **Type hints** → Build JSON Schema from Pydantic models
3. **Field descriptions** → Pulled from `Field(..., description=...)`
4. **Registry injection** → Tool available as both:
   - Built-in (direct function call)
   - MCP-prefixed (if exposed via server mode)
   - Plugin-registered (dynamic at runtime)

### Built-in Toolsets

| Toolset | Tools | Enabled By Default |
|---------|-------|-------------------|
| `web` | web_search, web_tools, browser | Yes |
| `terminal` | bash, python, code_execution | Conditional (sandbox) |
| `files` | file_operations, file_tools | Yes |
| `vision` | image_analysis, screenshot | Conditional (vision models) |
| `audio` | tts, speech_recognition | Conditional (audio hardware) |
| `image_gen` | image_generation | Conditional (API keys) |
| `code` | git_tools, github_tools | Conditional (auth) |

---

## 8. Skill Interface

**Skill storage:** `~/.hermes/skills/<category>/<skill-name>/` (user), `<repo>/skills/` (bundled)  
**Manifest:** `SKILL.md` (frontmatter + markdown)  
**Discovery:** `hermes_cli/skills_hub.py` (hub + local detection)

### SKILL.md Frontmatter

```yaml
---
name: skill-identifier
description: One-line summary
version: 1.0.0
author: Author Name
license: MIT
metadata:
  hermes:
    tags: [python, deployment, ci-cd]
    related_skills: [other-skill-id, ...]
    requires: [python-3.11, docker]
    cost: "high"  # or "medium", "low", "free"
---
```

### Skill Loading Modes

1. **Pre-armed** — Bundled + user skills loaded at startup (in system prompt)
2. **Lazy-loaded** — Hub skills loaded on-demand (`/skill-name` command)
3. **Indexed** — FTS search across all available skills (local + Hub)

### Skill Categories (Standard Convention)

```
skills/
├── github/
│   ├── github-auth/
│   ├── github-pr-workflow/
│   ├── github-code-review/
│   └── github-issues/
├── productivity/
│   ├── calendar-integration/
│   ├── task-automation/
│   └── email-management/
├── research/
│   ├── arxiv-search/
│   └── literature-summary/
└── ...
```

### Skill Interaction

Users invoke skills via:
- `/skill-name` — Load and execute skill
- `/skills` — Browse available skills
- `/skills search <query>` — FTS search
- Auto-loading when agent detects task matches skill domain

---

## 9. Webhook Subscriptions & Cron Scheduling

### Webhook Subscriptions

**Storage:** `~/.hermes/webhook_subscriptions.json`  
**Config:** `hermes_cli/webhook.py` lines 1–200  
**Platform adapter:** `gateway/platforms/webhook.py` (HTTP listener)

```bash
hermes webhook subscribe my-github-events \
  --channel telegram:123456 \
  --description "GitHub push notifications"
```

Subscription object:
```json
{
  "name": "my-github-events",
  "channel": "telegram:123456",
  "route": "/webhooks/my-github-events",
  "secret": "hmac-secret-auto-generated",
  "description": "GitHub push notifications",
  "created_at": "2026-04-20T...",
  "last_received": "2026-04-20T..."
}
```

**Delivery:** Hot-reloaded without gateway restart; webhook platform listens on `host:port`.

### Cron Scheduling

**Storage:** `~/.hermes/cron/jobs.json`  
**Scheduler daemon:** `cron/scheduler.py` (background process)  
**CLI interface:** `hermes_cli/cron.py` + `cron/jobs.py`

```bash
hermes cron create \
  --schedule "0 9 * * *" \
  --prompt "Generate daily standup report" \
  --deliver slack:#reports
```

Job object:
```json
{
  "id": "job-uuid",
  "name": "daily-standup",
  "schedule": {"type": "cron", "value": "0 9 * * *"},
  "prompt": "Generate daily standup report",
  "deliver": ["slack:#reports", "local"],
  "enabled": true,
  "skills": ["productivity/task-summary"],
  "script": null,
  "next_run_at": "2026-04-21T09:00:00Z",
  "last_run_at": "2026-04-20T09:00:00Z",
  "last_status": "success",
  "repeat": {"times": null, "completed": 0}
}
```

**Delivery modes:**
- `local` — Message to agent home chat (CLI or primary messaging platform)
- `<platform>:<channel>` — Route to specific platform/group
- `email:<recipient>` — Email delivery
- `webhook:<url>` — POST result to external webhook

---

## 10. Python API for Embedding

**Status:** Hermes is primarily a CLI tool; Python embedding is **unsupported** in the public API.

### Partial Python Access (Internal Use Only)

The codebase contains internal Python modules that *could* be imported:

```python
# Not officially supported; API may change between versions
from acp_adapter.session import SessionManager
from agent.anthropic_adapter import AnthropicAdapter  # or other model adapters
from gateway.platforms.base import BasePlatformAdapter
from hermes_cli.config import load_config
```

### Recommended Path (Official)

For embedding Hermes in Python applications:

1. **Use ACP client library** (if available)
   - Connect to running Hermes ACP server
   - Send prompts via protocol
   - Receive streamed responses

2. **Subprocess mode**
   ```python
   import subprocess
   import json
   
   result = subprocess.run(
       ["hermes", "chat", "-q", "your prompt"],
       capture_output=True, text=True
   )
   # parse stdout
   ```

3. **Webhook callback**
   - Have cron or gateway POST results to your API
   - Query Hermes via HTTP (webhook subscriber)

---

## Summary of Integration Points

| Integration | Type | Entry Point | Config |
|-----------|------|-----------|--------|
| CLI | Commands | `hermes <cmd>` | `hermes_cli/main.py` |
| MCP Client | Protocol | `mcp_servers` in config.yaml | `hermes_cli/mcp_config.py` |
| ACP Server | Protocol | Editor → localhost:5000 | `acp_adapter/` |
| Gateway | Messaging | `hermes gateway run` | `~/.hermes/config.yaml` → `platforms` |
| Plugins | System | `~/.hermes/plugins/<name>/` | `plugin.yaml` + `__init__.py` |
| Tools | Functions | `tools/` directory | `tools/` + toolset config |
| Skills | Docs | `~/.hermes/skills/` | `SKILL.md` frontmatter |
| Webhooks | HTTP | `/webhooks/<name>` | `webhook_subscriptions.json` |
| Cron | Scheduling | `hermes cron ...` | `~/.hermes/cron/jobs.json` |

---

**Document compiled:** 2026-04-20 (Saturday)  
**Scope:** Medium thoroughness — covers all major integration surfaces with file:line citations for implementation details.
