# MAW Local Plugin — Complete Technical Guide

> "วางไฟล์ใน `.maw/plugins/` แล้ว maw โหลดให้อัตโนมัติ — ไม่ต้อง register, ไม่ต้อง config"

---

## Chapter 1: What is a Local Plugin?

MAW JS มี plugin system ที่ **auto-discover** plugins จาก directory structure:

```
project/
├── .maw/
│   └── plugins/
│       └── my-plugin/
│           ├── plugin.json    ← manifest
│           └── index.ts       ← handler
├── src/
└── ...
```

เมื่อรัน `maw` จาก `project/` directory → maw จะ:
1. เดินขึ้นจาก `cwd` หา `.maw/plugins/` ทุกชั้น (สูงสุด 32 ชั้น)
2. หยุดเมื่อเจอ `.maw-root` marker
3. รวมกับ global `~/.maw/plugins/`
4. โหลดทุก plugin ที่เจอ — **อัตโนมัติ**

### Proof from Source Code

```typescript
// src/plugin/registry-helpers.ts:19
export function discoverLocalPluginDirs(cwd = process.cwd()): string[] {
  const dirs: string[] = [];
  let dir = resolve(cwd);
  for (let i = 0; i < 32; i += 1) {
    const pluginsDir = join(dir, ".maw", "plugins");
    if (existsSync(pluginsDir)) dirs.push(pluginsDir);
    if (existsSync(join(dir, ".maw-root"))) break;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return dirs;
}
```

---

## Chapter 2: Creating Your First Local Plugin

### Step 1: Create the directory

```bash
mkdir -p .maw/plugins/hello-world
cd .maw/plugins/hello-world
```

### Step 2: Write `plugin.json` (manifest)

```json
{
  "name": "hello-world",
  "version": "1.0.0",
  "description": "My first maw plugin",
  "command": {
    "name": "hello",
    "description": "Say hello from local plugin"
  },
  "main": "index.ts",
  "runtime": "bun"
}
```

### Step 3: Write `index.ts` (handler)

```typescript
import type { InvokeContext, InvokeResult } from "maw-js/plugin/types";

export const command = {
  name: "hello",
  description: "Say hello from local plugin",
};

export default async function handler(ctx: InvokeContext): Promise<InvokeResult> {
  const out: string[] = [];
  const log = (s: string) => (ctx.writer ? ctx.writer(s) : out.push(s));

  const args = ctx.source === "cli" ? (ctx.args as string[]) : [];
  const name = args[0] || "world";

  log(`👋 Hello, ${name}! (from local .maw/plugins/hello-world)`);
  log(`  cwd: ${process.cwd()}`);
  log(`  time: ${new Date().toISOString()}`);

  return {
    ok: true,
    output: ctx.writer ? "" : out.join("\n"),
    exitCode: 0,
  };
}
```

### Step 4: Install dependencies

```bash
bun init -y
bun add maw-js  # or link to local maw-js
```

### Step 5: Run it!

```bash
cd /path/to/project  # ที่มี .maw/plugins/hello-world
maw hello
# Output: 👋 Hello, world! (from local .maw/plugins/hello-world)

maw hello Leica
# Output: 👋 Hello, Leica! (from local .maw/plugins/hello-world)
```

---

## Chapter 3: Plugin Handler API

### InvokeContext

```typescript
interface InvokeContext {
  source: "cli" | "api" | "scheduler";  // ถูกเรียกจากไหน
  args: string[];                        // CLI arguments
  writer?: (line: string) => void;       // streaming output
  env: Record<string, string>;           // environment variables
  cwd: string;                           // current working directory
}
```

### InvokeResult

```typescript
interface InvokeResult {
  ok: boolean;           // สำเร็จหรือไม่
  output: string;        // output text (ถ้าไม่ใช้ writer)
  error?: string;        // error message
  exitCode: number;      // 0 = success
}
```

### Subcommands Pattern

```typescript
export default async function handler(ctx: InvokeContext): Promise<InvokeResult> {
  const args = ctx.args as string[];
  const sub = args[0]?.toLowerCase();

  switch (sub) {
    case "status":  return status(ctx);
    case "sync":    return sync(ctx);
    case "list":    return list(ctx);
    default:        return help(ctx);
  }
}
```

---

## Chapter 4: Real-World Example — Chronicle Sync Plugin

จาก Leica Oracle (`maw-plugin/index.ts`):

```typescript
export const command = {
  name: "leica",
  description: "Father Oracle — fleet commands, family status, chronicle.",
};

// Chronicle = polling pattern
// state.json เก็บ channelId → lastMessageId (bookmark)
// ทุกรอบ sync ดึงแค่ข้อความใหม่ (after: lastId)
// POST ไป backend → update bookmark
// idempotent + resumable

case "chronicle": {
  const action = args[1]?.toLowerCase();
  if (action === "sync") {
    const token = getDiscordToken();
    const state = loadState();  // { channelId: lastMessageId }
    
    for (const channel of channels) {
      const msgs = await discordGet(
        `/channels/${channel}/messages?after=${state[channel]}`
      );
      // POST each msg → backend
      // Update bookmark
      state[channel] = msgs[msgs.length - 1].id;
    }
    saveState(state);
  }
}
```

### Key Patterns:
1. **Bookmark state** — `loadState()`/`saveState()` persist ข้าม session
2. **Incremental fetch** — `?after=lastId` ดึงแค่ใหม่
3. **Idempotent** — รันซ้ำไม่พัง (upsert/skip duplicates)
4. **Resumable** — restart แล้ว bookmark ยังอยู่

---

## Chapter 5: Plugin Discovery — How It Works

### Search Order

```
1. cwd/.maw/plugins/          ← project-local (highest priority)
2. ../maw/plugins/             ← parent dir
3. ../../.maw/plugins/         ← grandparent (up to 32 levels)
4. ~/.maw/plugins/             ← global (lowest priority)
5. MAW_PLUGINS_DIR env var     ← override
```

### Stop Marker

วาง `.maw-root` file ใน directory ไหน → maw หยุดเดินขึ้น:

```
/home/user/projects/my-project/.maw-root    ← stop here
/home/user/projects/my-project/.maw/plugins/ ← found
/home/user/projects/.maw/plugins/            ← NOT searched
```

### Plugin Loading (server.ts:372)

```typescript
// Project-local plugins (.maw/plugins in cwd ancestors)
const projectPluginDirs = discoverLocalPluginDirs(process.cwd());
// → merged with global plugins
// → all auto-loaded
```

---

## Chapter 6: Advanced — Plugin with External APIs

### Discord API Plugin

```typescript
async function discordGet(path: string, token: string): Promise<any> {
  const res = await fetch(`https://discord.com/api/v10${path}`, {
    headers: {
      Authorization: `Bot ${token}`,
      "User-Agent": "my-plugin/1.0.0",
    },
  });
  if (!res.ok) throw new Error(`Discord ${res.status} ${path}`);
  return res.json();
}
```

### File System Plugin

```typescript
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { homedir } from "os";

const DATA_DIR = join(homedir(), ".maw", "my-plugin-data");

function loadData(): any {
  try { return JSON.parse(readFileSync(join(DATA_DIR, "state.json"), "utf8")); }
  catch { return {}; }
}

function saveData(data: any): void {
  mkdirSync(DATA_DIR, { recursive: true });
  writeFileSync(join(DATA_DIR, "state.json"), JSON.stringify(data, null, 2));
}
```

---

## Chapter 7: Testing Your Plugin

```bash
# 1. Verify maw sees your plugin
maw plugins ls | grep hello

# 2. Run with verbose
maw hello --verbose

# 3. Check from different cwd
cd /tmp && maw hello  # should NOT find project-local plugin
cd /path/to/project && maw hello  # should find it
```

---

## Chapter 8: Best Practices

1. **ใช้ `.maw/plugins/` สำหรับ project-specific** — ไม่ปน global
2. **ใช้ `~/.maw/plugins/` สำหรับ personal tools** — ใช้ได้ทุก project
3. **Manifest ต้องมี** `name`, `version`, `command`, `main`
4. **Handler return `InvokeResult`** — อย่า throw ตรง ๆ
5. **State เก็บใน `~/.maw/<plugin>/`** — ไม่ปน project files
6. **Secrets อยู่ใน `.env`** — อย่า hardcode ใน source
7. **Writer pattern** — ใช้ `ctx.writer` สำหรับ streaming output

---

## Quick Reference

| Command | Description |
|---------|------------|
| `maw plugins ls` | list all loaded plugins |
| `maw plugins info <name>` | plugin details |
| `maw <command>` | run plugin command |
| `maw plugins create <name>` | scaffold new plugin |

| File | Purpose |
|------|---------|
| `.maw/plugins/<name>/plugin.json` | manifest |
| `.maw/plugins/<name>/index.ts` | handler |
| `~/.maw/plugins/` | global plugins |
| `.maw-root` | stop discovery marker |

---

*Written by 🐱 Leica Oracle — Father Oracle*
*"The lens that sees clearly keeps the human human."*
*AI, ไม่ใช่คน — Rule 6*
