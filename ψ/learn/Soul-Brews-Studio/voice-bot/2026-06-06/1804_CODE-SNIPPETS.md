# Voice-Bot Code Snippets — Complete Architecture Reference

**Source**: `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/voice-bot/`
**Collected**: 2026-06-06 @ 18:04 UTC
**Language**: TypeScript (Bun runtime)

---

## 1. Main Entry Point — `src/index.ts`

### Discord Client Initialization
```typescript
import "sodium-native"; // Required for Discord's AEAD encryption (xchacha20poly1305_ietf)

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.GuildMembers,
  ],
  partials: [Partials.Channel],
});

const sessions = new Map<string, VoiceSession>(); // Per-guild voice connection state
```

### Configuration Constants
```typescript
const AUTO_FLUSH_MS = Number(process.env.AUTO_FLUSH_MS) || 15 * 60 * 1000;
const AUTO_LEAVE_ALONE_MS = Number(process.env.AUTO_LEAVE_ALONE_MS) || 5 * 60 * 1000;
const AUTO_LEAVE_SILENCE_MS = Number(process.env.AUTO_LEAVE_SILENCE_MS) || 15 * 60 * 1000;
const SILENCE_THRESHOLD_MS = Number(process.env.SILENCE_THRESHOLD_MS) || 1500;
const MAX_CHUNK_MS = Number(process.env.MAX_CHUNK_MS) || 30_000;
```

### Guild Resolution (Multi-Guild Support)
```typescript
function resolveActiveGuildId(interaction: ChatInputCommandInteraction): string | null {
  if (interaction.guildId) return interaction.guildId;
  for (const [gid, s] of sessions) {
    if (s.state !== "idle") return gid; // First active session
  }
  return FALLBACK_GUILD_ID ?? null;
}

function sessionFor(guildId: string): VoiceSession {
  let s = sessions.get(guildId);
  if (!s) {
    s = new VoiceSession();
    sessions.set(guildId, s);
  }
  return s;
}
```

### Owner-Only Authorization Gate
```typescript
const OWNER_IDS = new Set(
  (process.env.DC_OWNER_IDS ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean),
);

// Silent ignore (no refusal message to avoid leaking authorization rules)
if (!OWNER_IDS.has(interaction.user.id)) {
  console.log(`[codey-voice] ignored /${cmdName} from non-owner user=${interaction.user.id}`);
  return;
}
```

---

## 2. Voice Session State Machine — `src/voice-session.ts`

### SessionState Lifecycle
```typescript
export type SessionState = "idle" | "connecting" | "recording" | "leaving";

export class VoiceSession {
  private _state: SessionState = "idle";
  private _connection: VoiceConnection | null = null;
  private _segments: TranscriptSegment[] = [];
  private _lastHumanSpeechAt = 0; // For silence auto-leave watcher
  private _persistentUntil = 0;   // /codey stay mode (skip auto-leave)
  private _replyQueue: Array<{ triggerText: string; queuedAt: number }> = [];
}
```

### Connect Flow
```typescript
async connect(args: ConnectArgs): Promise<void> {
  if (this._state !== "idle") {
    throw new Error(`cannot connect: session is ${this._state}`);
  }
  this._state = "connecting";
  
  // Default-mute on join when speak mode is OFF
  const startMuted = !isSpeakMode(args.guildId);
  const conn = joinVoiceChannel({
    channelId: args.channelId,
    guildId: args.guildId,
    adapterCreator: args.adapterCreator,
    selfDeaf: false,
    selfMute: startMuted,
  });

  try {
    await entersState(conn, VoiceConnectionStatus.Ready, 15_000);
    this._state = "recording";
  } catch (e) {
    conn.destroy();
    this._state = "idle";
    throw new Error(`failed to enter voice channel within 15s: ${(e as Error).message}`);
  }
  
  // Wire per-speaker capture
  conn.receiver.speaking.on("start", (userId: string) => {
    startSpeakerCapture(conn, userId, cfg, async (chunk) => {
      await whisperHandler(chunk);
    });
  });

  // Create empty .md immediately at join
  const { filepath } = await this.flush();
  
  // Auto-flush every N ms (15-min default)
  if (autoFlushMs > 0) {
    this._autoFlushTimer = setInterval(async () => {
      if (this._segments.length === 0) return;
      await this.flush();
    }, autoFlushMs);
  }
}
```

### Trigger Detection & Reply Queueing
```typescript
const BUILTIN_TRIGGERS = [
  "โคดี้", "น้องโคดี้", "โคดี้จ๋า", // Call by name
  "ขอดี", "โค้ดดี้", // Whisper mishears
  "ตอบหน่อย", "ช่วยตอบ", // Action-style
];

const FUZZY_TRIGGER_RE = 
  /(?:ตอบ\s*(?:ห[่้]?น[่้]?[อ้า]?[ยา]?|นอย|หนอย)|ช่วย\s*(?:ตอบ|ฟัง)|ติดต่อไปแล้ว|อับน้?อย)/i;

function isTriggered(text: string): boolean {
  return TRIGGER_RE.test(text) || FUZZY_TRIGGER_RE.test(text);
}

// Per-speaker pending trigger — accumulates chunks until speaker is silent
private _accumulateTrigger(userId: string, chunkText: string): void {
  const existing = this._pendingTriggers.get(userId);
  if (existing) {
    clearTimeout(existing.timer);
    existing.text = `${existing.text} ${chunkText}`.trim();
    existing.timer = setTimeout(
      () => this._flushPendingTrigger(userId),
      VoiceSession.TRIGGER_DEBOUNCE_MS, // 1.5s default
    );
    return;
  }
  const timer = setTimeout(
    () => this._flushPendingTrigger(userId),
    VoiceSession.TRIGGER_DEBOUNCE_MS,
  );
  this._pendingTriggers.set(userId, { text: chunkText, timer, startedAt: Date.now() });
}

// Reply FIFO queue with merging
private async _runReplyWorker(): Promise<void> {
  while (this._replyQueue.length > 0 && this._state === "recording") {
    const first = this._replyQueue.shift()!;
    const merged = [first];

    // Drain adjacent items within MERGE_WINDOW_MS (20s default)
    while (
      this._replyQueue.length > 0 &&
      this._replyQueue[0]!.queuedAt - merged[merged.length - 1]!.queuedAt < 
      VoiceSession.MERGE_WINDOW_MS
    ) {
      merged.push(this._replyQueue.shift()!);
    }

    // Drop if stale (60s default)
    const oldestAge = Date.now() - first.queuedAt;
    if (oldestAge > VoiceSession.STALE_REPLY_MS) {
      console.log(`[voice-session] dropping ${merged.length} stale trigger(s)`);
      continue;
    }

    await this._handleTriggerReply(
      merged.length === 1 ? first.triggerText : 
      `มีคนเรียกโคดี้ติดกัน ${merged.length} ครั้ง...`
    );
  }
}
```

### TTS Reply Pipeline (Per-Speaker Context)
```typescript
private async _handleTriggerReply(triggerText: string): Promise<void> {
  let replyText = CANNED_REPLY;
  
  if (USE_BRAIN) {
    try {
      // Build per-speaker context (last 50 segments per speaker, not global)
      const { ctx, speakerCount } = this._buildPerSpeakerContext();

      if (BRAIN_MODE === "claude-session") {
        const { reply, requestId } = await requestClaudeReply({
          triggerText,
          channelName: this.channelName ?? "voice",
          context: ctx,
          speakerCount,
          timeoutMs: 120_000,
        });
        if (reply) {
          replyText = reply;
          this._cost.claudeReplyCount++;
        }
      } else {
        // Fallback: Groq/Gemini
        const generated = await generateReply(triggerText, ctx);
        if (generated) replyText = generated;
      }
    } catch (e) {
      console.warn(`[voice-session] brain failed → using canned: ${e?.message}`);
    }
  }
  
  await this.speakReply(replyText);
}

private _buildPerSpeakerContext(): { ctx: ContextSegment[]; speakerCount: number } {
  const real = this._segments.filter((s) => !s.isNote && s.text.trim());
  const bySpeaker = new Map<string, typeof real>();
  
  for (const s of real) {
    const arr = bySpeaker.get(s.speakerId) ?? [];
    arr.push(s);
    bySpeaker.set(s.speakerId, arr);
  }
  
  const perSpeakerLast50: typeof real = [];
  for (const [, segs] of bySpeaker) {
    perSpeakerLast50.push(...segs.slice(-50)); // Last 50 PER speaker
  }
  
  perSpeakerLast50.sort((a, b) => a.startedAt - b.startedAt);
  
  const ctx: ContextSegment[] = perSpeakerLast50.map((s) => ({
    speaker: s.speaker,
    text: s.text,
    startedAt: s.startedAt,
  }));
  
  return { ctx, speakerCount: bySpeaker.size };
}
```

### TTS Playback
```typescript
async speakReply(text: string): Promise<void> {
  if (this._state !== "recording" || !this._connection) {
    throw new Error(`speakReply needs recording state`);
  }
  
  // Track TTS billing (per character)
  this._cost.ttsCallCount++;
  this._cost.ttsBilledChars += text.length;
  
  const ttsPath = await synthesizeTts(text);
  const player = createAudioPlayer();
  const subscription = this._connection.subscribe(player);
  
  try {
    const resource = createAudioResource(ttsPath);
    player.play(resource);
    await entersState(player, AudioPlayerStatus.Playing, 5_000);
    await entersState(player, AudioPlayerStatus.Idle, 60_000);
  } finally {
    subscription?.unsubscribe();
    player.stop(true);
    deleteTtsFile(ttsPath);
    
    // Record Codey's reply in transcript
    this._segments.push({
      speaker: "🌀 Codey",
      speakerId: "codey-tts",
      startedAt: Date.now() - 1000,
      endedAt: Date.now(),
      text,
    });
    
    await this.flush(); // Live update
  }
}
```

### Persistent Mode (/codey stay)
```typescript
isPersistent(): boolean {
  return this._persistentUntil > 0 && Date.now() < this._persistentUntil;
}

setPersistent(ms: number): void {
  this._persistentUntil = Date.now() + Math.max(0, ms);
}

clearPersistent(): void {
  this._persistentUntil = 0;
}
```

---

## 3. Audio Pipeline — `src/audio-pipeline.ts`

### Per-Speaker Capture (Opus → PCM → WAV Chunks)
```typescript
export function startSpeakerCapture(
  connection: VoiceConnection,
  userId: string,
  config: PipelineConfig,
  onChunk: ChunkHandler,
  onComplete?: () => void,
): void {
  const opusStream = receiver.subscribe(userId, {
    end: {
      behavior: EndBehaviorType.AfterSilence,
      duration: config.silenceThresholdMs, // 1500ms default
    },
  });

  const pcmDecoder = new prism.opus.Decoder({
    rate: 48_000,
    channels: 2,
    frameSize: 960,
  });

  const pcmStream = opusStream.pipe(pcmDecoder);
  let buffers: Buffer[] = [];
  let flushSeq = 0;
  let ended = false;

  // Periodic flush (8s default) — long utterances split into chunks
  const flushIntervalMs = config.chunkFlushMs ?? 8_000;
  const flushTimer = setInterval(() => {
    if (ended) return;
    void dispatchBuffer(true); // isPartial = true
  }, flushIntervalMs);

  pcmStream.on("data", (chunk: Buffer) => {
    buffers.push(chunk);
    // Append to session-level raw audio for final WAV export
    if (config.guildId) {
      getRawRecorder(config.guildId).append(chunk);
    }
  });

  pcmStream.on("end", async () => {
    ended = true;
    clearInterval(flushTimer);
    // Wait for in-flight flush, then final flush
    while (flushing) await new Promise((r) => setTimeout(r, 50));
    if (buffers.length > 0) {
      await dispatchBuffer(false); // isPartial = false
    }
    onComplete?.();
  });
}

const dispatchBuffer = async (isPartial: boolean): Promise<void> => {
  if (buffers.length === 0) return;
  const pcm = Buffer.concat(buffers);
  buffers = [];
  
  // Drop final chunks < 1500ms (Whisper hallucinates on noise)
  const durationMs = Date.now() - subChunkStartedAt;
  if (!isPartial && durationMs < minFinalChunkMs) {
    console.log(`[audio] drop short final chunk dur=${durationMs}ms`);
    return;
  }

  const wavPath = join(TMP_DIR, `${startedAt}_${userId}_p${flushSeq}.wav`);
  await encodeWav(pcm, wavPath); // 48kHz stereo → 16kHz mono for Whisper

  const chunk: AudioChunk = {
    userId,
    wavPath,
    startedAt,
    endedAt: Date.now(),
    durationMs,
    byteSize: pcm.length,
    isPartial,
  };

  await onChunk(chunk);
};
```

### WAV Encoding (PCM → FFmpeg)
```typescript
function encodeWav(pcm48kStereo: Buffer, outputPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const ff = spawn(FFMPEG_BIN, [
      "-hide_banner", "-loglevel", "error",
      "-f", "s16le",
      "-ar", "48000", // Input: 48kHz stereo
      "-ac", "2",
      "-i", "-",
      "-ar", "16000", // Output: 16kHz mono (Whisper friendly)
      "-ac", "1",
      "-f", "wav",
      "-y", outputPath,
    ]);

    ff.stdin?.write(pcm48kStereo);
    ff.stdin?.end();
  });
}
```

### Raw Audio Recording (Full Session WAV)
```typescript
class RawAudioRecorder {
  private buffers: Buffer[] = [];
  private startedAt = Date.now();

  append(pcm: Buffer): void {
    this.buffers.push(pcm);
  }

  async save(channelName: string): Promise<string | null> {
    if (!SAVE_RAW_AUDIO || this.buffers.length === 0) return null;
    
    const pcm = Buffer.concat(this.buffers);
    const ymd = `${d.getFullYear()}-${padStart(d.getMonth() + 1, 2)}...`;
    const hm = `${padStart(d.getHours(), 2)}${padStart(d.getMinutes(), 2)}`;
    const safe = channelName.replace(/[^a-zA-Z0-9_-]/g, "_");
    const outPath = join(RAW_AUDIO_DIR, `${ymd}_${hm}_${safe}.wav`);
    
    await encodeRawWav(pcm, outPath);
    console.log(`[audio] raw recording saved: ${outPath}`);
    return outPath;
  }
}
```

---

## 4. Speech-to-Text Dispatch — `src/stt/index.ts`

### STT Backend Dispatcher
```typescript
export type SttBackend = "whisper-cpp" | "google" | "groq";

const BACKEND: SttBackend = (process.env.STT_BACKEND as SttBackend) || "whisper-cpp";

async function transcribeRaw(wavPath: string): Promise<TranscribeResult> {
  if (BACKEND === "whisper-cpp") {
    const { transcribeWhisperCpp } = await import("./whisperCpp.ts");
    return transcribeWhisperCpp(wavPath);
  }
  if (BACKEND === "google") {
    const { transcribeGoogle } = await import("./google.ts");
    return transcribeGoogle(wavPath);
  }
  if (BACKEND === "groq") {
    const { transcribeGroq } = await import("./groq.ts");
    return transcribeGroq(wavPath);
  }
  throw new Error(`unknown STT_BACKEND: ${BACKEND}`);
}

export async function transcribe(wavPath: string): Promise<TranscribeResult> {
  const raw = await transcribeRaw(wavPath);
  
  // Post-process: drop hallucinated text
  if (raw.text && isHallucination(raw.text)) {
    console.log(`[stt] hallucination dropped: "${raw.text.slice(0, 80)}"`);
    return { ...raw, text: "" };
  }
  
  return raw;
}

export async function transcribeAndCleanup(wavPath: string): Promise<TranscribeResult> {
  try {
    return await transcribe(wavPath);
  } finally {
    try {
      await unlink(wavPath); // Privacy: delete post-STT
    } catch {}
  }
}
```

### Whisper.cpp HTTP Client — `src/stt/whisperCpp.ts`
```typescript
const PORT = Number(process.env.WHISPER_SERVER_PORT) || 9000;
const HOST = process.env.WHISPER_SERVER_HOST || "127.0.0.1";
const PATH = process.env.WHISPER_SERVER_PATH || "/transcribe";
const LANG = process.env.WHISPER_LANGUAGE || "th";

export async function transcribeWhisperCpp(wavPath: string): Promise<TranscribeResult> {
  const form = new FormData();
  
  if (typeof Bun !== "undefined") {
    form.set("file", Bun.file(wavPath));
  } else {
    const { readFile } = await import("node:fs/promises");
    const buf = await readFile(wavPath);
    form.set("file", new Blob([buf], { type: "audio/wav" }), "chunk.wav");
  }
  
  form.set("language", LANG);
  form.set("response_format", "json");
  form.set("temperature", "0");

  const endpoint = `http://${HOST}:${PORT}${PATH}`;
  const res = await fetch(endpoint, { method: "POST", body: form });
  
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`whisper-server HTTP ${res.status}: ${body.slice(0, 200)}`);
  }
  
  const data = (await res.json()) as { text?: string; language?: string };
  return {
    text: (data.text ?? "").trim(),
    language: data.language ?? LANG,
  };
}

export async function pingWhisperServer(timeoutMs = 1500): Promise<boolean> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const res = await fetch(`http://${HOST}:${PORT}/`, { signal: ctl.signal });
    return res.ok || res.status === 404;
  } catch {
    return false;
  } finally {
    clearTimeout(t);
  }
}
```

---

## 5. AI Response Generation — `src/brain.ts`

### Groq LLM (OpenAI-Compatible)
```typescript
const API_KEY = process.env.GROQ_API_KEY;
const BRAIN_MODEL = process.env.BRAIN_MODEL || "llama-3.3-70b-versatile";
const API_URL = "https://api.groq.com/openai/v1/chat/completions";

const BRAIN_SYSTEM =
  `You are โคดี้ (Codey), AI secretary and voice transcriber, speaking Thai.
You are responding via voice in a Discord call to BM (your human).
Reply briefly — 1-2 short sentences — because this will be spoken aloud.
Voice characteristics: warm, professional, helpful. Use "ครับ" particles.
Never pretend to be human. If asked who you are, say "โคดี้ AI ของ BM ครับ".
Reply in Thai unless explicitly asked otherwise.

You will receive the trigger phrase (what the user just said to you) AND recent conversation context.
Decide how to respond based on intent:
- Direct question (กี่โมง, อะไร, ยังไง) → answer the question directly
- Request for opinion/summary (สรุปหน่อย, ว่าไง, เห็นด้วยไหม) → summarize or give opinion
- Greeting (สวัสดี, ได้ยินไหม) → greet back briefly
- Other → respond naturally to what was said`;

async function callGroq(
  system: string,
  userText: string,
  maxTokens = 200,
): Promise<string> {
  if (!API_KEY) {
    throw new Error("[brain] GROQ_API_KEY missing in .env");
  }
  if (!userText.trim()) return "";

  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({
      model: BRAIN_MODEL,
      messages: [
        { role: "system", content: system },
        { role: "user", content: userText },
      ],
      max_tokens: maxTokens,
      temperature: 0.7,
    }),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(`[brain] Groq HTTP ${res.status}: ${errText.slice(0, 300)}`);
  }

  const json = (await res.json()) as GroqResponse;
  _lastUsage = {
    inputTokens: json.usage?.prompt_tokens ?? 0,
    outputTokens: json.usage?.completion_tokens ?? 0,
  };
  return (json.choices?.[0]?.message?.content ?? "").trim();
}

export async function generateReply(
  userText: string,
  context?: ContextSegment[],
): Promise<string> {
  let prompt = userText;
  if (context && context.length > 0) {
    const transcript = context
      .map((s) => {
        const t = new Date(s.startedAt).toISOString().slice(11, 19);
        return `[${t}] ${s.speaker}: ${s.text}`;
      })
      .join("\n");
    
    prompt =
      `Trigger (สิ่งที่เพิ่งพูดกับคุณ): "${userText}"\n\n` +
      `บทสนทนาล่าสุด:\n---\n${transcript}\n---`;
  }
  
  return callGroq(BRAIN_SYSTEM, prompt);
}
```

---

## 6. Claude Session Bridge — `src/think-bridge.ts`

### Request-Reply File IPC Pattern
```typescript
export const THINK_REQ_DIR = join(homedir(), ".claude", "channels", "codey", "think-requests");
export const THINK_REPLY_DIR = join(homedir(), ".claude", "channels", "codey", "think-replies");

export interface ThinkRequest {
  requestId: string;
  triggerText: string;
  triggeredAt: string;
  channelName: string;
  speakerCount: number;
  segmentCount: number;
  context: ContextSegment[];
  replyPath: string;
}

export async function requestClaudeReply(args: {
  triggerText: string;
  channelName: string;
  context: ContextSegment[];
  speakerCount: number;
  timeoutMs?: number;
  mode?: "voice" | "text";
}): Promise<{ reply: string | null; requestId: string }> {
  const requestId = `req-${Date.now()}-${randomUUID().slice(0, 8)}`;
  const reqPath = join(THINK_REQ_DIR, `${requestId}.json`);
  const replyPath = join(THINK_REPLY_DIR, `${requestId}.txt`);

  await mkdir(THINK_REQ_DIR, { recursive: true });
  await mkdir(THINK_REPLY_DIR, { recursive: true });

  const payload: ThinkRequest = {
    requestId,
    triggerText: args.triggerText,
    triggeredAt: new Date().toISOString(),
    channelName: args.channelName,
    speakerCount: args.speakerCount,
    segmentCount: args.context.length,
    context: args.context,
    replyPath,
  };
  await writeFile(reqPath, JSON.stringify(payload, null, 2));

  // Notify Claude session via maw
  const mode = args.mode ?? "voice";
  const profile = getActiveProfile();
  const resolved = getActiveVoice();
  
  const notif =
    `🌀 [voice-bot] โคดี้ถูกเรียก (${args.channelName})\n` +
    `Trigger: "${args.triggerText.slice(0, 200)}"\n` +
    `Context: ${args.context.length} segments / ${args.speakerCount} speaker(s)\n` +
    `Read: ${reqPath}\n` +
    `Reply: ${replyPath}\n` +
    `Rules: Thai only, สั้น, ลงท้าย ค่ะ/นะคะ, no markdown. ` +
    `TTS via ${profile} (${resolved.voice}).`;

  sendMaw(notif);

  // Poll for reply file (500ms interval, default 90s timeout)
  const reply = await pollForReply(replyPath, args.timeoutMs ?? 90_000);
  
  return { reply, requestId };
}

async function pollForReply(
  replyPath: string,
  timeoutMs: number,
): Promise<string | null> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await fileExists(replyPath)) {
      const txt = (await readFile(replyPath, "utf8")).trim();
      if (txt) return txt;
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  return null;
}

function sendMaw(notif: string): void {
  try {
    const proc = spawn("maw", ["hey", MAW_TARGET || "codey", notif], {
      stdio: "ignore",
      detached: true,
    });
    proc.unref();
  } catch (e) {
    console.warn(`[think-bridge] spawn maw failed:`, e);
  }
}

export async function cleanupRequest(requestId: string): Promise<void> {
  for (const p of [
    join(THINK_REQ_DIR, `${requestId}.json`),
    join(THINK_REPLY_DIR, `${requestId}.txt`),
  ]) {
    try {
      await unlink(p);
    } catch {}
  }
}
```

---

## 7. Text-to-Speech Dispatch — `src/tts/index.ts`

### Runtime Voice Profile Selection
```typescript
export async function synthesizeTts(text: string): Promise<TtsFile> {
  if (!text.trim()) throw new Error("synthesizeTts: empty text");
  const v = getActiveVoice(); // Resolve at call-time, not load-time

  if (v.backend === "mac-say") {
    const { synthesizeMacSay } = await import("./macSay.ts");
    return synthesizeMacSay(text, v.voice);
  }
  if (v.backend === "edge") {
    const { synthesizeEdge } = await import("./edge.ts");
    return synthesizeEdge(text, v.voice);
  }
  if (v.backend === "google") {
    const { synthesizeGoogle } = await import("./google.ts");
    return synthesizeGoogle(text, v.voice, v.languageCode);
  }
  throw new Error(`unknown backend in profile: ${v.backend}`);
}

export function deleteTtsFile(path: string): void {
  try {
    unlinkSync(path);
  } catch {
    // already gone
  }
}

export function ttsBackend(): TtsBackend {
  return getActiveVoice().backend;
}
```

### Voice Configuration — `src/voice-config.ts`
```typescript
export type VoiceProfile =
  | "kanya"         // macOS Kanya (Enhanced) — free
  | "kanya-compact" // macOS Kanya (Compact fallback)
  | "narisa"        // macOS Narisa Thai — free alternative
  | "niwat"         // Edge TTS Thai male — free
  | "premwadee"     // Edge TTS Thai female — free
  | "leda";         // Google Chirp3-HD (multilingual) — paid

const PROFILES: Record<VoiceProfile, ResolvedVoice> = {
  "kanya": {
    backend: "mac-say",
    voice: "Kanya (Enhanced)",
    label: "Kanya Enhanced (macOS, Thai, free)",
    costNote: "$0 — on-device",
  },
  "leda": {
    backend: "google",
    voice: "en-US-Chirp3-HD-Leda",
    languageCode: "en-US",
    label: "Leda — Google Chirp3-HD (multilingual, paid)",
    costNote: "~$30 / 1M chars",
  },
};

function defaultProfile(): VoiceProfile {
  const backend = (process.env.TTS_BACKEND || "mac-say").toLowerCase();
  if (backend === "google") return "leda";
  const voice = (process.env.MAC_SAY_VOICE || "Kanya").toLowerCase();
  if (voice.includes("narisa")) return "narisa";
  if (voice.includes("enhanced")) return "kanya";
  return "kanya-compact";
}

let active: VoiceProfile = defaultProfile();

export function getActiveVoice(): ResolvedVoice {
  return PROFILES[active];
}

export function setActiveVoice(profile: VoiceProfile): ResolvedVoice {
  if (!(profile in PROFILES)) {
    throw new Error(`unknown voice profile: ${profile}`);
  }
  active = profile;
  return PROFILES[profile];
}
```

---

## 8. Transcript Export & Handoff

### Markdown Rendering — `src/transcript-writer.ts`
```typescript
export interface TranscriptSegment {
  speaker: string;
  speakerId: string;
  startedAt: number;
  endedAt: number;
  text: string;
  language?: string;
  isNote?: boolean;
  noteAuthor?: string;
}

export function renderTranscript(
  header: TranscriptHeader,
  segments: TranscriptSegment[],
): string {
  const lines: string[] = [];
  lines.push(`# Voice transcript — ${header.channelName}`);
  lines.push(
    `> Session: ${formatTimestamp(header.sessionStart)} → ${formatTimestamp(header.sessionEnd)} (${formatDurationMin(header.sessionEnd - header.sessionStart)})`,
  );
  if (header.participants.length > 0) {
    lines.push(`> Participants: ${header.participants.join(", ")}`);
  }
  lines.push(`> Recorded by Codey 🌀`);
  lines.push(`> Order: 📜 newest first (waterfall)`);
  lines.push("");
  lines.push("---");
  lines.push("");

  // Waterfall: newest segment on top
  for (let i = segments.length - 1; i >= 0; i--) {
    const s = segments[i]!;
    if (s.isNote) {
      lines.push(`## ${formatTimeOfDay(s.startedAt)} — [note from ${s.noteAuthor ?? "unknown"}]`);
    } else {
      lines.push(`## ${formatTimeOfDay(s.startedAt)} — ${s.speaker}`);
    }
    lines.push(s.text);
    lines.push("");
  }

  return lines.join("\n");
}

export async function writeTranscriptFile(
  header: TranscriptHeader,
  segments: TranscriptSegment[],
): Promise<string> {
  await mkdir(TRANSCRIPT_DIR, { recursive: true });
  const ymd = `${d.getFullYear()}-${padStart(d.getMonth() + 1, 2)}-${padStart(d.getDate(), 2)}`;
  const hm = `${padStart(d.getHours(), 2)}${padStart(d.getMinutes(), 2)}`;
  const safe = header.channelName.replace(/[^a-zA-Z0-9_-]/g, "_");
  const filename = `${ymd}_${hm}_${safe}.md`;
  const filepath = join(TRANSCRIPT_DIR, filename);
  
  const markdown = renderTranscript(header, segments);
  await writeFile(filepath, markdown, "utf8");
  
  return filepath;
}
```

### Post-Flush Handoff — `src/handoff.ts`
```typescript
const DOWNLOAD_DIR = join(homedir(), "Downloads", "codey-discord-voice");

export async function handoff(
  transcriptPath: string,
  meta: HandoffMeta = {},
): Promise<{ copied: string; notified: boolean }> {
  let copied = "";
  try {
    await mkdir(DOWNLOAD_DIR, { recursive: true });
    const dest = join(DOWNLOAD_DIR, basename(transcriptPath));
    await copyFile(transcriptPath, dest);
    copied = dest;
    console.log(`[handoff] copied transcript → ${dest}`);
  } catch (e: any) {
    console.warn(`[handoff] copy failed: ${e?.message}`);
  }

  const partsList = (meta.participants ?? []).join(", ") || "(none)";
  const durationSec = Math.floor((meta.durationMs ?? 0) / 1000);
  
  const lines = [
    `[voice-bot] session complete — channel="${meta.channelName ?? "voice"}"`,
    `duration=${durationSec}s chunks=${meta.chunkCount ?? 0} segments=${meta.segmentCount ?? 0}`,
    `participants=[${partsList}]`,
    `transcript=${copied || transcriptPath}`,
  ];
  
  if (meta.costReport) {
    lines.push("", `**💰 Cost:**`, "```", meta.costReport, "```");
  }

  // Notify Claude session + request summary + send to Discord
  const notif = lines.join("\n");
  sendMaw(notif);
  
  // Archive to VPS
  const archivePromise = archiveSessionInBackground({...});
  trackPendingArchive(archivePromise);
}
```

### Discord Transcript Send — `src/discord-transcript.ts`
```typescript
export async function sendTranscriptToDiscord(
  client: Client,
  voiceChannelId: string | undefined | null,
  filepath: string,
  channelName?: string,
  segmentCount?: number,
  replyChannelId?: string | null,
): Promise<void> {
  if (!ENABLED) {
    console.log("[discord-transcript] disabled");
    return;
  }
  
  // Priority: replyChannelId (where /yj was typed) → voice channel → env default
  const channelId = replyChannelId || voiceChannelId || DEFAULT_CHANNEL_ID || null;
  if (!channelId) {
    console.log("[discord-transcript] no target channel — skip");
    return;
  }
  
  if (!existsSync(filepath)) {
    console.warn(`[discord-transcript] file not found: ${filepath}`);
    return;
  }
  
  try {
    const ch = await client.channels.fetch(channelId);
    if (!ch || !ch.isTextBased()) {
      console.log(`[discord-transcript] channel ${channelId} not text-capable`);
      return;
    }
    
    const name = channelName ? `#${channelName}` : "voice";
    const segs = segmentCount != null ? ` · ${segmentCount} segments` : "";
    
    await (ch as any).send({
      content: `📄 **Transcript** — ${name}${segs} · Recorded by Codey 🌀`,
      files: [{ attachment: filepath, name: basename(filepath) }],
    });
    
    console.log(`[discord-transcript] ✅ sent ${basename(filepath)} → ${channelId}`);
  } catch (e: any) {
    console.warn(`[discord-transcript] failed: ${e?.message}`);
  }
}
```

---

## 9. Error Handling & Graceful Shutdown

### Auto-Leave Watchers (in index.ts)
```typescript
// Auto-leave when alone in channel
function startAutoLeaveWatcher() {
  if (AUTO_LEAVE_ALONE_MS <= 0) {
    console.log("[codey-voice] auto-leave-when-alone disabled");
    return;
  }
  setInterval(async () => {
    for (const [guildId, session] of sessions) {
      if (session.state !== "recording" || !session.channelId) continue;
      
      const vc = guild.channels.cache.get(session.channelId);
      const humans = (vc as VoiceBasedChannel).members.filter((m) => !m.user.bot);
      
      if (humans.size === 0) {
        // Persistent mode (/codey stay) overrides
        if (session.isPersistent()) {
          aloneSince.delete(guildId);
          continue;
        }
        
        if (!aloneSince.has(guildId)) {
          aloneSince.set(guildId, Date.now());
          console.log(`[codey-voice] alone in ${session.channelName} — countdown`);
        } else if (Date.now() - aloneSince.get(guildId)! > AUTO_LEAVE_ALONE_MS) {
          await performAutoLeave(session, `alone > ${AUTO_LEAVE_ALONE_MS}ms`);
        }
      } else {
        aloneSince.delete(guildId);
      }
    }
  }, 30_000);
}

// Auto-leave on silence (even if humans present)
function startAutoLeaveSilenceWatcher() {
  if (AUTO_LEAVE_SILENCE_MS <= 0) return;
  
  setInterval(async () => {
    for (const session of sessions.values()) {
      if (session.state !== "recording") continue;
      if (session.isPersistent()) continue; // Skip persistent mode
      
      const silentMs = Date.now() - session.getLastHumanSpeechAt();
      if (silentMs > AUTO_LEAVE_SILENCE_MS) {
        const mins = Math.floor(silentMs / 60_000);
        await performAutoLeave(
          session,
          `silence ${mins}min > ${Math.floor(AUTO_LEAVE_SILENCE_MS / 60_000)}min`,
        );
      }
    }
  }, 60_000);
}

// Hard cap on persistent mode (/codey stay)
function startPersistentCapWatcher() {
  setInterval(async () => {
    const now = Date.now();
    for (const session of sessions.values()) {
      if (session.state !== "recording") continue;
      const until = session.getPersistentUntil();
      if (until > 0 && now >= until) {
        session.clearPersistent();
        const hours = Math.floor((now - (session.startedAt ?? now)) / 3_600_000);
        await performAutoLeave(session, `stay expired (~${hours}h cap)`);
      }
    }
  }, 60_000);
}
```

### Graceful Shutdown
```typescript
for (const sig of ["SIGTERM", "SIGINT", "SIGHUP"] as const) {
  process.on(sig, async () => {
    console.log(`[codey-voice] received ${sig}, flushing + disconnecting all sessions...`);
    for (const [gid, s] of sessions) {
      if (s.state !== "idle") {
        try {
          await s.flush();
        } catch {}
        try {
          await s.disconnect();
          console.log(`[codey-voice] disconnected guild=${gid}`);
        } catch (e) {
          console.warn(`[codey-voice] disconnect failed for guild=${gid}:`, e);
        }
      }
    }
    client.destroy();
    try {
      await stopWhisperServer();
    } catch {}
    try {
      stopUiServer();
    } catch {}
    try {
      stopRemoteControlPoller();
    } catch {}
    try {
      unlinkPidFile();
    } catch {}
    process.exit(0);
  });
}
```

### Memory Monitoring
```typescript
function startMemoryReporter() {
  if (MEMORY_REPORT_MS <= 0) return;
  
  setInterval(() => {
    const m = process.memoryUsage();
    const fmt = (b: number) => `${(b / 1024 / 1024).toFixed(1)}MB`;
    console.log(
      `[codey-voice] mem rss=${fmt(m.rss)} heap=${fmt(m.heapUsed)}/${fmt(m.heapTotal)} ext=${fmt(m.external)}`,
    );
  }, MEMORY_REPORT_MS);
}
```

---

## 10. Key Patterns & Design Decisions

### Audio Pipeline Design (Never Force-Destroy)
- **Problem**: Destroying opus stream at maxMs mid-utterance causes silence_until_restart
- **Solution**: Keep stream open until actual silence; periodic flush (isPartial=true) captures snapshots for long utterances
- **Result**: Handles 30+ minute continuous speech without lost frames

### Trigger Debouncing
- User says: "โคดี้ ตอบ ... <pause> ... เรื่อง X"
- Instead of replying at first pause after "ตอบ", accumulate chunks until speaker silent for TRIGGER_DEBOUNCE_MS (1.5s)
- Prevents mid-sentence replies on phrase breaks

### Reply Merging
- Multiple triggers within MERGE_WINDOW_MS (20s) → single combined reply
- Avoids spammy back-to-back TTS when user triggers rapidly
- Merges if age < STALE_REPLY_MS (60s); older requests dropped

### Per-Speaker Context
- Takes last 50 segments **per speaker** (not global last 50)
- Ensures quiet speakers contribute context vs. dominant talkers
- Better opinion generation across multi-speaker sessions

### Runtime Voice Profiles
- Voice profile resolved **at every synthesizeTts() call**, not cached at startup
- User runs `/codey voice leda` → next reply uses Leda immediately (no restart)
- Enables on-the-fly cost/language switching (Thai-only → multilingual)

### File-Based IPC (think-bridge)
- voice-bot writes JSON request → `maw hey codey "<notif>"` → Claude session reads + replies
- Claude writes reply text → voice-bot polls file (500ms intervals, 90s timeout)
- Graceful fallback: timeout → canned reply; brain failure → canned reply

### Hallucination Filtering
- Every STT output post-processed through `isHallucination()`
- Known Whisper artifacts: "UPS โรงเรียน", "ขอบคุณที่ติดตาม", etc.
- Dropped text → session treats as silence (no segment recorded)

### Waterfall Transcript Format (Newest First)
- Segments stored chronologically internally
- Rendered in reverse (newest on top) for readability in long sessions
- Live-flush: every successful segment writes updated .md (near real-time)

---

## 11. Cost Tracking

### Metrics Collected
```typescript
export interface CostMetrics {
  sttBilledSec: number;        // Cloud STT: 15-sec increment billing
  sttCallCount: number;
  ttsBilledChars: number;      // Cloud TTS: per-character billing
  ttsCallCount: number;
  geminiInputTokens: number;
  geminiOutputTokens: number;
  geminiCallCount: number;
  claudeReplyCount: number;    // maw bridge: count only
  ttsProfilesUsed?: Set<VoiceProfile>;
}

export function formatCost(cost: CostMetrics): string {
  // Displays STT/TTS costs, token counts, call counts
  // Called at session.leave() for final cost report
}
```

### Billing Examples
- **STT**: Google Cloud charges per 15-sec increment. A 8-sec chunk bills as 15 sec.
- **TTS**: Google Chirp3-HD charges ~$30 / 1M characters. macOS `say` is $0.
- **Groq**: Fast, used in brain; no explicit billing tracked (fixed API call cost).

---

## References & Config

| Env Variable | Default | Purpose |
|---|---|---|
| `DISCORD_TOKEN` | required | Discord bot token |
| `DC_OWNER_IDS` | required | Comma-sep owner IDs (slash auth gate) |
| `STT_BACKEND` | `whisper-cpp` | "whisper-cpp" \| "google" \| "groq" |
| `TTS_BACKEND` | `mac-say` | "mac-say" \| "google" \| "edge" |
| `WHISPER_SERVER_PORT` | 9000 | whisper.cpp HTTP server port |
| `WHISPER_LANGUAGE` | `th` | STT language code |
| `AUTO_FLUSH_MS` | 900000 | Transcript auto-flush (15 min) |
| `AUTO_LEAVE_ALONE_MS` | 300000 | Auto-leave when alone (5 min) |
| `AUTO_LEAVE_SILENCE_MS` | 900000 | Auto-leave on silence (15 min) |
| `SILENCE_THRESHOLD_MS` | 1500 | Chunk end threshold (1.5s silence) |
| `BRAIN_MODE` | `claude-session` | "claude-session" \| "gemini" |
| `TRIGGER_DEBOUNCE_MS` | 1500 | Trigger accumulation debounce |
| `MERGE_WINDOW_MS` | 20000 | Reply merge window (20s) |
| `STALE_REPLY_MS` | 60000 | Drop stale triggers (60s) |
| `MAX_REPLY_QUEUE` | 5 | Max queued triggers before drop |
| `SAVE_RAW_AUDIO` | true | Save full session WAV |
| `RAW_AUDIO_DIR` | ~/Downloads/codey-discord-voice | Raw WAV save location |
| `TRANSCRIPT_DIR` | transcripts | Markdown transcripts dir |
| `MEMORY_REPORT_MS` | 600000 | Memory log interval (10 min) |
| `CLAUDE_REPLY_TIMEOUT_MS` | 90000 | Claude session reply timeout (90s) |

---

**End of Code Snippets Document**
