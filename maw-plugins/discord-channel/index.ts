/**
 * maw discord-channel — manage Discord channel plugin state.
 *
 * Pattern follows maw token: subcommand routing, pass vault for secrets,
 * per-repo state dir with global symlink support.
 *
 * Subcommands:
 *   token save/load/show/set  — DISCORD_BOT_TOKEN via pass vault
 *   access show/pair/allow/remove/group/policy — access.json management
 *   status                    — current state overview
 *   state init/link/dir       — DISCORD_STATE_DIR management
 */

import type { InvokeContext, InvokeResult } from "maw-js/plugin/types";
import { existsSync, readFileSync, writeFileSync, mkdirSync, symlinkSync, realpathSync } from "fs";
import { join, basename } from "path";
import { homedir } from "os";
import { randomBytes } from "crypto";

export const command = {
  name: "discord-channel",
  description: "Manage Discord channel plugin: token, access.json, state dir, status.",
};

// ── Paths ────────────────────────────────────────────────────────────────

const GLOBAL_STATE = join(homedir(), ".claude", "channels", "discord");
const PASS_TOKEN_PREFIX = "claude/discord-bot-token-";
const PASS_ENVRC_PREFIX = "envrc";

function stateDir(cwd: string): string {
  // Priority: DISCORD_STATE_DIR env > .discord-state/ in cwd > global
  if (process.env.DISCORD_STATE_DIR) return process.env.DISCORD_STATE_DIR;
  const local = join(cwd, ".discord-state");
  if (existsSync(local)) return local;
  return GLOBAL_STATE;
}

function accessPath(cwd: string): string {
  return join(stateDir(cwd), "access.json");
}

// ── Helpers ──────────────────────────────────────────────────────────────

interface Access {
  dmPolicy: "pairing" | "allowlist" | "disabled";
  allowFrom: string[];
  groups: Record<string, { requireMention: boolean; allowFrom: string[] }>;
  pending: Record<string, any>;
  mentionPatterns?: string[];
  ackReaction?: string;
  replyToMode?: "off" | "first" | "all";
  textChunkLimit?: number;
  chunkMode?: "length" | "newline";
}

function defaultAccess(): Access {
  return { dmPolicy: "pairing", allowFrom: [], groups: {}, pending: {} };
}

function loadAccess(cwd: string): Access {
  const p = accessPath(cwd);
  if (!existsSync(p)) return defaultAccess();
  try {
    const raw = JSON.parse(readFileSync(p, "utf-8"));
    return { ...defaultAccess(), ...raw };
  } catch {
    return defaultAccess();
  }
}

function saveAccess(cwd: string, access: Access): void {
  const p = accessPath(cwd);
  const dir = join(p, "..");
  mkdirSync(dir, { recursive: true });
  writeFileSync(p, JSON.stringify(access, null, 2) + "\n");
}

function run(cmd: string[], opts: { stdin?: string; cwd?: string } = {}) {
  const spawnOpts: any = {
    cwd: opts.cwd,
    env: process.env,
    stdout: "pipe",
    stderr: "pipe",
  };
  if (opts.stdin !== undefined) {
    spawnOpts.stdin = new TextEncoder().encode(opts.stdin);
  }
  const proc = Bun.spawnSync(cmd, spawnOpts);
  const dec = new TextDecoder();
  return {
    ok: proc.exitCode === 0,
    stdout: proc.stdout instanceof Uint8Array ? dec.decode(proc.stdout) : String(proc.stdout ?? ""),
    stderr: proc.stderr instanceof Uint8Array ? dec.decode(proc.stderr) : String(proc.stderr ?? ""),
  };
}

// ── Subcommands ──────────────────────────────────────────────────────────

function cmdTokenShow(name: string): string {
  const r = run(["pass", "show", `${PASS_TOKEN_PREFIX}${name}`]);
  if (!r.ok) return `token "${name}" not found in pass`;
  return `token "${name}" exists in pass (value hidden)`;
}

function cmdTokenSave(name: string, token: string): string {
  // SECURITY: token via stdin, never argv
  const r = run(["pass", "insert", "--multiline", "--force", `${PASS_TOKEN_PREFIX}${name}`], {
    stdin: token,
  });
  if (!r.ok) return `pass insert failed`;
  return `saved token "${name}" to pass vault`;
}

function cmdTokenLoad(name: string, cwd: string): string {
  const r = run(["pass", "show", `${PASS_TOKEN_PREFIX}${name}`]);
  if (!r.ok) return `token "${name}" not found in pass`;
  // Write to .env in state dir (never print the value)
  const envPath = join(stateDir(cwd), ".env");
  mkdirSync(stateDir(cwd), { recursive: true });
  writeFileSync(envPath, `DISCORD_BOT_TOKEN=${r.stdout.trim()}\n`, { mode: 0o600 });
  return `loaded token "${name}" → ${envPath} (chmod 600)`;
}

function cmdTokenList(): string {
  const r = run(["pass", "ls", "claude"]);
  if (!r.ok) return "no tokens in pass vault";
  const names: string[] = [];
  for (const line of r.stdout.split("\n")) {
    const clean = line.replace(/\x1b\[[0-9;]*m/g, "");
    const m = /discord-bot-token-(\S+)/.exec(clean);
    if (m) names.push(m[1]);
  }
  if (names.length === 0) return "no discord bot tokens in pass vault";
  return "Discord bot tokens:\n" + names.map((n, i) => `  ${i + 1}. ${n}`).join("\n");
}

function cmdAccessShow(cwd: string): string {
  const access = loadAccess(cwd);
  const lines: string[] = [];
  lines.push(`state dir: ${stateDir(cwd)}`);
  lines.push(`file: ${accessPath(cwd)}`);
  lines.push(`dmPolicy: ${access.dmPolicy}`);
  lines.push(`allowFrom: [${access.allowFrom.join(", ")}]`);
  const groupKeys = Object.keys(access.groups);
  if (groupKeys.length > 0) {
    lines.push(`groups:`);
    for (const [chId, policy] of Object.entries(access.groups)) {
      const af = policy.allowFrom?.length > 0 ? policy.allowFrom.join(",") : "*";
      lines.push(`  ${chId}: requireMention=${policy.requireMention}, allowFrom=${af}`);
    }
  } else {
    lines.push(`groups: (none)`);
  }
  const pendingCount = Object.keys(access.pending).length;
  lines.push(`pending: ${pendingCount} code(s)`);
  if (access.ackReaction) lines.push(`ackReaction: ${access.ackReaction}`);
  if (access.replyToMode) lines.push(`replyToMode: ${access.replyToMode}`);
  if (access.mentionPatterns) lines.push(`mentionPatterns: ${JSON.stringify(access.mentionPatterns)}`);
  return lines.join("\n");
}

function cmdAccessPair(cwd: string, code: string): string {
  const access = loadAccess(cwd);
  const entry = access.pending[code];
  if (!entry) return `pairing code "${code}" not found or expired`;
  const senderId = entry.senderId;
  const chatId = entry.chatId;
  if (!access.allowFrom.includes(senderId)) {
    access.allowFrom.push(senderId);
  }
  delete access.pending[code];
  saveAccess(cwd, access);
  // Write approved/ file for server polling
  const approvedDir = join(stateDir(cwd), "approved");
  mkdirSync(approvedDir, { recursive: true });
  writeFileSync(join(approvedDir, senderId), chatId || "");
  return `paired! added ${senderId} to allowFrom (chat: ${chatId})`;
}

function cmdAccessAllow(cwd: string, userId: string): string {
  const access = loadAccess(cwd);
  if (access.allowFrom.includes(userId)) return `${userId} already in allowFrom`;
  access.allowFrom.push(userId);
  saveAccess(cwd, access);
  return `added ${userId} to allowFrom`;
}

function cmdAccessRemove(cwd: string, userId: string): string {
  const access = loadAccess(cwd);
  access.allowFrom = access.allowFrom.filter((id) => id !== userId);
  saveAccess(cwd, access);
  return `removed ${userId} from allowFrom`;
}

function cmdAccessGroupAdd(cwd: string, channelId: string, requireMention: boolean): string {
  const access = loadAccess(cwd);
  access.groups[channelId] = {
    requireMention,
    allowFrom: [], // empty = everyone in channel
  };
  saveAccess(cwd, access);
  return `added group ${channelId} (requireMention=${requireMention}, allowFrom=*)`;
}

function cmdAccessGroupRemove(cwd: string, channelId: string): string {
  const access = loadAccess(cwd);
  delete access.groups[channelId];
  saveAccess(cwd, access);
  return `removed group ${channelId}`;
}

function cmdAccessPolicy(cwd: string, policy: string): string {
  if (!["pairing", "allowlist", "disabled"].includes(policy)) {
    return `invalid policy "${policy}" — must be pairing|allowlist|disabled`;
  }
  const access = loadAccess(cwd);
  access.dmPolicy = policy as Access["dmPolicy"];
  saveAccess(cwd, access);
  return `dmPolicy set to "${policy}"`;
}

function cmdStatus(cwd: string): string {
  const dir = stateDir(cwd);
  const lines: string[] = [];
  lines.push(`state dir: ${dir}`);
  lines.push(`is global: ${dir === GLOBAL_STATE}`);

  const envPath = join(dir, ".env");
  if (existsSync(envPath)) {
    const content = readFileSync(envPath, "utf-8");
    const hasToken = content.includes("DISCORD_BOT_TOKEN");
    lines.push(`bot token: ${hasToken ? "present (value hidden)" : "missing"}`);
  } else {
    lines.push(`bot token: no .env file`);
  }

  const ap = join(dir, "access.json");
  if (existsSync(ap)) {
    const access = loadAccess(cwd);
    lines.push(`access.json: present`);
    lines.push(`  dmPolicy: ${access.dmPolicy}`);
    lines.push(`  allowFrom: ${access.allowFrom.length} user(s)`);
    lines.push(`  groups: ${Object.keys(access.groups).length} channel(s)`);
    lines.push(`  pending: ${Object.keys(access.pending).length} code(s)`);
  } else {
    lines.push(`access.json: not found`);
  }

  const mode = process.env.DISCORD_ACCESS_MODE;
  lines.push(`access mode: ${mode === "static" ? "static (frozen)" : "dynamic (default)"}`);

  return lines.join("\n");
}

function cmdStateInit(cwd: string): string {
  const local = join(cwd, ".discord-state");
  if (existsSync(local)) return `already exists: ${local}`;
  mkdirSync(local, { recursive: true });
  mkdirSync(join(local, "inbox"), { recursive: true });
  writeFileSync(join(local, "access.json"), JSON.stringify(defaultAccess(), null, 2) + "\n");
  return `initialized: ${local}\n  access.json: default (pairing mode)\n  inbox/: created`;
}

function cmdStateLink(cwd: string): string {
  const local = join(cwd, ".discord-state");
  if (!existsSync(local)) return `no .discord-state/ in ${cwd} — run 'maw discord-channel state init' first`;
  try {
    symlinkSync(local, GLOBAL_STATE);
    return `linked: ${GLOBAL_STATE} → ${local}`;
  } catch (e: any) {
    if (e.code === "EEXIST") {
      return `${GLOBAL_STATE} already exists — remove it first if you want to relink`;
    }
    return `symlink failed: ${e.message}`;
  }
}

function cmdStateDir(cwd: string): string {
  return stateDir(cwd);
}

// ── Help ─────────────────────────────────────────────────────────────────

function helpText(): string {
  return [
    "usage: maw discord-channel <subcommand> [args]",
    "",
    "token:",
    "  token list                    — list discord bot tokens in pass vault",
    "  token show <name>             — check if token exists (value hidden)",
    "  token save <name>             — save bot token from stdin to pass",
    "  token load <name>             — load bot token from pass → .env in state dir",
    "",
    "access:",
    "  access show                   — display current access.json",
    "  access pair <code>            — approve a pairing code",
    "  access allow <userId>         — add user to DM allowlist",
    "  access remove <userId>        — remove user from DM allowlist",
    "  access group add <channelId> [--mention]  — opt-in a guild channel",
    "  access group rm <channelId>   — remove a guild channel",
    "  access policy <mode>          — set dmPolicy (pairing|allowlist|disabled)",
    "",
    "status:                         — overview of state dir, token, access",
    "",
    "state:",
    "  state init                    — create .discord-state/ in cwd",
    "  state link                    — symlink global → local .discord-state/",
    "  state dir                     — print resolved state directory path",
  ].join("\n");
}

// ── Entry ────────────────────────────────────────────────────────────────

export default async function handler(ctx: InvokeContext): Promise<InvokeResult> {
  const logs: string[] = [];
  const origLog = console.log;
  console.log = (...a: any[]) => {
    if (ctx.writer) ctx.writer(...a);
    else logs.push(a.map(String).join(" "));
  };
  const out = () => logs.join("\n");

  try {
    const args: string[] = ctx.source === "cli" ? (ctx.args as string[]) : [];
    const positional = args.filter((a) => !a.startsWith("--"));
    const flags = args.filter((a) => a.startsWith("--"));
    const sub = positional[0];
    const sub2 = positional[1];
    const sub3 = positional[2];
    const cwd = process.cwd();

    if (!sub) {
      console.log(helpText());
      return { ok: true, output: out() || helpText() };
    }

    switch (sub) {
      case "token": {
        switch (sub2) {
          case "list":
          case "ls":
            console.log(cmdTokenList());
            break;
          case "show":
            if (!sub3) { console.log("usage: maw discord-channel token show <name>"); break; }
            console.log(cmdTokenShow(sub3));
            break;
          case "save": {
            if (!sub3) { console.log("usage: maw discord-channel token save <name>"); break; }
            // Read token from stdin (for piping: echo $TOKEN | maw discord-channel token save mybot)
            const input = await new Promise<string>((resolve) => {
              let buf = "";
              process.stdin.resume();
              process.stdin.on("data", (chunk) => { buf += chunk.toString(); });
              process.stdin.on("end", () => resolve(buf.trim()));
              setTimeout(() => resolve(buf.trim()), 3000);
            });
            if (!input) { console.log("no token provided on stdin"); break; }
            console.log(cmdTokenSave(sub3, input));
            break;
          }
          case "load":
            if (!sub3) { console.log("usage: maw discord-channel token load <name>"); break; }
            console.log(cmdTokenLoad(sub3, cwd));
            break;
          default:
            console.log("usage: maw discord-channel token <list|show|save|load> [name]");
        }
        return { ok: true, output: out() };
      }

      case "access": {
        switch (sub2) {
          case "show":
            console.log(cmdAccessShow(cwd));
            break;
          case "pair":
            if (!sub3) { console.log("usage: maw discord-channel access pair <code>"); break; }
            console.log(cmdAccessPair(cwd, sub3));
            break;
          case "allow":
            if (!sub3) { console.log("usage: maw discord-channel access allow <userId>"); break; }
            console.log(cmdAccessAllow(cwd, sub3));
            break;
          case "remove":
            if (!sub3) { console.log("usage: maw discord-channel access remove <userId>"); break; }
            console.log(cmdAccessRemove(cwd, sub3));
            break;
          case "group": {
            const action = sub3;
            const channelId = positional[3];
            if (action === "add" && channelId) {
              const mention = flags.includes("--mention");
              console.log(cmdAccessGroupAdd(cwd, channelId, mention));
            } else if ((action === "rm" || action === "remove") && channelId) {
              console.log(cmdAccessGroupRemove(cwd, channelId));
            } else {
              console.log("usage: maw discord-channel access group <add|rm> <channelId> [--mention]");
            }
            break;
          }
          case "policy":
            if (!sub3) { console.log("usage: maw discord-channel access policy <pairing|allowlist|disabled>"); break; }
            console.log(cmdAccessPolicy(cwd, sub3));
            break;
          default:
            console.log("usage: maw discord-channel access <show|pair|allow|remove|group|policy> [args]");
        }
        return { ok: true, output: out() };
      }

      case "status":
        console.log(cmdStatus(cwd));
        return { ok: true, output: out() };

      case "state": {
        switch (sub2) {
          case "init":
            console.log(cmdStateInit(cwd));
            break;
          case "link":
            console.log(cmdStateLink(cwd));
            break;
          case "dir":
            console.log(cmdStateDir(cwd));
            break;
          default:
            console.log("usage: maw discord-channel state <init|link|dir>");
        }
        return { ok: true, output: out() };
      }

      default:
        console.log(helpText());
        return { ok: false, error: `unknown subcommand "${sub}"`, output: out() };
    }
  } catch (e: any) {
    return { ok: false, error: out() || e.message, output: out() };
  } finally {
    console.log = origLog;
  }
}
