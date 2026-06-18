# Pi Agent Harness — Deep Learning Overview

**Date**: 2026-06-17  
**Source**: https://github.com/earendil-works/pi  
**Version**: 0.79.6

---

## 1. What is Pi?

Pi is a **minimal, extensible terminal coding agent harness** built in TypeScript. It gives an LLM (Claude, GPT-4, etc.) four core tools (read, write, edit, bash) and lets you add capabilities through TypeScript extensions, skills, themes, and prompt templates — without forking. The agent stays interactive: you can steer it mid-execution, queue follow-up messages, branch sessions, and compact long conversations.

---

## 2. Directory Structure

```
pi/
├── packages/
│   ├── tui/              # Terminal UI library (differential rendering, components)
│   ├── ai/               # Unified LLM API (OpenAI, Anthropic, Google, etc.)
│   ├── agent/            # Agent runtime (state, tool calling, transport abstraction)
│   └── coding-agent/     # Interactive CLI + SDK (the main application)
├── scripts/              # Build, publish, release, profiling
├── .pi/                  # Pi's own config (extensions, prompts, skills)
└── docs/                 # Architecture, contributing, etc.
```

### Key Packages

| Package | Purpose |
|---------|---------|
| **@earendil-works/pi-tui** | Minimal TUI framework with differential rendering (no dependencies except `chalk`, `marked`) |
| **@earendil-works/pi-ai** | Multi-provider LLM abstraction (OpenAI, Anthropic, Google, Bedrock, Mistral, Groq, etc.) |
| **@earendil-works/pi-agent-core** | Agent state machine, tool execution, message transport |
| **@earendil-works/pi-coding-agent** | Full CLI with session management, extensions, skills, themes |

---

## 3. Installation & Basic Usage

### Install

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
# or via curl
curl -fsSL https://pi.dev/install.sh | sh
```

### Authenticate

```bash
export ANTHROPIC_API_KEY=sk-ant-...
pi
```

Or via OAuth:

```bash
pi
/login  # Select provider
```

### Basic Example

```bash
# Interactive mode (default)
pi "List all .ts files in src/"

# Non-interactive print mode
pi -p "Summarize this codebase"

# With a specific model
pi --model claude-opus "Help me refactor this"

# Continue from a past session
pi -c
```

---

## 4. Project Architecture

### High-Level Flow

```
User Input (Terminal)
    ↓
TUI (Differential Rendering)
    ↓
Interactive CLI (coding-agent)
    ↓
Agent Runtime (pi-agent-core)
    ↓
Tool Execution (read/write/edit/bash) + Extensions
    ↓
LLM API (pi-ai) → Provider (OpenAI, Anthropic, etc.)
    ↓
Response → Rendering
```

### Core Layers

#### 1. **TUI (Terminal User Interface)** — `packages/tui/`

**What**: Minimal differential-rendering TUI framework  
**Dependencies**: `chalk` (colors), `marked` (markdown parsing), `get-east-asian-width` (ANSI width)  
**Key Features**:
- Three-strategy rendering: first render → full screen → incremental updates
- Synchronized output (CSI 2026 for atomic updates, no flicker)
- Built-in components: `Text`, `Input`, `Editor`, `Markdown`, `SelectList`, `Loader`, `Image`, `Box`, `Container`
- Overlay system (dialogs, menus, modals)
- Focusable interface for IME support (Chinese, Japanese, Korean input)
- File/path autocomplete in `Editor`

**Key File**: `src/tui.ts` (1500+ lines, TUI class manages all rendering/input)

**How to extend**: Create a custom `Component` that implements:
```typescript
interface Component {
  render(width: number): string[];  // Return lines ≤ width
  handleInput?(data: string): void; // Process keyboard input
  invalidate?(): void;              // Clear cached state
}
```

#### 2. **AI (LLM Abstraction)** — `packages/ai/`

**What**: Unified multi-provider LLM API  
**Providers Supported**:
- Subscriptions: Anthropic Claude Pro/Max, OpenAI ChatGPT Plus/Pro, GitHub Copilot
- API Keys: Anthropic, OpenAI, Azure, Google Gemini, Vertex, Bedrock, Mistral, Groq, Cerebras, DeepSeek, NVIDIA NIM, xAI, OpenRouter, Cloudflare, Vercel, and 10+ more

**Key Exports**:
- Model discovery (auto-updated per release)
- Provider configuration via `models.json` or extensions
- OAuth support for subscriptions

#### 3. **Agent Core** — `packages/agent/`

**What**: Agent state machine, message handling, tool execution  
**Key Concepts**:
- Transport-agnostic (SSE, WebSocket, HTTP polling)
- State stored as JSONL with parent/child IDs (enables branching)
- Tool registry + execution pipeline
- Message queue (steering vs. follow-up)
- Session compaction (summarize old messages to preserve context)

#### 4. **Coding Agent (Interactive CLI)** — `packages/coding-agent/`

**What**: Full interactive terminal app + SDK  
**Modes**:
- **Interactive**: Default (TUI, user can steer agent mid-execution)
- **Print** (`-p`): Non-interactive, output once and exit
- **JSON** (`--mode json`): Emit all events as JSONL
- **RPC** (`--mode rpc`): Process integration (stdin/stdout JSONL)

**Key Components**:
- Session manager (JSONL files in `~/.pi/agent/sessions/`)
- Settings manager (`settings.json` — global + project-local)
- Extension loader (discover from `~/.pi/agent/extensions/`, `.pi/extensions/`, npm, git)
- Skill loader (follow Agent Skills standard)
- Prompt template expansion
- Theme system (dark/light built-in, custom JSON themes)
- Project trust system (verify before loading project-local resources)
- Built-in tools: `read`, `write`, `edit`, `bash`, `grep`, `find`, `ls`

---

## 5. Key Patterns

### Sessions & Branching

Sessions are stored as **JSONL** files (`~/.pi/agent/sessions/`) with a tree structure:

```json
{"id":"msg-1","parentId":null,"role":"user","content":"..."}
{"id":"msg-2","parentId":"msg-1","role":"assistant","..."}
{"id":"msg-3","parentId":"msg-1","role":"user","content":"..."}
```

Each entry has `id` and `parentId`, enabling **in-place branching** without creating new files.

**Commands**:
- `/tree` — Navigate session tree, switch branches, label bookmarks
- `/fork` — Create new session file from a previous user message
- `/clone` — Copy current branch to new session
- `--fork <path|id>` — Fork from CLI

### Compaction

Long sessions can exhaust context. Compaction **lossy-summarizes older messages** while keeping recent ones.

```bash
/compact                    # Manual compaction
/compact <custom-prompt>    # Custom instructions for summarization
```

The full history remains in the JSONL file; use `/tree` to revisit.

### Message Queue

Submit messages while agent is working:

```
Enter           → Queue steering message (delivered after current turn finishes)
Alt+Enter       → Queue follow-up message (delivered after agent finishes all work)
Escape          → Abort + restore queued messages to editor
Alt+Up          → Retrieve queued messages back to editor
```

---

## 6. TUI Architecture Deep Dive

### How the TUI is Built

The TUI is **framework-agnostic** — it's just a simple component system:

```typescript
class TUI extends Container {
  addChild(component: Component): void;
  removeChild(component: Component): void;
  setFocus(component: Component): void;
  start(): void;
  stop(): void;
  requestRender(): void;
  showOverlay(component, options?): OverlayHandle;
}
```

**Key implementation details**:

1. **Differential Rendering** (3 strategies in `tui.ts`):
   - **First render**: Output all lines, no scrollback clear
   - **Width changed or change above viewport**: Clear screen, full re-render
   - **Normal update**: Move to first changed line, clear to end, render deltas

2. **Synchronized Output** (CSI 2026):
   ```
   \x1b[?2026h  ← Start atomicity
   <render>
   \x1b[?2026l  ← End atomicity (flicker-free)
   ```

3. **ANSI Handling**:
   - `visibleWidth()` — Calc display width ignoring ANSI codes
   - `truncateToWidth()` — Truncate string, preserve ANSI, add ellipsis
   - `wrapTextWithAnsi()` — Wrap text, preserve styles across lines

4. **Hardware Cursor Positioning** (IME support):
   - Focusable components set `CURSOR_MARKER` in rendered output
   - TUI scans output, positions real cursor for IME candidate window

**Terminal Abstraction** (`src/terminal.ts`):

```typescript
interface Terminal {
  start(onInput, onResize): void;
  stop(): void;
  write(data: string): void;
  get columns(): number;
  get rows(): number;
  moveBy(lines: number): void;
  // ... more
}

// Two implementations:
class ProcessTerminal implements Terminal { /* uses process.stdin/stdout */ }
class VirtualTerminal implements Terminal { /* uses @xterm/headless for testing */ }
```

### Built-in Components

| Component | Purpose |
|-----------|---------|
| `Text` | Multi-line text with word-wrap, padding, optional background |
| `TruncatedText` | Single-line, truncates to fit |
| `Input` | Single-line text input with horizontal scroll |
| `Editor` | Multi-line editor with slash-command autocomplete, file completion, paste handling |
| `Markdown` | Renders markdown with syntax highlighting + theming |
| `SelectList` | Interactive selection with keyboard nav, filtering |
| `SettingsList` | Settings panel with value cycling, submenus |
| `Loader` / `CancellableLoader` | Animated spinner with message |
| `Image` | Inline images (Kitty, iTerm2 graphics protocols) |
| `Box` | Container with padding + background |
| `Container` | Groups children |
| `Spacer` | Empty lines |

---

## 7. Theming System

### How Theming Works

Themes are **JSON files** following a schema. The theme defines colors by name, then assigns them to UI elements.

**File locations** (hot-reload):
- Global: `~/.pi/agent/themes/`
- Project: `.pi/themes/`
- Pi package: `<package>/themes/`

**Built-in themes**: `dark.json`, `light.json`

### Theme Structure

```json
{
  "$schema": "...",
  "name": "dark",
  "vars": {
    "cyan": "#00d7ff",
    "blue": "#5f87ff",
    "green": "#b5bd68",
    "text": "#d4d4d4",
    "userMsgBg": "#343541",
    ...
  },
  "colors": {
    "accent": "accent",
    "border": "blue",
    "error": "red",
    "userMessageBg": "userMsgBg",
    "mdHeading": "#f0c674",
    "syntaxKeyword": "blue",
    ... (90+ color keys)
  },
  "export": {
    "pageBg": "#...",
    "cardBg": "#..."
  }
}
```

### Color Palette

**Key color groups**:

| Group | Keys | Purpose |
|-------|------|---------|
| **UI** | `accent`, `border`, `borderAccent`, `borderMuted` | Nav, buttons, edges |
| **Text** | `text`, `muted`, `dim`, `thinkingText` | Messages, labels |
| **Messages** | `userMessageBg`, `customMessageBg`, `toolPending/Success/ErrorBg` | Message boxes |
| **Markdown** | `mdHeading`, `mdLink`, `mdCode`, `mdQuote`, etc. | Rendered markdown |
| **Syntax** | `syntaxKeyword`, `syntaxString`, `syntaxComment`, etc. | Code highlighting |
| **Thinking** | `thinkingOff`, `thinkingMinimal`, `thinkingLow`, etc. | Editor border per thinking level |

### Creating a Custom Theme

1. **Create a JSON file** (e.g., `.pi/themes/brand.json`):

```json
{
  "$schema": "https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/src/modes/interactive/theme/theme-schema.json",
  "name": "brand",
  "vars": {
    "primary": "#FF6B00",
    "text": "#1a1a1a"
  },
  "colors": {
    "accent": "primary",
    "border": "primary",
    "text": "text",
    "userMessageBg": "#ffe6cc",
    ... (90+ more colors required)
  }
}
```

2. **Load it**:
   ```bash
   pi --theme .pi/themes/brand.json
   ```

3. **Hot-reload**: Edit the file and changes appear immediately in the TUI.

---

## 8. Forking to Create a Branded TUI Agent

To create your own branded TUI agent variant:

### Option A: Extend via Package (Recommended)

Create a Pi Package with custom extensions, skills, and themes:

```bash
mkdir my-agent
cd my-agent

# Create package.json
cat > package.json << 'EOF'
{
  "name": "my-branded-agent",
  "keywords": ["pi-package"],
  "pi": {
    "extensions": ["./extensions"],
    "themes": ["./themes"],
    "prompts": ["./prompts"],
    "skills": ["./skills"]
  }
}
EOF

# Create custom theme
mkdir -p themes
cp ~/.pi/agent/themes/dark.json themes/brand.json
# Edit themes/brand.json with your colors

# Create custom extension
mkdir -p extensions
cat > extensions/brand.ts << 'EOF'
export default function (pi: ExtensionAPI) {
  // Register custom tools, commands, event handlers
  pi.registerCommand("brand-settings", {
    description: "Show brand settings",
    run: async (ctx) => {
      // Custom UI
    }
  });
}
EOF

# Install globally or per-project
pi install npm:./my-branded-agent
```

### Option B: Fork the Repo

If you need deeper customization:

```bash
git clone https://github.com/earendil-works/pi.git my-agent
cd my-agent

# Customize:
# - packages/coding-agent/src/modes/interactive/theme/dark.json
# - packages/coding-agent/src/modes/interactive/assets/ (images, logo)
# - packages/tui/src/components/ (custom components)
# - Update brand strings in src/modes/interactive/

npm install --ignore-scripts
npm run build

# Publish as your own package
npm publish --workspaces
```

### Key Customization Points

| Area | Files | What to Change |
|------|-------|-----------------|
| **Theme colors** | `packages/coding-agent/src/modes/interactive/theme/*.json` | Primary/secondary colors, UI palette |
| **Logo/Images** | `packages/coding-agent/src/modes/interactive/assets/` | Splash screen, icons |
| **System Prompt** | `.pi/SYSTEM.md` or `~/.pi/agent/SYSTEM.md` | Agent behavior instructions |
| **Extensions** | `.pi/extensions/`, `~/.pi/agent/extensions/` | Custom tools, UI components, commands |
| **Skills** | `.pi/skills/`, `~/.pi/agent/skills/` | On-demand capability packages |
| **Prompt Templates** | `.pi/prompts/`, `~/.pi/agent/prompts/` | Reusable prompt macros |
| **TUI Components** | `packages/tui/src/components/` | Custom interactive UI (if forking repo) |

---

## 9. Extensions Architecture

Extensions are **TypeScript modules** loaded at runtime. They have full access to:

```typescript
export default async function (pi: ExtensionAPI) {
  // Register custom tools
  pi.registerTool({
    name: "deploy",
    description: "Deploy to production",
    parameters: { ... },
    execute: async (params) => { ... }
  });

  // Register custom commands
  pi.registerCommand("ship", {
    description: "Ship a release",
    run: async (ctx) => { ... }
  });

  // Listen to events
  pi.on("tool_call", async (event, ctx) => { ... });
  pi.on("message", async (event, ctx) => { ... });

  // Register custom models/providers
  pi.registerProvider({
    name: "my-provider",
    models: [...],
    authenticate: async () => { ... }
  });

  // Replace/augment UI
  pi.replaceEditor(customEditorComponent);
  pi.addStatusLine(customStatusComponent);
  pi.addOverlay(customUIComponent);

  // Other capabilities
  // - Custom compaction logic
  // - Permission gates
  // - Git checkpointing
  // - SSH execution
  // - Games while waiting (yes, Doom extension exists)
}
```

**Loading**:
- Global: `~/.pi/agent/extensions/`
- Project: `.pi/extensions/`
- Pi package: `<package>/extensions/`
- CLI: `pi -e ./my-ext.ts`

---

## 10. Notable Patterns & Tech

### Supply-Chain Hardening

- Direct deps pinned to **exact versions**
- Internal workspace packages remain **version-ranged**
- `.npmrc` sets `save-exact=true` and `min-release-age=2`
- **Pre-commit hook** blocks lockfile commits unless `PI_ALLOW_LOCKFILE_CHANGE=1`
- Shrinkwrap generated for CLI package (pins transitive deps)
- **Lifecycle script allowlist** — new lifecycle-script deps fail checks until reviewed
- Scheduled CI audits: `npm audit --omit=dev` + signature verification

### Session Format (JSONL)

Sessions are **tree-structured JSONL** with `id` and `parentId`:

```jsonl
{"id":"a","parentId":null,"role":"user","content":"task 1"}
{"id":"b","parentId":"a","role":"assistant","..."}
{"id":"c","parentId":"a","role":"user","content":"task 2"}
```

This enables:
- **Branching**: Multiple children of one parent
- **In-place editing**: No new files needed
- **Full history preservation**: Complete tree persists even after branching

### Differential Rendering Strategy

Three-tier rendering for performance:

1. **First render**: No clear (preserve scrollback)
2. **Resizes/changes above viewport**: Clear screen, full re-render
3. **Normal updates**: Cursor to first changed line, clear to end, output deltas

All wrapped in **CSI 2026** synchronized output for **atomic, flicker-free** updates.

### No Built-in Features (Intentional)

Pi omits:
- **No MCP** — Build CLI tools with READMEs (skills), or add via extension
- **No sub-agents** — Spawn pi via tmux, or build with extensions
- **No plan mode** — Write plans to files, or build with extensions
- **No background bash** — Use tmux (full observability, interaction)
- **No permission popups** — Run in container, or build custom flow via extension
- **No built-in to-dos** — They confuse models; use TODO.md or custom extension

Philosophy: **Aggressively extensible**, keep core minimal.

---

## 11. Testing & Development

### Build

```bash
npm install --ignore-scripts
npm run build        # Build all packages (correct order: tui → ai → agent → coding-agent)
npm run check        # Lint, format, type-check
./test.sh            # Run tests (skips LLM tests without API keys)
```

### Project-Specific Rules

See `AGENTS.md` (project instructions for humans and agents).

### Key Files to Know

| File | Purpose |
|------|---------|
| `packages/tui/src/tui.ts` | Core TUI logic (1500+ lines) |
| `packages/tui/src/components/` | Built-in UI components |
| `packages/ai/src/providers/` | LLM provider implementations |
| `packages/agent/src/agent.ts` | Agent state machine |
| `packages/coding-agent/src/cli.ts` | CLI entry point |
| `packages/coding-agent/src/modes/interactive/` | Interactive mode (TUI integration) |
| `packages/coding-agent/src/core/extensions.ts` | Extension loader |
| `.pi/` | Pi's own config (extensions, prompts, skills it uses) |

---

## 12. Real-World Integration

### SDK (Embedding in Your App)

```typescript
import { createAgentSession, ModelRegistry, SessionManager } from "@earendil-works/pi-coding-agent";

const authStorage = AuthStorage.create();
const modelRegistry = ModelRegistry.create(authStorage);
const { session } = await createAgentSession({
  sessionManager: SessionManager.inMemory(),
  authStorage,
  modelRegistry,
});

await session.prompt("What files are in the current directory?");
```

See `examples/sdk/` for full examples.

### RPC Mode (Non-Node.js)

```bash
pi --mode rpc
```

Uses **strict LF-delimited JSONL** over stdin/stdout. Clients must split on `\n` only.

See `docs/rpc.md` for protocol.

---

## 13. Extensibility Examples

### Real-world Extensions in Repo

- **Gondolin** (`examples/extensions/gondolin/`) — Run tools in a local Linux micro-VM while keeping Pi and auth on host
- **Doom Overlay** (`examples/extensions/doom-overlay/`) — Play Doom while waiting for AI responses
- **Plan Mode** (`examples/extensions/plan-mode/`) — Add structured planning to Pi
- **Sandbox** (`examples/extensions/sandbox/`) — OpenShell policy-controlled sandbox
- **Custom Providers** (`examples/extensions/custom-provider-*/`) — Anthropic, GitLab Duo examples

---

## 14. Deployment & Containerization

Pi ships **without built-in permission system**. For stronger boundaries:

- **Gondolin extension** — Keep Pi + auth on host, route tools into micro-VM
- **Plain Docker** — Run whole process in container
- **OpenShell** — Policy-controlled sandbox

See `packages/coding-agent/docs/containerization.md`.

---

## 15. Quick Start for Fork

To fork and create your branded agent:

```bash
# Clone
git clone https://github.com/earendil-works/pi.git my-agent
cd my-agent

# Customize
# 1. Edit packages/coding-agent/src/modes/interactive/theme/*.json
# 2. Replace assets in packages/coding-agent/src/modes/interactive/assets/
# 3. Create .pi/extensions/ for brand-specific tools
# 4. Create .pi/themes/ for custom themes

# Build
npm install --ignore-scripts
npm run build

# Test
./pi-test.sh "Your test prompt"

# Publish
npm publish --workspaces
```

---

## Key Takeaways

1. **Minimal core** — 4 tools (read/write/edit/bash), extended via TypeScript
2. **Differential TUI** — Renders only what changed, synchronized output (flicker-free)
3. **Extensible** — Extensions, skills, themes, prompt templates, custom providers
4. **Tree-structured sessions** — JSONL with branching, no file duplication
5. **Multi-provider LLM API** — OpenAI, Anthropic, Google, Bedrock, and 15+ more
6. **Aggressively minimal philosophy** — No MCP, sub-agents, or plan mode built-in; build what you need
7. **Supply-chain hardened** — Exact pinning, audit hooks, lifecycle allowlists
8. **Easy to fork** — Customize theme, assets, extensions, providers

---

## Resources

- **Website**: https://pi.dev
- **Docs**: https://pi.dev/docs/latest
- **GitHub**: https://github.com/earendil-works/pi
- **Discord**: https://discord.com/invite/3cU7Bz4UPx
- **RFC**: https://rfc.earendil.com/keyword/pi/
- **Session Sharing**: https://huggingface.co/datasets/badlogicgames/pi-mono
