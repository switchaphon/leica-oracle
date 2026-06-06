# Caveman Quick Reference Guide

**Project**: caveman — AI agent output compression  
**Author**: Julius Brussee  
**License**: MIT  
**Tagline**: *why use many token when few do trick*

---

## What It Does

Caveman makes AI coding agents (Claude Code, Cursor, Windsurf, Cline, GitHub Copilot, 30+ others) respond in compressed caveman-style prose — cuts ~65-75% output tokens while preserving full technical accuracy. Same fix quality, 75% fewer tokens, 3x faster responses.

**Before/After Example:**
- **Normal**: "The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle..." (69 tokens)
- **Caveman**: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`." (19 tokens)

---

## Installation

### One-Line Install (All Agents)

**macOS / Linux / WSL / Git Bash:**
```bash
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash
```

**Windows (PowerShell 5.1+):**
```powershell
irm https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.ps1 | iex
```

**What it does:**
- Auto-detects all supported AI agents on your machine
- Installs caveman for each one
- Wires hooks, statusline badge, MCP middleware
- Safe to re-run; ~30 seconds total
- Requires Node ≥18

**Preview before installing:**
```bash
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash -s -- --dry-run
```

### Per-Agent Install (Manual)

See [INSTALL.md](https://github.com/JuliusBrussee/caveman/blob/main/INSTALL.md) for 30+ agents. Key examples:

| Agent | Command |
|-------|---------|
| Claude Code | `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman` |
| Cursor | `npx skills add JuliusBrussee/caveman -a cursor` |
| Windsurf | `npx skills add JuliusBrussee/caveman -a windsurf` |
| Cline | `npx skills add JuliusBrussee/caveman -a cline` |
| Codex | `npx skills add JuliusBrussee/caveman -a codex` |
| Gemini CLI | `gemini extensions install https://github.com/JuliusBrussee/caveman` |

---

## How to Use It

### Claude Code (Auto-Activates)

Once installed, caveman activates automatically on every session. Start coding normally — agent talks caveman from message one.

**Optional:** Override mode mid-session with `/caveman [lite|full|ultra|wenyan]`

### Other Agents

Type `/caveman` once per session to activate (or say "talk like caveman"). Level sticks until session ends.

**Intensity Levels:**
- `lite` — drop filler, keep substance (22% token reduction)
- `full` (default) — fragments, skip articles (65% token reduction)
- `ultra` — telegraphic, one thought per line (83% token reduction)
- `wenyan` — classical Chinese-inspired brevity (even shorter)

---

## Key Features

| Feature | What | Usage |
|---------|------|-------|
| **Main Skill** | `/caveman [lite\|full\|ultra\|wenyan]` | Compress every reply; level persists until changed or session ends |
| **Commit Mode** | `/caveman-commit` | Conventional Commit messages, ≤50 char subject, "why" over "what" |
| **Review Mode** | `/caveman-review` | One-line PR comments: `L42: 🔴 bug: user null. Add guard.` |
| **Compress Files** | `/caveman-compress <file>` | Rewrite memory files (CLAUDE.md, notes) into caveman-speak; ~46% savings |
| **Stats** | `/caveman-stats` | Real session token usage + lifetime savings + USD; `--share` for tweetable line |
| **Help** | `/caveman-help` | Quick-reference card |
| **Subagents** | `cavecrew-*` | Investigator/builder/reviewer — ~60% fewer tokens, longer context |

### Auto-Clarity Rule

Caveman automatically switches to normal prose for:
- Security warnings
- Irreversible action confirmations (e.g., `git push --force`)
- Multi-step sequences where fragment ambiguity risks misread
- User confused or repeating a question

Then resumes caveman mode after.

---

## Configuration

### Mode Persistence

**Claude Code:** Session-start hook reads `$CLAUDE_CONFIG_DIR/.caveman-active` flag (default `~/.claude/.caveman-active`). Modes stick for the session or until `/caveman <newmode>` is called.

**Default Mode:** Set `CAVEMAN_DEFAULT_MODE` env var or use `$XDG_CONFIG_HOME/caveman/config.json`:
```json
{ "defaultMode": "ultra" }
```

### Disable Statusline Badge

Set env var: `CAVEMAN_STATUSLINE_SAVINGS=0`

### Custom Config Directory (Claude Code)

Set env var: `CLAUDE_CONFIG_DIR=/path/to/config`

---

## Tech Stack

| Layer | What |
|-------|------|
| **Core** | Node.js ≥18 CLI installer (`bin/install.js`); platform-agnostic |
| **Skills** | Markdown files with YAML frontmatter (`skills/*/SKILL.md`); LLM-readable prompt bodies |
| **Hooks** | Claude Code: JavaScript hooks in `src/hooks/`; hook into SessionStart + UserPromptSubmit |
| **MCP** | Optional `caveman-shrink` middleware (wraps any MCP server, compresses tool descriptions) |
| **Testing** | Node tests + Python evals (three-arm harness: baseline / terse / skill) + real benchmark runs through Claude API |
| **CI** | GitHub Actions: auto-syncs `skills/*/SKILL.md` → `plugins/caveman/skills/*/` on push |

---

## Real Benchmarks

Average **65% output token reduction** across 10 real prompts (range 22-87%). Token counts from Claude API (not estimated).

| Task | Normal | Caveman | Saved |
|------|-------:|--------:|------:|
| Explain React re-render bug | 1180 | 159 | 87% |
| Fix auth middleware token expiry | 704 | 121 | 83% |
| Set up PostgreSQL connection pool | 2347 | 380 | 84% |
| Explain git rebase vs merge | 702 | 292 | 58% |
| Refactor callback to async/await | 387 | 301 | 22% |
| Architecture: microservices vs monolith | 446 | 310 | 30% |
| Review PR for security issues | 678 | 398 | 41% |
| Docker multi-stage build | 1042 | 290 | 72% |
| Debug PostgreSQL race condition | 1200 | 232 | 81% |
| Implement React error boundary | 3454 | 456 | 87% |
| **Average** | **1214** | **294** | **65%** |

**caveman-compress** on memory files saves ~46% input tokens:
- `claude-md-preferences.md`: 706 → 285 tokens (59.6% saved)
- `project-notes.md`: 1145 → 535 tokens (53.3% saved)
- `claude-md-project.md`: 1122 → 636 tokens (43.3% saved)

---

## Comparison with Similar Tools

| Tool | Purpose | Scope |
|------|---------|-------|
| **caveman** (this) | Output compression + commit/review/stats skills | Prompt injection (skill system) + hooks (Claude Code) |
| **caveman-code** | Full terminal coding agent, caveman throughout | Whole application (agent replacement) |
| **cavemem** | Cross-agent persistent memory | User memory/context between sessions |
| **cavekit** | Spec-driven build loop | Build process orchestration |
| **cavegemma** | Gemma 4 31B fine-tuned on caveman pairs | Model weights (no prompting needed) |

**Related (not same):**
- **Claude Code rules files** (`.cursor/rules/`, `.windsurf/rules/`) — agent-specific rule syntax, one-per-agent. Caveman is agent-agnostic.
- **Conventional Commits** — commit message format. Caveman's `/caveman-commit` enforces it while also compressing.
- **Code review linters** (ESLint, etc.) — source code quality. Caveman's `/caveman-review` compresses *human review output*, not static analysis.

---

## Key Design Principles

1. **Brain still big** — caveman only affects output tokens, not reasoning/thinking tokens. Accuracy unchanged or improved.
2. **Intensity levels** — adjust compression to task: light work (lite), day-to-day (full), speed mode (ultra).
3. **Auto-clarity** — switches to normal prose for high-stakes decisions; resumes caveman after.
4. **Multi-agent** — installs into 30+ agents via single command; detection logic in `bin/install.js`.
5. **Silent fail** — hooks never block session start; all filesystem errors caught and ignored.
6. **Symlink-safe** — flag writes through `safeWriteFlag()` to prevent local privilege escalation.

---

## Troubleshooting

**"Claude Code isn't talking caveman after install."**
1. Check `node bin/install.js --list` — confirm `claude` is detected
2. Verify `~/.claude/settings.json` has `"hooks"` with `caveman-activate.js` and `caveman-mode-tracker.js`
3. Check `~/.claude/.caveman-active` exists with content `full`
4. Restart Claude Code (hooks only fire on session start)

**"Hooks failing on Windows."**
- Use `install.ps1` (not `install.sh`)
- PowerShell 5.1 minimum
- If execution policy blocks: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

**"My settings.json got broken."**
- Check for backup at `~/.claude/settings.json.bak`
- Installer uses JSONC-tolerant parser so comments and trailing commas don't break the merge

**"I'm in a managed environment where I can't install hooks."**
```bash
# Install just rule files, no global state
node bin/install.js --with-init --only cursor --only windsurf
```

---

## Resources

- **GitHub**: https://github.com/JuliusBrussee/caveman
- **Full Install Guide**: [INSTALL.md](https://github.com/JuliusBrussee/caveman/blob/main/INSTALL.md)
- **Contributing**: [CONTRIBUTING.md](https://github.com/JuliusBrussee/caveman/blob/main/CONTRIBUTING.md)
- **Maintainer Guide**: [CLAUDE.md](https://github.com/JuliusBrussee/caveman/blob/main/CLAUDE.md) (file structure, hook architecture, CI)
- **Paper**: [Brevity Constraints Reverse Performance Hierarchies in Language Models (arXiv 2604.00025)](https://arxiv.org/abs/2604.00025)

---

## One More Thing

**caveman-code** (separate project) extends caveman to the entire terminal agent. If you want the whole coding loop running on 2× fewer tokens, check it out:
```bash
npm install -g @juliusbrussee/caveman-code
```

Caveman teaches lobster brevity — same installer, scoped to [OpenClaw](https://openclaw.ai) gateway:
```bash
npx -y github:JuliusBrussee/caveman -- --only openclaw
```
