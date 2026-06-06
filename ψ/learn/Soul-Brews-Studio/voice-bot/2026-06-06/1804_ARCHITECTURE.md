# Voice-Bot Architecture Analysis

**Project**: Codey Voice Bot — Discord voice channel transcriber + AI secretary  
**Repository**: https://github.com/Soul-Brews-Studio/voice-bot  
**Runtime**: Bun 1.0+ with TypeScript  
**Document date**: 2026-06-06

---

## Overview

Codey is a real-time voice transcription bot that joins Discord voice channels, captures audio from all speakers, transcribes speech-to-text, and responds with AI-generated answers via text-to-speech. It operates as a stateful actor per guild, maintaining session state across multiple voice channels within a Discord ecosystem.

### Core Features

- **Real-time per-speaker transcription** — timestamped, speaker-attributed speech-to-text
- **Voice trigger replies** — detects "Codey answer" and responds via Groq LLM + TTS
- **Multiple TTS voices** — macOS Kanya/Narisa, Edge TTS (Niwat/Premwadee), Google Chirp
- **Transcript export** — Markdown format with timestamps + participant list
- **Raw audio recording** — full session WAV file on leave
- **Auto-leave** — exits when alone (5min) or silent (15min), or on `/codey stay` hard cap
- **Cost tracking** — per-session breakdown of STT/TTS/LLM charges
- **Web UI** — live transcript view at `localhost:8080`

---

## Directory Structure

```
voice-bot/
├── src/                    # Main codebase
│   ├── index.ts           # Entry point — Discord client + slash commands
│   ├── voice-session.ts   # Per-guild session state machine (idle→recording→leaving)
│   ├── audio-pipeline.ts  # Per-speaker opus→PCM→WAV chunking
│   ├── transcriber.ts     # STT dispatcher
│   ├── stt/               # Speech-to-text backends
│   │   ├── index.ts       # Dispatcher
│   │   ├── whisperCpp.ts  # Local whisper.cpp (default)
│   │   ├── google.ts      # Google Cloud Speech
│   │   ├── groq.ts        # Groq Whisper Large V3
│   │   ├── hallucinations.ts  # Filter false positives (UPS, school names, etc.)
│   │   ├── types.ts       # Common types
│   │   └── whisperServerManager.ts  # Manages local whisper.cpp HTTP daemon
│   ├── tts.ts             # TTS dispatcher
│   ├── tts/               # Text-to-speech backends
│   │   ├── index.ts       # Dispatcher
│   │   ├── macSay.ts      # macOS `say` (free, Thai)
│   │   ├── edge.ts        # Microsoft Edge TTS (free)
│   │   ├── google.ts      # Google Cloud TTS (paid, Chirp)
│   │   └── types.ts       # Common types
│   ├── voice-config.ts    # Runtime voice profile switching
│   ├── brain.ts           # Groq LLM integration (reply generation)
│   ├── think-bridge.ts    # Claude session IPC (via maw hey)
│   ├── transcript-writer.ts  # Markdown export
│   ├── discord-transcript.ts  # (Likely Discord-specific formatting)
│   ├── handoff.ts         # Post-session copy + notify (via maw)
│   ├── session-archive.ts # VPS archival of sessions
│   ├── live-feed.ts       # JSONL event stream for web UI
│   ├── ui-server.ts       # Web UI server (localhost:8080)
│   ├── command-watcher.ts # Polls VOICE_CMD_DIR for cross-process IPC
│   ├── command-types.ts   # VoiceCommand / VoiceResult types
│   ├── remote-control-poller.ts  # (Infrastructure support)
│   ├── speak-state.ts     # Global speak/trigger mode + allowlist
│   ├── cost.ts            # Cost estimation + pricing
│   ├── auto-shutdown.ts   # Graceful shutdown on idle
│   ├── pid-file.ts        # PID tracking
│   ├── register-commands.ts  # Discord slash command registration
│   └── commands.ts        # Slash command definitions
├── test/                  # Unit tests (Bun test)
│   ├── config.test.ts
│   ├── trigger.test.ts
│   ├── reply-queue.test.ts
│   └── transcript-writer.test.ts
├── ui/                    # Web UI assets
│   └── index.html
├── deploy/yoi-ui/         # Deployment config (systemd service)
│   ├── package.json
│   ├── server.ts
│   └── yoi-ui.service
├── package.json           # Bun project manifest
├── tsconfig.json
├── README.md
└── IMPLEMENTATION-PLAN.md

```

---

## Core Abstractions

### 1. VoiceSession (src/voice-session.ts)

**State machine**: `idle → connecting → recording → leaving → idle`

Maintains per-guild session state:
- Voice connection to Discord
- Active audio capture pipelines (per speaker)
- Transcript segments accumulated during session
- Participant tracking (name/ID pairs)
- Costs (STT/TTS/LLM per call)
- Auto-flush and auto-leave state

**Key methods**:
- `connect(args: ConnectArgs)` — join a voice channel, setup receiver listener
- `disconnect()` — clean up connection, reset state
- `flush()` — write transcript snapshot to disk (.md file)
- `speakReply(text)` — synthesize text via TTS + play in voice channel
- `addNote(text, author)` — manual transcript annotation
- `getStatus()` — return current session metadata
- `setPersistent(ms)` — override auto-leave for N milliseconds (/codey stay)
- `isPersistent()` — check if in stay mode

**Lifecycle hooks**:
- `onChunk` — called when audio chunk captured (usually calls `transcribeAndCleanup`)
- `onComplete` — called when speaker stops (stream ends via silence detection)

### 2. Audio Pipeline (src/audio-pipeline.ts)

**Goal**: Convert Discord opus frames → PCM → periodic WAV chunks → transcription

**Strategy**: Long-utterance safe (avoid lost audio after 30s)
- Each user speaking → open opus subscription (auto-ends on silence)
- Opus frames → decode to PCM (48kHz stereo s16le) via `prism-media`
- Buffer fills → every `chunkFlushMs` (default 8s), snapshot to WAV
- Send WAV to `onChunk` handler, reset buffer, continue capturing
- On stream 'end' (silence threshold reached) → final flush + `onComplete`

**Key classes/functions**:
- `startSpeakerCapture(connection, userId, config, onChunk, onComplete)` — spawn listener for one speaker
- `RawAudioRecorder` — accumulates all PCM across session → encodes single WAV on disconnect
- `encodeRawWav(pcm, outputPath)` — spawn ffmpeg to convert PCM → WAV

**Silence handling**: Configurable via `SILENCE_THRESHOLD_MS` (default 1500ms). No audio loss — streams stay open, periodic snapshots preserve long utterances.

### 3. STT Dispatcher (src/transcriber.ts, src/stt/index.ts)

**Backend selection**: `STT_BACKEND` env variable
- `whisper-cpp` (default) — local whisper.cpp + Metal acceleration, free
- `google` — Google Cloud Speech-to-Text, paid
- `groq` — Groq Whisper Large V3, free tier

**Post-processing**: All transcriptions run through `hallucinations.ts`
- Filters common false positives: "UPS โรงเรียน", "ขอบคุณที่ติดตาม", etc.
- Returns empty string if hallucinated → caller treats as silence (no segment)

**Privacy**: WAV file deleted after transcription (via `transcribeAndCleanup`).

**Whisper.cpp server management**: If backend is whisper.cpp, `startWhisperServer()` spawns a local HTTP daemon at startup (~3s model load). Subsequent calls hit local endpoint (no network).

### 4. TTS Dispatcher (src/tts/index.ts, src/voice-config.ts)

**Voice profiles**: Runtime-switchable via `/codey voice <profile>`

| Profile | Backend | Voice | Cost |
|---------|---------|-------|------|
| kanya / kanya-compact | macOS `say` | Kanya Thai | Free |
| narisa | macOS `say` | Narisa Thai | Free |
| niwat | Edge TTS | th-TH-NiwatNeural (male) | Free |
| premwadee | Edge TTS | th-TH-PremwadeeNeural (female) | Free |
| leda | Google TTS | en-US-Chirp3-HD-Leda | ~$30/1M chars |

**Config**: Resolved per-call from `voice-config.ts` (NOT cached), so `/codey voice` changes apply immediately to next reply.

**Backends**:
- `macSay.ts` — spawns `say` command with voice name + text file input
- `edge.ts` — calls Microsoft Edge TTS API (free, cloud)
- `google.ts` — calls Google Cloud Text-to-Speech API (paid)

### 5. Brain (Groq LLM) (src/brain.ts)

**Model**: Groq Llama 3.3 70B (via OpenAI-compatible API)  
**Use**: Generate spoken replies when user triggers "Codey answer"

**System prompt** (configurable via `BRAIN_SYSTEM` env):
```
You are โคดี้ (Codey), AI secretary + voice transcriber, speaking Thai.
Respond briefly (1-2 short sentences — will be spoken aloud).
Voice: warm, professional, helpful. Use "ครับ" particles.
Never pretend human. If asked who you are: "โคดี้ AI ของ BM ครับ".
```

**Context**: Recent conversation segments (up to 50) passed to aid responses.  
**Token limit**: Max 200 output tokens (keeps replies spoken-friendly).  
**Fallback**: If `USE_BRAIN=false`, use `CANNED_REPLY` env (default: "ค่ะ โคดี้ฟังอยู่ค่ะ").

**Cost**: Tracks input/output tokens per call for cost reporting.

### 6. Think Bridge (Claude Session IPC) (src/think-bridge.ts)

**Purpose**: Request deep AI replies via Claude (Opus 4.7) running in a separate tmux session.

**Flow**:
1. Voice-bot writes request JSON to `~/.claude/channels/codey/think-requests/<requestId>.json`
2. Spawns `maw hey codey "<notification>"` (pastes message into tmux window)
3. Claude session wakes up, reads request context, writes reply to `think-replies/<requestId>.txt`
4. Voice-bot polls reply file every 500ms (up to 90s timeout)
5. Returns reply text → caller TTS-plays it

**Triggers**:
- `/codey think <msg>` slash command → text mode (reply shown in ephemeral Discord message)
- Voice trigger + `BRAIN_MODE=claude-session` → voice mode (reply TTS-played in channel)

**Cleanup**: Caller deletes request + reply files after consumption.

---

## Data Flow: Voice → Text → AI → Response

### 1. User speaks in voice channel

```
User audio → Discord gateway → bot receiver (subscribed per user)
           → opus frames → audio-pipeline.ts
           → decode opus → PCM (48kHz stereo)
           → buffer → periodic WAV snapshots
           → WAV file saved to /tmp/
```

### 2. Transcription

```
WAV → transcriber.ts (dispatch to STT backend)
    ↓
    STT backend (whisper-cpp | google | groq)
    ↓
    hallucinations.ts (filter false positives)
    ↓
    TranscriptSegment { speaker, text, startedAt, endedAt }
    ↓
    added to session.segments[]
    ↓
    DELETE WAV file (privacy)
```

### 3. Trigger Detection

```
segment.text → isTriggered() check
            → test against TRIGGER_RE (literal phrases: "โคดี้", "ตอบหน่อย", etc.)
            → test against FUZZY_TRIGGER_RE (loose spelling variants)
            ↓
    IF triggered:
      - check trigger mode (owner-only | anyone | selected allow-list)
      - check if speak mode is ON
      ↓
      request reply
```

### 4. Reply Generation

**Option A: Groq LLM (fast)**
```
segment.text + context → brain.ts
                       → Groq Llama 3.3 70B
                       → 1-2 sentence reply
                       → track token usage for costs
```

**Option B: Claude via think-bridge (deep)**
```
segment.text + context → write to think-requests/
                       → spawn maw hey codey
                       → wait for Claude to write think-replies/
                       → poll up to 90s
                       → return reply
```

### 5. TTS Synthesis

```
reply text → voice-config.getActiveVoice()
           → TTS backend (macSay | edge | google)
           → MP3/WAV audio file
           → play in Discord voice channel via audio player
           → DELETE audio file (privacy)
           → track char count for costs
```

### 6. Session Flush

```
all segments → transcript-writer.ts → renderTranscript()
            → Markdown output (waterfall: newest first)
            → write to transcripts/<session-id>.md
            ↓
            copyToDownloads() → ~/Downloads/codey-discord-voice/
            ↓
            handoff() → maw hey codey <notification>
                      (Claude summarizes + posts to Discord)
```

---

## Entry Points

### 1. Main Process: `src/index.ts`

**Boot sequence**:
1. Load `DISCORD_TOKEN` from .env, validate `DC_OWNER_IDS`
2. Create Discord.js Client with voice intents
3. If `STT_BACKEND=whisper-cpp`, start local whisper server
4. On `ClientReady`:
   - Start command watcher (polls VOICE_CMD_DIR)
   - Start UI server (port 8080)
   - Start remote control poller
   - Start auto-leave watchers (alone + silence)
   - Start persistent-mode cap watcher
   - Start memory reporter
5. Register slash command handlers
6. Listen for `InteractionCreate` (slash commands + buttons)
7. Listen for `VoiceStateUpdate` (track participants)
8. On signal (SIGTERM/SIGINT): flush all sessions + disconnect + cleanup

**Slash commands** (owner-only):
- `/codey help` — show usage
- `/codey join [channel-id]` — connect to voice channel
- `/codey leave` — disconnect + save + handoff
- `/codey save` — snapshot transcript (keep recording)
- `/codey note <text>` — add manual annotation
- `/codey status` — show session state
- `/codey speak-on / speak-off` — mute/unmute mic + trigger replies
- `/codey say <text>` — immediate TTS (no AI)
- `/codey think <msg>` — request deep Claude reply
- `/codey trigger <mode>` — set trigger mode (anyone | owner-only | selected)
- `/codey voice <profile>` — switch voice profile
- `/codey stay [hours]` — override auto-leave (max 24h)
- `/codey unstay` — cancel stay mode

### 2. Slash Command Registration: `src/register-commands.ts`

Run once after deploying:
```bash
bun src/register-commands.ts
```

Registers all `/codey` commands globally (or per-guild if `DISCORD_GUILD_ID` set).

### 3. Cross-Process Commands: `src/command-watcher.ts`

**Purpose**: Allow external processes (Telegram, CLI, other bots) to control voice-bot via file IPC.

**Mechanism**:
- Polls `VOICE_CMD_DIR` every 500ms for new `.json` files
- Each file: `{ command: "join" | "leave" | ..., args: {...} }`
- Executes via VoiceSession
- Writes result `.json` to `VOICE_RESULT_DIR`
- Deletes input file

**Commands**:
- `join { channelId, guildId }`
- `leave { guildId }`
- `save { guildId }`
- `say { guildId, text }`
- `think { guildId, text, timeoutMs }`
- `speak-on / speak-off { guildId }`
- `trigger { guildId, action, userId? }`
- `voice { guildId, profile }`
- `status { guildId }`

---

## Configuration (Environment Variables)

### Discord

| Var | Default | Notes |
|-----|---------|-------|
| `DISCORD_TOKEN` | (required) | Bot token from Discord Developer Portal |
| `DISCORD_GUILD_ID` | (optional) | Single-guild fallback; fallback if no guild context |
| `DC_OWNER_IDS` | (required) | Comma-separated user IDs for slash command access |

### STT

| Var | Default | Notes |
|-----|---------|-------|
| `STT_BACKEND` | whisper-cpp | whisper-cpp \| google \| groq |
| `GROQ_API_KEY` | (if groq) | API key for Groq Whisper |
| `GOOGLE_APPLICATION_CREDENTIALS` | (if google) | Path to JSON service account key |
| `SILENCE_THRESHOLD_MS` | 1500 | Stream auto-ends after this silence |
| `MAX_CHUNK_MS` | 30000 | (deprecated; kept for env compat) |

### TTS

| Var | Default | Notes |
|-----|---------|-------|
| `TTS_BACKEND` | mac-say | mac-say \| google \| edge |
| `MAC_SAY_VOICE` | Kanya | macOS voice name |
| `GOOGLE_APPLICATION_CREDENTIALS` | (if google) | Service account key (same as STT) |

### Voice Config

| Var | Default | Notes |
|-----|---------|-------|
| `BRAIN_MODE` | claude-session | claude-session \| gemini |
| `BRAIN_MODEL` | llama-3.3-70b-versatile | Groq model for replies |
| `BRAIN_SYSTEM` | (Thai system prompt) | Custom system instruction for LLM |
| `USE_BRAIN` | true | Set to false to use `CANNED_REPLY` instead |
| `CANNED_REPLY` | ค่ะ โคดี้ฟังอยู่ค่ะ | Fallback reply if brain disabled |
| `CLAUDE_REPLY_TIMEOUT_MS` | 90000 | Timeout for `/codey think` |

### Auto-Leave

| Var | Default | Notes |
|-----|---------|-------|
| `AUTO_FLUSH_MS` | 900000 (15min) | Transcript auto-save interval |
| `AUTO_LEAVE_ALONE_MS` | 300000 (5min) | Exit if no humans in channel |
| `AUTO_LEAVE_SILENCE_MS` | 900000 (15min) | Exit if no speech detected |
| `STAY_MAX_HOURS` | 24 | Cap for `/codey stay` command |

### Storage

| Var | Default | Notes |
|-----|---------|-------|
| `TRANSCRIPT_DIR` | transcripts | Where to write .md files |
| `RAW_AUDIO_DIR` | ~/Downloads/codey-discord-voice | Where to save session WAW files |
| `SAVE_RAW_AUDIO` | true | Set to false to skip WAV recording |
| `VOICE_CMD_DIR` | ~/.claude/channels/codey/voice-cmd | Cross-process command polling |
| `VOICE_RESULT_DIR` | ~/.claude/channels/codey/voice-result | Results of cross-process commands |

### UI & Monitoring

| Var | Default | Notes |
|-----|---------|-------|
| `UI_PORT` | 8080 | Web UI server port |
| `LIVE_FEED` | true | Enable event stream (JSONL) |
| `LIVE_FEED_MAX_BYTES` | 10485760 (10MB) | Auto-rotate live-feed if oversized |
| `LIVE_FEED_REMOTE_URL` | (optional) | POST events to VPS dashboard |
| `LIVE_FEED_REMOTE_TOKEN` | (optional) | Auth token for remote ingest |
| `MEMORY_REPORT_MS` | 600000 (10min) | Memory usage log interval |

### Cost Estimation

| Var | Default | Notes |
|-----|---------|-------|
| `STT_USD_PER_MIN` | 0.024 | Google Cloud Speech pricing |
| `TTS_USD_PER_1M_CHARS` | 16 | Google Chirp3-HD pricing |
| `GEMINI_INPUT_USD_PER_1M_TOKENS` | 0.075 | Gemini 2.5 Flash |
| `GEMINI_OUTPUT_USD_PER_1M_TOKENS` | 0.3 | Gemini 2.5 Flash |

### Infrastructure

| Var | Default | Notes |
|-----|---------|-------|
| `MAW_BIN` | maw | Path to maw binary (for `maw hey` calls) |
| `MAW_TARGET` | codey | tmux session name for think-bridge |

---

## Dependencies

### Runtime

```json
{
  "@discordjs/opus": "^0.10.0",        // opus encoding
  "@discordjs/voice": "^0.19.2",       // Discord voice connection
  "@google-cloud/speech": "^7.3.1",    // STT (optional backend)
  "@google-cloud/text-to-speech": "^6.4.1", // TTS (optional backend)
  "discord.js": "^14.16.0",            // Discord bot framework
  "ffmpeg-static": "^5.2.0",           // WAV encoding
  "opusscript": "^0.1.1",              // Opus codec fallback
  "prism-media": "^1.3.5",             // Audio pipeline
  "sodium-native": "^5.1.0",           // AEAD encryption (xchacha20poly1305_ietf)
  "tweetnacl": "^1.0.3"                // Encryption fallback
}
```

**Critical**: `sodium-native` is required for Discord's new AEAD encryption. Without it, voice packets get dropped silently → 0 chunks captured.

### Development

```json
{
  "@types/bun": "latest",
  "@types/node": "^22.0.0",
  "typescript": "^5.5.0"
}
```

### Build/Deployment

- **Runtime**: Bun 1.0+
- **ffmpeg**: External binary (statically bundled via ffmpeg-static)
- **maw**: Optional (for think-bridge + handoff notifications)

---

## State Persistence & Graceful Shutdown

### Session Lifecycle

1. **Idle** → user calls `/codey join`
2. **Connecting** → joining voice channel
3. **Recording** → active audio capture + transcription
4. **Leaving** → flushing transcript + disconnecting
5. **Idle** → ready for next join

### On Process Termination (SIGTERM/SIGINT)

1. For each active session:
   - `flush()` → write final transcript
   - `disconnect()` → clean up connection + audio pipelines
2. Stop command watcher
3. Stop UI server
4. Stop remote control poller
5. Stop whisper server (if running)
6. Delete PID file
7. Exit

All flushes are best-effort — failures are logged but don't block shutdown.

### Auto-Leave Triggers

1. **Alone timeout**: Channel empties of humans for >5min (unless `/codey stay`)
2. **Silence timeout**: No human speech for >15min (unless `/codey stay`)
3. **Persistent cap**: Hard expire after N hours (set via `/codey stay <hours>`)
4. **Manual**: `/codey leave` or `/voice-out` command

---

## Cost Tracking (src/cost.ts)

Per-session breakdown:

```typescript
interface CostMetrics {
  sttBilledSec: number;        // billable seconds (15-sec increments for Google)
  sttCallCount: number;
  ttsBilledChars: number;      // billable chars for paid TTS
  ttsCallCount: number;
  geminiInputTokens: number;   // if using Gemini brain
  geminiOutputTokens: number;
  geminiCallCount: number;
  claudeReplyCount: number;    // via think-bridge (no per-call cost, subscription)
}
```

**Free backends** (always $0):
- STT: whisper-cpp (local)
- TTS: mac-say (on-device), edge-tts (cloud-free), niwat/premwadee

**Paid backends**:
- STT: Google Cloud Speech ($0.024/min, 15-sec increments)
- TTS: Google Chirp ($16/1M chars)

Cost report printed on `/codey leave` and appended to handoff notification.

---

## Testing

Bun test framework. Run:

```bash
bun test
```

Key test files:
- `test/config.test.ts` — voice profile switching
- `test/trigger.test.ts` — trigger phrase detection
- `test/reply-queue.test.ts` — (likely concurrent reply handling)
- `test/transcript-writer.test.ts` — markdown rendering

---

## Notable Design Decisions

### 1. Long-Utterance Safety

Audio pipeline keeps opus streams open indefinitely (no force-destroy at maxChunkMs). Periodic WAV snapshots preserve long utterances. Avoids the "lost audio after 30s" bug where destroying mid-utterance dropped frames until Discord re-emitted "speaking start".

### 2. Trigger Phrase Filtering

**Literal phrases** (BUILTIN_TRIGGERS): exact matches for "โคดี้", "ตอบหน่อย", etc. Low false-positive risk because owner-only mode already filters by user ID.

**Fuzzy patterns** (FUZZY_TRIGGER_RE): loose regex for common Whisper mishears. Catches Groq transcription drift without requiring per-case tuning.

### 3. Per-Call TTS Voice Resolution

Voice profile is resolved **per TTS call** (not cached at module load). Allows `/codey voice` command to take immediate effect without restart.

### 4. Hallucination Filtering

Post-process all transcriptions through `hallucinations.ts` to filter Whisper-specific false positives (e.g., "UPS โรงเรียน" from random noise). Returns empty string → caller treats as silence (no segment).

### 5. Think-Bridge File IPC

Claude replies requested via file-based IPC (`think-requests/` → `maw hey codey` → `think-replies/`). Avoids tmux comms issues (send-keys gets stuck in buffer) while staying within existing Leica infrastructure (maw/tmux).

### 6. Waterfall Transcript Order

Transcript segments rendered "newest first" (reverse chronological). Mimics chat UIs where latest messages appear at top. Internal array stays chronological (simpler iteration).

### 7. Cost Estimation Over Metering

Costs tracked in-memory and reported per-session. No external billing service. Allows fine-grained cost breakdown per session for the user's cost awareness.

---

## Integration Points

### Leica Oracle Integration

**Handoff notification**: On `/codey leave` or auto-leave, voice-bot calls `handoff()` which:
1. Copies transcript to `~/Downloads/codey-discord-voice/`
2. Spawns `maw hey codey <notification>` → pastes into Leica (Father Oracle) tmux window
3. Leica reads transcript, summarizes, optionally posts to Discord

**Think-bridge**: For deep AI replies, voice-bot writes request to `think-requests/`, spawns `maw hey codey`, waits for reply. Requires Leica to be running in tmux.

### Remote Control via File IPC

`command-watcher.ts` polls `VOICE_CMD_DIR` for commands from external sources (CLI, Telegram bot, Discord slash command proxy). Allows cross-process orchestration without direct API coupling.

### Web UI (localhost:8080)

`ui-server.ts` serves simple HTML dashboard. `live-feed.ts` appends JSONL events. UI polls or tails the feed to show live transcripts.

---

## Performance Characteristics

### Memory

- Per speaker: ~1-2MB (opus buffers + PCM)
- Per session: ~5-20MB (depending on transcript size + raw audio)
- Per process: ~100-200MB baseline (Discord client + handlers)

Memory reporter logs every 10min (configurable) → helps detect leaks during long sessions.

### Latency

- **Audio capture → WAV chunk**: ~8s (default `chunkFlushMs`)
- **WAV → transcription**: ~1-2s (whisper.cpp on M-series); ~2-5s (Google Cloud)
- **Transcription → trigger detection**: <10ms
- **Trigger → Groq reply**: ~1-2s
- **Reply text → TTS**: ~0.5-2s (macOS say is instant; Edge/Google add network latency)
- **TTS → Discord playback**: ~100ms

End-to-end (user speaks → bot replies): ~5-15s for Groq; ~15-30s for Claude via think-bridge.

### Throughput

- **Audio capture**: 48kHz stereo s16le = 192kB/s per speaker. 2 speakers = 384kB/s.
- **Transcription queue**: Sequential processing (one chunk at a time). Can add parallelism if needed.
- **Cross-process commands**: ~100 commands/sec (polling 500ms interval).

---

## Known Limitations

1. **Emoji in transcripts**: Waterfall order + emoji might not render cleanly in all Markdown viewers.
2. **Long silence handling**: Hard 15min cap means very quiet meetings get auto-left even if participants are engaged.
3. **Groq API rate limits**: Free tier has quota; heavy usage might hit limits (fallback to canned reply or paid tier).
4. **macOS only**: Some TTS profiles (Kanya voice) require macOS. Linux users need Edge/Google.
5. **Think-bridge dependency**: Deep replies require Leica running in tmux with maw available. Graceful fallback to Groq if unavailable.
6. **Single guild per process**: Slash commands work per-guild, but design targets single guild. Multi-guild would need per-guild session queues.

---

## Future Extensibility

### Adding a New STT Backend

1. Create `src/stt/backend-name.ts`
2. Export `transcribeBackendName(wavPath: string): Promise<TranscribeResult>`
3. Add dispatch in `src/stt/index.ts`
4. Add `STT_BACKEND=backend-name` env option

### Adding a New TTS Voice Profile

1. Add entry to `PROFILES` object in `src/voice-config.ts`
2. Implement backing voice in corresponding TTS backend file
3. `setActiveVoice(profile)` instantly applies it (no restart)

### Adding a New Trigger Mode

1. Extend `TriggerMode` type in `src/speak-state.ts`
2. Add logic to `canTrigger()` function
3. Add handler in `/codey trigger <mode>` command

---

## Summary

**Voice-bot** is a sophisticated Discord voice transcription + AI reply bot. Its architecture emphasizes:

- **Robustness**: Long-utterance safety, graceful shutdown, best-effort error handling
- **Cost awareness**: Per-session cost tracking + optional free backends
- **Extensibility**: Pluggable STT/TTS backends, runtime voice switching, custom trigger phrases
- **Integration**: File-based IPC with Leica Oracle, cross-process command handling, web UI for monitoring
- **Privacy**: Audio files deleted post-transcription, no persistent storage of raw audio

The codebase is well-modularized, with clear separation between Discord integration (index.ts), audio mechanics (audio-pipeline.ts), transcription (transcriber.ts), synthesis (tts.ts), and orchestration (voice-session.ts).
