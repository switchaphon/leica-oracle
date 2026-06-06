# Caveman — Code Snippets & Patterns

**Project**: caveman (JuliusBrussee)  
**Purpose**: Token-optimized communication skill that cuts ~75% output tokens while maintaining technical accuracy  
**Date**: 2026-06-06

---

## Overview

Caveman is a cross-platform skill/plugin installer that modifies AI agent communication to be terse ("like smart caveman") without sacrificing technical substance. Achieves 65% average token savings across 10 benchmarks by dropping filler, articles, hedging, while preserving code, APIs, error messages exact.

**Key metrics:**
- 75% output token reduction claimed
- 65% average measured across 10 benchmarks
- Supports 8 intensity levels (lite/full/ultra + wenyan variants)
- Installs on 30+ AI agents (Claude Code, Gemini, Cursor, Windsurf, Cline, Copilot, etc.)

---

## Main Entry Point: bin/install.js

**Purpose**: Universal cross-platform installer; replaces old bash + PowerShell fragments with single Node script.

### Provider Matrix Architecture

```javascript
// Single source of truth for 30+ agents with detection logic
const PROVIDERS = [
  { id: 'claude',     label: 'Claude Code',    mech: 'claude plugin install',    detect: 'command:claude' },
  { id: 'cursor',     label: 'Cursor',         mech: 'npx skills add (cursor)',  detect: 'command:cursor||macapp:Cursor', profile: 'cursor' },
  { id: 'windsurf',   label: 'Windsurf',       mech: 'npx skills add (windsurf)', detect: 'command:windsurf||macapp:Windsurf', profile: 'windsurf' },
  { id: 'openclaw',   label: 'OpenClaw',       mech: 'workspace skill + SOUL.md', detect: 'command:openclaw||dir:$HOME/.openclaw/workspace' },
  // ... 26 more agents
];
```

**Key pattern**: Each agent has:
- `id` — unique identifier
- `label` — display name
- `mech` — install mechanism (plugin, skill, native)
- `detect` — detection spec (command:bin, dir:path, vscode-ext:name, etc.)
- `profile` — npx-skills profile name (if applicable)
- `soft` — optional; "soft" providers excluded from auto-detect; require explicit `--only`

### Detection Logic

```javascript
function detectMatch(spec) {
  if (!spec) return false;
  for (const clause of spec.split('||')) {
    const c = clause.trim();
    if (!c) continue;
    const colon = c.indexOf(':');
    const kind = colon === -1 ? c : c.slice(0, colon);
    const val  = colon === -1 ? '' : expandHome(c.slice(colon + 1));
    let ok = false;
    switch (kind) {
      case 'command':           ok = hasCmd(val); break;
      case 'dir':               ok = safeStat(val, 'isDirectory'); break;
      case 'vscode-ext':        ok = vscodeExtPresent(val); break;
      case 'cursor-ext':        ok = cursorExtPresent(val); break;
      case 'jetbrains-plugin':  ok = jetbrainsPluginPresent(val); break;
      case 'macapp':            ok = macAppPresent(val); break;
    }
    if (ok) return true;
  }
  return false;
}
```

**Pattern insight**: Declarative detection specs + pluggable check functions. `||` for fallback chains (e.g., try binary first, then macOS app).

### Platform-Specific Command Execution

```javascript
const IS_WIN = process.platform === 'win32';

function quoteWinArg(a) {
  if (!IS_WIN) return a;
  if (a === '' || /[\s"]/.test(a)) {
    // StandardCommandLineToArgvW escaping: \\ → \\\\, " → \"
    return '"' + String(a).replace(/\\(?=\\*"|$)/g, '\\\\').replace(/"/g, '\\"') + '"';
  }
  return a;
}

function spawnXplat(cmd, args, opts) {
  if (IS_WIN) {
    const quoted = args.map(quoteWinArg).join(' ');
    return child_process.spawnSync(`${cmd} ${quoted}`, [], Object.assign({ shell: true }, opts || {}));
  }
  return child_process.spawnSync(cmd, args, opts || {});
}
```

**Pattern insight**: Windows `.cmd` shims need shell:true; quoting via CommandLineToArgvW; Unix uses direct spawn.

### Argument Parsing

```javascript
function parseArgs(argv) {
  const opts = {
    dryRun: false, force: false, skipSkills: false,
    withHooks: 'auto', withInit: false, withMcpShrink: 'auto',
    all: false, minimal: false, listOnly: false, noColor: false,
    only: [], uninstall: false, nonInteractive: false,
    configDir: null, help: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case '--dry-run': opts.dryRun = true; break;
      case '--force': opts.force = true; break;
      // ...
      case '--only': {
        const v = argv[++i];
        if (!v) die('error: --only requires an argument');
        opts.only.push(v === 'aider' ? 'aider-desk' : v);
        break;
      }
      case '--': break;  // POSIX EOO marker; ignore
    }
  }
  // Auto-normalize: --all turns all options on
  if (opts.all) { opts.withHooks = true; opts.withInit = true; opts.withMcpShrink = true; }
  if (opts.minimal) { opts.withHooks = false; opts.withInit = false; opts.withMcpShrink = false; }
  return opts;
}
```

### Installation Dispatch

```javascript
async function main() {
  // ... detect providers ...
  for (const prov of PROVIDERS) {
    if (!want(prov.id)) continue;
    if (prov.soft && !explicit(prov.id)) continue;
    if (!explicit(prov.id) && !detectMatch(prov.detect)) continue;
    
    if (prov.id === 'claude')   { await installClaude(ctx); continue; }
    if (prov.id === 'gemini')   { installGemini(ctx); continue; }
    if (prov.id === 'opencode') { installOpencode(ctx); continue; }
    if (prov.id === 'openclaw') { installOpenclaw(ctx); continue; }
    if (prov.profile)           { installViaSkills(ctx, prov); continue; }
  }
}
```

---

## Configuration Management: bin/lib/settings.js

**Purpose**: JSONC-tolerant JSON read/write + hook validation for settings.json

### JSONC Parser (Comment-Aware)

```javascript
function stripJsonComments(src) {
  let out = '';
  let i = 0;
  let inString = false, stringChar = '';
  let inLine = false, inBlock = false;
  
  while (i < src.length) {
    const c = src[i];
    const next = i + 1 < src.length ? src[i + 1] : '';
    
    // Line comment: // → end of line
    if (!inString && c === '/' && next === '/') { inLine = true; i += 2; continue; }
    if (inLine && c === '\n') { inLine = false; out += c; i++; continue; }
    if (inLine) { i++; continue; }
    
    // Block comment: /* → */
    if (!inString && c === '/' && next === '*') { inBlock = true; i += 2; continue; }
    if (inBlock && c === '*' && next === '/') { inBlock = false; i += 2; continue; }
    if (inBlock) { i++; continue; }
    
    // String escaping
    if (c === '"' || c === "'") { 
      inString = !inString && c === stringChar ? false : (inString ? inString : c);
      out += c; i++; continue; 
    }
    if (inString && c === '\\' && i + 1 < src.length) {
      out += c + src[i + 1]; i += 2; continue;
    }
    
    out += c; i++;
  }
  
  // Trailing comma cleanup: remove , before } or ]
  return out.replace(/,(\s*[}\]])/g, '$1');
}
```

**Error recovery**: Fast path (strict JSON), fallback to JSONC strip + retry.

### Atomic File Write

```javascript
function writeSettings(p, obj) {
  const dir = path.dirname(p);
  fs.mkdirSync(dir, { recursive: true });
  const tmp = path.join(dir, `.${path.basename(p)}.${process.pid}.${crypto.randomBytes(4).toString('hex')}.tmp`);
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 2) + '\n', { mode: 0o600 });
  fs.renameSync(tmp, p);  // atomic rename
}
```

**Pattern**: Temp file + rename prevents corruption on crash; `mode: 0o600` for secrets.

### Hook Validation

```javascript
function validateHookFields(settings) {
  if (!settings?.hooks || typeof settings.hooks !== 'object') return;
  for (const ev of Object.keys(settings.hooks)) {
    const arr = settings.hooks[ev];
    if (!Array.isArray(arr)) { delete settings.hooks[ev]; continue; }
    
    settings.hooks[ev] = arr.filter(entry => {
      if (!entry?.hooks || !Array.isArray(entry.hooks)) return false;
      entry.hooks = entry.hooks.filter(h => {
        if (!h || typeof h !== 'object') return false;
        if (h.type === 'command') return typeof h.command === 'string' && h.command.length > 0;
        if (h.type === 'agent')   return typeof h.prompt === 'string' && h.prompt.length > 0;
        return false;
      });
      return entry.hooks.length > 0;
    });
    if (settings.hooks[ev].length === 0) delete settings.hooks[ev];
  }
}
```

**Rationale**: Claude Code's Zod schema discards entire settings.json if any hook is malformed. Pre-validate before write.

---

## Runtime Hook: src/hooks/caveman-activate.js

**Purpose**: SessionStart hook — emits caveman rules each session, reads SKILL.md at runtime

### Dynamic Rule Filtering

```javascript
const modeLabel = mode === 'wenyan' ? 'wenyan-full' : mode;
let skillContent = '';
try {
  skillContent = fs.readFileSync(
    path.join(__dirname, '..', 'skills', 'caveman', 'SKILL.md'), 'utf8'
  );
} catch (e) { /* fallback to hardcoded */ }

if (skillContent) {
  const body = skillContent.replace(/^---[\s\S]*?---\s*/, '');  // strip YAML frontmatter
  
  const filtered = body.split('\n').reduce((acc, line) => {
    const tableRowMatch = line.match(/^\|\s*\*\*(\S+?)\*\*\s*\|/);
    if (tableRowMatch && tableRowMatch[1] === modeLabel) {
      acc.push(line);  // keep only active level
      return acc;
    }
    
    const exampleMatch = line.match(/^- (\S+?):\s/);
    if (exampleMatch && exampleMatch[1] === modeLabel) {
      acc.push(line);
      return acc;
    }
    
    acc.push(line);
    return acc;
  }, []);
  
  output = 'CAVEMAN MODE ACTIVE — level: ' + modeLabel + '\n\n' + filtered.join('\n');
}
```

**Pattern**: Read skill file at runtime, strip frontmatter, filter examples by intensity level. No hardcoded duplication → single source of truth.

---

## Configuration Resolution: src/hooks/caveman-config.js

**Purpose**: Mode detection (env var → config file → default)

### Multi-Layer Config Resolution

```javascript
function getDefaultMode() {
  // 1. Environment variable (highest priority)
  const envMode = process.env.CAVEMAN_DEFAULT_MODE;
  if (envMode && VALID_MODES.includes(envMode.toLowerCase())) {
    return envMode.toLowerCase();
  }

  // 2. Config file ($XDG_CONFIG_HOME/caveman/config.json or platform-specific)
  try {
    const configPath = getConfigPath();
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (config.defaultMode && VALID_MODES.includes(config.defaultMode.toLowerCase())) {
      return config.defaultMode.toLowerCase();
    }
  } catch (e) { /* config file absent or invalid — fall through */ }

  // 3. Default
  return 'full';
}
```

### Symlink-Safe Flag Write

```javascript
function safeWriteFlag(flagPath, content) {
  const debug = process.env.CAVEMAN_DEBUG === '1';
  try {
    const flagDir = path.dirname(flagPath);
    fs.mkdirSync(flagDir, { recursive: true });

    // When parent dir is a symlink, resolve and verify ownership
    let realFlagDir;
    const lstat = fs.lstatSync(flagDir);
    if (lstat.isSymbolicLink()) {
      realFlagDir = fs.realpathSync(flagDir);
      const realStat = fs.statSync(realFlagDir);
      if (!realStat.isDirectory()) {
        if (debug) process.stderr.write(`[caveman] symlink target not a directory\n`);
        return;
      }
      // Unix: verify ownership (uid match)
      if (typeof process.getuid === 'function') {
        const uid = process.getuid();
        if (realStat.uid !== uid) {
          if (debug) process.stderr.write(`[caveman] symlink owned by different user\n`);
          return;
        }
      }
      // Windows: verify resolved path under home dir
      if (process.platform === 'win32') {
        const home = os.homedir();
        if (!realFlagDir.startsWith(home)) {
          if (debug) process.stderr.write(`[caveman] symlink points outside home dir\n`);
          return;
        }
      }
    } else {
      realFlagDir = flagDir;
    }

    // Write flag file (the flag itself must never be a symlink)
    const tmp = path.join(realFlagDir, `.caveman-active.${process.pid}.tmp`);
    fs.writeFileSync(tmp, content, { mode: 0o600 });
    fs.renameSync(tmp, flagPath);
  } catch (e) {
    if (debug) process.stderr.write(`[caveman] safeWriteFlag error: ${e.message}\n`);
  }
}
```

**Security pattern**: Protects against symlink attacks; allows legitimate symlinked config dirs; verifies ownership on Unix, path containment on Windows.

---

## Stats & Token Tracking: src/hooks/caveman-stats.js

**Purpose**: Parse Claude Code session log, compute savings

### Session Log Parsing

```javascript
function parseSession(filePath) {
  let raw;
  try { raw = fs.readFileSync(filePath, 'utf8'); }
  catch { return { outputTokens: 0, cacheReadTokens: 0, turns: 0, model: null }; }

  let outputTokens = 0;
  let cacheReadTokens = 0;
  let turns = 0;
  let model = null;
  
  for (const line of raw.split('\n')) {
    // Parse JSONL session log, extract usage + model per turn
    // Accumulate outputTokens and cacheReadTokens
  }
  return { outputTokens, cacheReadTokens, turns, model };
}
```

### Pricing Calculation

```javascript
const MODEL_OUTPUT_PRICE_PER_M = [
  ['claude-opus-4',     75.00],
  ['claude-sonnet-4',   15.00],
  ['claude-haiku-4',     4.00],
  // ... more models
];

function priceForModel(model) {
  if (!model) return null;
  for (const [prefix, price] of MODEL_OUTPUT_PRICE_PER_M) {
    if (model.startsWith(prefix)) return price;
  }
  return null;
}

// Compute savings
const COMPRESSION = { 'full': 0.65 };  // 65% measured savings
const compression = COMPRESSION[mode] || 0;
const savedTokens = outputTokens * compression;
const savingsUsd = (savedTokens * priceForModel(model)) / 1_000_000;
```

**Data source**: `benchmarks/results/*.json` measured empirically; Anthropic pricing table hardcoded and updated manually.

---

## Skill Definition: skills/caveman/SKILL.md

**Purpose**: YAML frontmatter + markdown ruleset; emitted by activation hook

### Frontmatter (Plugin Metadata)

```yaml
---
name: caveman
description: >
  Ultra-compressed communication mode. Cuts token usage ~75% by speaking like caveman
  while keeping full technical accuracy. Supports intensity levels: lite, full (default), ultra,
  wenyan-lite, wenyan-full, wenyan-ultra.
  Use when user says "caveman mode", "talk like caveman", "use caveman", "less tokens",
  "be brief", or invokes /caveman. Also auto-triggers when token efficiency is requested.
---
```

### Intensity Table

| Level | What changes |
|-------|------|
| **lite** | No filler/hedging. Keep articles + full sentences. Professional but tight |
| **full** | Drop articles, fragments OK, short synonyms. Classic caveman |
| **ultra** | Abbreviate prose words (DB/auth/config), strip conjunctions, arrows for causality, one-word when one-word enough |
| **wenyan-full** | Maximum classical terseness. Fully 文言文. 80-90% character reduction |

### Examples

```
Example — "Why React component re-render?"
- lite: "Your component re-renders because you create a new object reference each render. Wrap it in `useMemo`."
- full: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
- ultra: "Inline obj prop → new ref → re-render. `useMemo`."
```

---

## Test Architecture: tests/test_caveman_init.js

**Purpose**: Fixture-based tests for per-repo IDE rule file generation

### Fixture Test Pattern

```javascript
function test(name, fn) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'caveman-init-test-'));
  try {
    fn(tmp);
    passed++;
    console.log(`  ✓ ${name}`);
  } catch (e) {
    failed++;
    console.error(`  ✗ ${name}\n    ${e.message}`);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

test('greenfield: creates all rule files with proper frontmatter', (tmp) => {
  execFileSync(process.execPath, [INIT, tmp], { encoding: 'utf8' });
  const cursor = fs.readFileSync(path.join(tmp, '.cursor/rules/caveman.mdc'), 'utf8');
  assert.match(cursor, /alwaysApply: true/);
  assert.match(cursor, /Respond terse like smart caveman/);
});

test('idempotent: re-running on a clean install skips all', (tmp) => {
  execFileSync(process.execPath, [INIT, tmp], { encoding: 'utf8' });
  const out = execFileSync(process.execPath, [INIT, tmp], { encoding: 'utf8' });
  assert.match(out, /5 skipped/);
});
```

**Pattern**: Each test gets its own temp dir, executes in isolation, cleaned up after. Idempotency verified by re-run assertion.

---

## Key Patterns & Techniques

### 1. Provider Matrix + Declarative Detection
- Single source of truth (PROVIDERS array)
- Composable detection specs: `'command:claude||macapp:Cursor'`
- Soft providers (no reliable probe) require explicit `--only`

### 2. Cross-Platform Abstraction
- Windows: `.cmd` shims need shell:true + CommandLineToArgvW quoting
- Unix: direct spawn
- Config paths: XDG_CONFIG_HOME → platform-specific fallbacks

### 3. Symlink Security
- Resolve symlinked parent dirs, verify ownership (Unix uid) or containment (Windows home)
- Flag file itself must never be symlink (the clobber vector)
- Silent-fail on security check; `CAVEMAN_DEBUG=1` emits diagnostics

### 4. Runtime Configuration
- Environment → config file → hardcoded default
- YAML frontmatter in SKILL.md + markdown body for rules
- Hook reads SKILL.md at runtime, filters by intensity level; no duplication

### 5. Idempotency & Atomicity
- Atomic file writes via temp + rename
- Detection probes before install (skip if already installed unless --force)
- Marker strings for incremental updates (e.g., AGENTS.md fenced blocks)

### 6. Error Recovery
- JSONC-tolerant JSON parser (comments + trailing commas)
- Pre-validate hook structures before write (Zod schema strict)
- Fallback hardcoded rules if SKILL.md not found

### 7. Intensity Levels
- 8 modes: off, lite, full, ultra + wenyan variants (classical Chinese)
- Single SKILL.md with intensity table + per-level examples
- Hook filters examples at runtime; activation rule shows only active level

---

## File Ownership & Architecture

| File | Role |
|------|------|
| `bin/install.js` | Universal installer; provider detection + dispatch |
| `bin/lib/settings.js` | JSONC parser + hook validation |
| `bin/lib/openclaw.js` | OpenClaw workspace integration (SOUL.md injection) |
| `src/hooks/caveman-activate.js` | SessionStart hook; emits rules + flag |
| `src/hooks/caveman-config.js` | Mode resolution (env → config → default) + symlink-safe flag write |
| `src/hooks/caveman-stats.js` | Session log parser; token savings estimate |
| `src/hooks/caveman-mode-tracker.js` | UserPromptSubmit hook; mode persistence check |
| `src/tools/caveman-init.js` | Per-repo IDE rule file writer (.cursor, .windsurf, AGENTS.md, etc.) |
| `skills/caveman/SKILL.md` | Intensity table + rules (canonical source of truth) |
| `tests/test_caveman_init.js` | Fixture-based init tests |

---

## Summary

Caveman is a **configuration-as-code system** for controlling LLM verbosity:

1. **Installer** detects 30+ agents via declarative specs, routes to agent-specific install (plugin/skill/native)
2. **Hook system** (SessionStart → caveman-activate.js) injects rules; reads SKILL.md at runtime for single source of truth
3. **Config resolution** (env → file → default) with symlink security
4. **Intensity filtering** done at hook time, not hardcoded; easily swap between lite/full/ultra mid-session
5. **Stats tracking** reads Claude Code session log, estimates token savings vs. baseline
6. **Idempotency** baked in: detection probes, marker strings, --force override
7. **Cross-platform** single Node script handles Windows cmd quoting, Unix shell escaping, path normalization

The architecture prioritizes **reliability** (symlink attacks, settings.json crashes, malformed hooks) over cleverness, and **maintainability** (single source of truth in SKILL.md, no hardcoded duplication).
