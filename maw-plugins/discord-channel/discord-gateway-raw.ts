#!/usr/bin/env bun
/**
 * Leica's Discord Gateway Client — raw WebSocket, zero dependencies.
 *
 * Connects to Discord Gateway directly (no discord.js), reads messages
 * from allowed channels, and relays to stdout or maw hey.
 *
 * Proves: I can read Discord messages with my own bot token,
 * using only the WebSocket API documented at:
 * https://discord.com/developers/docs/events/gateway
 *
 * Usage:
 *   DISCORD_BOT_TOKEN=xxx bun run discord-gateway-raw.ts
 *   DISCORD_BOT_TOKEN=xxx bun run discord-gateway-raw.ts --channel 1512079809021214730
 */

// ── Types ────────────────────────────────────────────────────────────────

interface GatewayPayload {
  op: number;
  d: any;
  s: number | null;
  t: string | null;
}

interface MessageAuthor {
  id: string;
  username: string;
  bot?: boolean;
}

interface Attachment {
  id: string;
  filename: string;
  size: number;
  content_type?: string;
  url: string;
}

interface MessageCreate {
  id: string;
  channel_id: string;
  author: MessageAuthor;
  content: string;
  timestamp: string;
  attachments?: Attachment[];
  referenced_message?: { id: string } | null;
}

interface GatewayError {
  code: string;
  message: string;
}

// ── Config ───────────────────────────────────────────────────────────────

const TOKEN = process.env.DISCORD_BOT_TOKEN;
if (!TOKEN) {
  process.stderr.write("discord-gateway-raw: DISCORD_BOT_TOKEN required\n");
  process.exit(1);
}

const args = process.argv.slice(2);
const channelIdx = args.indexOf("--channel");
const FILTER_CHANNEL = channelIdx >= 0 ? args[channelIdx + 1] : null;
const VERBOSE = args.includes("--verbose");

// Discord Gateway intents (bitfield)
// GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768) | DIRECT_MESSAGES(4096)
const INTENTS = 1 | 512 | 32768 | 4096;

const GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json";

// ── State ────────────────────────────────────────────────────────────────

let seq: number | null = null;
let sessionId: string | null = null;
let resumeUrl: string | null = null;
let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
let heartbeatAcked = true;
let ws: WebSocket | null = null;
let messageCount = 0;
let botUserId: string | null = null;

// ── Gateway Connection ───────────────────────────────────────────────────

function connect(url: string = GATEWAY_URL): void {
  log(`connecting to ${url.replace(/\?.*/, "")}`);

  ws = new WebSocket(url);

  ws.onopen = () => {
    log("websocket open");
  };

  ws.onmessage = (event: MessageEvent) => {
    const payload = parsePayload(event.data);
    if (!payload) return;

    // Track sequence number for heartbeat + resume
    if (payload.s !== null) seq = payload.s;

    switch (payload.op) {
      case 10: // Hello — start heartbeat + identify
        handleHello(payload.d);
        break;
      case 11: // Heartbeat ACK
        heartbeatAcked = true;
        break;
      case 0: // Dispatch — events
        handleDispatch(payload);
        break;
      case 1: // Heartbeat request from server
        sendHeartbeat();
        break;
      case 7: // Reconnect
        log("server requested reconnect");
        reconnect();
        break;
      case 9: // Invalid Session
        log(`invalid session (resumable=${payload.d})`);
        if (payload.d) {
          setTimeout(() => reconnect(), 1000 + Math.random() * 4000);
        } else {
          sessionId = null;
          seq = null;
          setTimeout(() => connect(), 1000 + Math.random() * 4000);
        }
        break;
      default:
        if (VERBOSE) log(`unknown op: ${payload.op}`);
    }
  };

  ws.onerror = (event: Event) => {
    log(`websocket error: ${(event as ErrorEvent).message ?? "unknown"}`);
  };

  ws.onclose = (event: CloseEvent) => {
    log(`websocket closed: ${event.code} ${event.reason}`);
    stopHeartbeat();

    // Reconnect on recoverable closes
    const unrecoverable = [4004, 4010, 4011, 4012, 4013, 4014];
    if (unrecoverable.includes(event.code)) {
      log(`unrecoverable close code ${event.code} — exiting`);
      process.exit(1);
    }
    setTimeout(() => reconnect(), 2000 + Math.random() * 3000);
  };
}

// ── Handlers ─────────────────────────────────────────────────────────────

function handleHello(d: { heartbeat_interval: number }): void {
  const interval = d.heartbeat_interval;
  log(`heartbeat interval: ${interval}ms`);

  // Start heartbeat with jitter for first beat
  heartbeatAcked = true;
  stopHeartbeat();
  setTimeout(() => {
    sendHeartbeat();
    heartbeatTimer = setInterval(() => {
      if (!heartbeatAcked) {
        log("heartbeat not acked — reconnecting");
        ws?.close(4000, "heartbeat timeout");
        return;
      }
      sendHeartbeat();
    }, interval);
  }, Math.random() * interval);

  // Identify or Resume
  if (sessionId && seq !== null) {
    sendResume();
  } else {
    sendIdentify();
  }
}

function handleDispatch(payload: GatewayPayload): void {
  switch (payload.t) {
    case "READY": {
      sessionId = payload.d.session_id;
      resumeUrl = payload.d.resume_gateway_url;
      botUserId = payload.d.user?.id ?? null;
      log(`ready — session=${sessionId}, bot=${payload.d.user?.username}#${payload.d.user?.discriminator}`);
      log(`guilds: ${payload.d.guilds?.length ?? 0}`);
      break;
    }

    case "RESUMED":
      log("resumed successfully");
      break;

    case "MESSAGE_CREATE": {
      const msg = payload.d as MessageCreate;
      handleMessage(msg);
      break;
    }

    default:
      if (VERBOSE) log(`dispatch: ${payload.t}`);
  }
}

function handleMessage(msg: MessageCreate): void {
  // Skip own messages (prevent loop)
  if (msg.author.bot && msg.author.id === botUserId) return;

  // Filter by channel if specified
  if (FILTER_CHANNEL && msg.channel_id !== FILTER_CHANNEL) return;

  messageCount++;

  // Format attachment info
  const atts = (msg.attachments ?? [])
    .map((a) => `${a.filename} (${a.content_type ?? "?"}, ${(a.size / 1024).toFixed(0)}KB)`)
    .join("; ");

  const attSuffix = atts ? ` [attachments: ${atts}]` : "";

  // Output to stdout — proof that we received the message
  const line = `[${msg.timestamp}] #${msg.channel_id} ${msg.author.username}: ${msg.content}${attSuffix}`;
  console.log(line);

  // Also write structured JSON to stderr for machine consumption
  const structured = {
    type: "message",
    channel_id: msg.channel_id,
    message_id: msg.id,
    author: msg.author.username,
    author_id: msg.author.id,
    content: msg.content,
    timestamp: msg.timestamp,
    is_bot: msg.author.bot ?? false,
    attachment_count: (msg.attachments ?? []).length,
  };
  process.stderr.write(`MSG:${JSON.stringify(structured)}\n`);
}

// ── Send functions ───────────────────────────────────────────────────────

function sendHeartbeat(): void {
  heartbeatAcked = false;
  send({ op: 1, d: seq });
}

function sendIdentify(): void {
  log("sending identify");
  send({
    op: 2,
    d: {
      token: TOKEN,
      intents: INTENTS,
      properties: {
        os: process.platform,
        browser: "leica-gateway",
        device: "leica-gateway",
      },
    },
  });
}

function sendResume(): void {
  log(`resuming session ${sessionId} at seq ${seq}`);
  send({
    op: 6,
    d: {
      token: TOKEN,
      session_id: sessionId,
      seq,
    },
  });
}

function send(data: Record<string, unknown>): void {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

// ── Reconnect ────────────────────────────────────────────────────────────

function reconnect(): void {
  stopHeartbeat();
  ws?.close();
  const url = resumeUrl ? `${resumeUrl}/?v=10&encoding=json` : GATEWAY_URL;
  connect(url);
}

function stopHeartbeat(): void {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────

function parsePayload(data: unknown): GatewayPayload | null {
  try {
    const str = typeof data === "string" ? data : new TextDecoder().decode(data as ArrayBuffer);
    return JSON.parse(str) as GatewayPayload;
  } catch {
    log("failed to parse gateway payload");
    return null;
  }
}

function log(msg: string): void {
  process.stderr.write(`[leica-gw] ${msg}\n`);
}

// ── Shutdown ─────────────────────────────────────────────────────────────

let shuttingDown = false;
function shutdown(): void {
  if (shuttingDown) return;
  shuttingDown = true;
  log(`shutting down — received ${messageCount} messages total`);
  stopHeartbeat();
  ws?.close(1000, "shutdown");
  setTimeout(() => process.exit(0), 1000);
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);

// ── Boot ─────────────────────────────────────────────────────────────────

log("leica discord gateway client v0.1.0");
log(`filter channel: ${FILTER_CHANNEL ?? "all"}`);
log(`intents: ${INTENTS} (GUILDS|GUILD_MESSAGES|MESSAGE_CONTENT|DM)`);
connect();
