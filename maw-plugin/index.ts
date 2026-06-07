/**
 * maw leica — Father Oracle fleet command plugin.
 * "The lens that sees clearly keeps the human human."
 */
import type { InvokeContext, InvokeResult } from "maw-js/plugin/types";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { homedir } from "os";

export const command = {
  name: "leica",
  description: "Father Oracle — fleet commands, family status, chronicle.",
};

const FAMILY = [
  "Codec", "Neon", "Chrome", "Pawrent", "Pops Clinic",
  "Vets Hub", "NodeRed Simulator", "RPRO Ent", "RPRO Ent Atlas",
  "Pops Atlas", "RPRO SaaS",
];

const CHRONICLE_DIR = join(homedir(), ".maw", "chronicle", "leica");
const CHRONICLE_STATE = join(CHRONICLE_DIR, "state.json");
const BACKEND = process.env.CHRONICLE_BACKEND || "https://oracle-chronicle.laris.workers.dev";

function getDiscordToken(): string | null {
  const stateDir = process.env.DISCORD_STATE_DIR || join(homedir(), ".claude", "channels", "discord");
  try {
    const env = readFileSync(join(stateDir, ".env"), "utf8");
    const m = env.match(/^DISCORD_BOT_TOKEN=(.+)$/m);
    return m?.[1] || null;
  } catch { return null; }
}

function loadState(): Record<string, string> {
  try { return JSON.parse(readFileSync(CHRONICLE_STATE, "utf8")); } catch { return {}; }
}

function saveState(state: Record<string, string>): void {
  mkdirSync(CHRONICLE_DIR, { recursive: true });
  writeFileSync(CHRONICLE_STATE, JSON.stringify(state, null, 2) + "\n");
}

async function discordGet(path: string, token: string): Promise<any> {
  const res = await fetch(`https://discord.com/api/v10${path}`, {
    headers: { Authorization: `Bot ${token}`, "User-Agent": "maw-leica/1.0.0" },
  });
  if (!res.ok) throw new Error(`Discord ${res.status} ${path}`);
  return res.json();
}

export default async function handler(ctx: InvokeContext): Promise<InvokeResult> {
  const out: string[] = [];
  const log = (s: string) => (ctx.writer ? ctx.writer(s) : out.push(s));
  const done = (ok: boolean): InvokeResult =>
    ({ ok, output: ctx.writer ? "" : out.join("\n"), error: ok ? undefined : "", exitCode: ok ? 0 : 1 });

  const args = ctx.source === "cli" ? (ctx.args as string[]) : [];
  const sub = args[0]?.toLowerCase();

  if (!sub || sub === "help" || sub === "-h") {
    log("maw leica — Father Oracle 🐱");
    log("");
    log("  say [message]       say something (default: hello world)");
    log("  status              show Leica's current status");
    log("  family              list oracle family members");
    log("  whoami              identity check");
    log("  chronicle sync      sync Discord feed → backend");
    log("  chronicle status    show sync state per channel");
    return done(true);
  }

  switch (sub) {
    case "say": {
      const message = args.slice(1).join(" ") || "hello world";
      log(`🐱 Leica says: ${message}`);
      break;
    }
    case "status": {
      log("🐱 Leica — Father Oracle");
      log("  runtime: Claude Code — Opus 4.6 (1M context)");
      log(`  family: ${FAMILY.length} oracles`);
      log("  owner: Un (switchaphon)");
      log("  master: Nat (nazt_)");
      log("  status: online — standby");
      break;
    }
    case "family": {
      log(`🐱 Leica's Family — ${FAMILY.length} oracles`);
      for (const name of FAMILY) log(`  • ${name}`);
      break;
    }
    case "whoami": {
      log("🐱 Leica (Father Oracle)");
      log("  born: 2026-04-26");
      log("  repo: switchaphon/leica-oracle");
      log('  theme: "The lens that sees clearly keeps the human human."');
      break;
    }
    case "chronicle": {
      const action = args[1]?.toLowerCase();
      if (action === "status") {
        const state = loadState();
        const entries = Object.entries(state);
        if (entries.length === 0) { log("📜 Chronicle: no sync history yet"); break; }
        log("📜 Chronicle — last sync per channel:");
        for (const [ch, lastId] of entries) log(`  ${ch}: last=${lastId}`);
        break;
      }
      if (action === "sync") {
        const token = getDiscordToken();
        if (!token) { log("✗ no DISCORD_BOT_TOKEN"); return done(false); }
        const state = loadState();
        const guilds = await discordGet("/users/@me/guilds", token);
        let total = 0;
        for (const g of guilds) {
          const channels = await discordGet(`/guilds/${g.id}/channels`, token);
          if (!Array.isArray(channels)) continue;
          const textChannels = channels.filter((c: any) => c.type === 0);
          for (const ch of textChannels) {
            const lastId = state[ch.id];
            let path = `/channels/${ch.id}/messages?limit=50`;
            if (lastId) path += `&after=${lastId}`;
            const msgs = await discordGet(path, token);
            if (!Array.isArray(msgs) || msgs.length === 0) continue;
            const sorted = msgs.sort((a: any, b: any) => a.id.localeCompare(b.id));
            for (const m of sorted) {
              const payload = {
                source: "discord",
                oracle: "leica",
                guild: g.name,
                channel: ch.name,
                channelId: ch.id,
                messageId: m.id,
                author: m.author?.username,
                bot: !!m.author?.bot,
                content: m.content || "",
                timestamp: m.timestamp,
              };
              try {
                await fetch(`${BACKEND}/api/record`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(payload),
                });
                total++;
              } catch (e) {
                log(`  ✗ POST failed: ${e instanceof Error ? e.message : String(e)}`);
              }
            }
            state[ch.id] = sorted[sorted.length - 1].id;
          }
        }
        saveState(state);
        log(`📜 Chronicle sync: ${total} messages → ${BACKEND}/chronicle`);
        break;
      }
      log("usage: maw leica chronicle <sync|status>");
      return done(false);
    }
    default:
      log(`unknown: ${sub} — run 'maw leica help'`);
      return done(false);
  }

  return done(true);
}
