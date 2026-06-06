# Codey Voice Bot — Quick Reference

## Overview

**Codey** is a Discord voice channel transcriber and AI secretary. The bot joins voice channels, captures real-time speech-to-text (per-speaker with timestamps), replies to specific triggers with AI-generated answers via text-to-speech, and exports full session transcripts plus raw WAV recordings.

---

## Installation

### Prerequisites
- **Bun v1.0+** (runtime)
- **macOS or Linux** (for TTS)
- Discord bot token ([create here](https://discord.com/developers/applications))
- Groq API key ([free tier](https://console.groq.com))
- Google Cloud credentials (optional, for Google Chirp TTS)

### Setup Steps
```bash
git clone https://github.com/Soul-Brews-Studio/voice-bot.git
cd voice-bot
bun install
cp .env.example .env
# Edit .env with your tokens
bun src/register-commands.ts
```

---

## Environment Variables

| Variable | Description | Example / Default |
|----------|-------------|-------------------|
| `DISCORD_TOKEN` | Bot token | (required) |
| `DISCORD_APP_ID` | App ID | (required) |
| `DISCORD_GUILD_ID` | Guild / server ID | (required) |
| `DC_OWNER_IDS` | Owner user IDs (comma-separated) | (required; else all slash commands ignored) |
| `STT_BACKEND` | Speech-to-text backend | `groq` |
| `GROQ_API_KEY` | Groq API key | (required for STT) |
| `GROQ_STT_MODEL` | Whisper model | `whisper-large-v3` |
| `GROQ_STT_LANGUAGE` | STT language code | `th` (Thai) |
| `TTS_VOICE` | Default TTS voice | `th-TH-PremwadeeNeural` |
| `BRAIN_MODE` | LLM backend | `gemini` or `groq` |
| `BRAIN_MODEL` | LLM model | `llama-3.3-70b-versatile` |
| `USE_BRAIN` | Enable AI replies | `true` |
| `CANNED_REPLY` | Default response if brain disabled | `Yes, I'm listening` |
| `SILENCE_THRESHOLD_MS` | Audio silence trigger (ms) | `1500` |
| `MAX_CHUNK_MS` | Max audio chunk size (ms) | `30000` |
| `MAX_REPLY_QUEUE` | Max pending AI replies | `5` |
| `STALE_REPLY_MS` | Reply timeout (ms) | `60000` |
| `AUTO_FLUSH_MS` | Auto-save transcript (ms) | `900000` (15 min) |
| `AUTO_LEAVE_ALONE_MS` | Auto-leave if alone (ms) | `300000` (5 min) |
| `AUTO_LEAVE_SILENCE_MS` | Auto-leave if silent (ms) | `900000` (15 min) |
| `TRANSCRIPT_DIR` | Output directory | `transcripts` |
| `UI_PORT` | Web UI port (optional) | `8080` |
| `UI_PASSWORD` | Web UI password (optional) | `changeme` |
| `UI_ENABLED` | Enable web UI (optional) | `true` |

---

## Quick Start

### Run the Bot
```bash
bun src/index.ts          # Foreground
bun --watch src/index.ts  # Dev mode with reload
```

### Run in tmux
```bash
tmux new -s codey-voice -d "bun src/index.ts"
```

---

## Discord Slash Commands

All commands are invoked as `/codey <subcommand>`.

| Command | Params | Description |
|---------|--------|-------------|
| `/codey join` | — | Join invoker's voice channel, start recording & transcription |
| `/codey leave` | — | Leave voice channel, save transcript + audio WAV, end session |
| `/codey save` | — | Snapshot transcript to file mid-session (bot stays in channel) |
| `/codey note <text>` | `text` | Add manual note/annotation to transcript |
| `/codey speak-on` | — | Enable AI voice replies (TTS enabled) |
| `/codey speak-off` | — | Disable AI voice (listen-only mode) |
| `/codey say <text>` | `text` | Immediately speak text via TTS |
| `/codey think <msg>` | `msg` | Send message to Claude AI, receive spoken response |
| `/codey voice <name>` | `name` | Switch TTS voice profile |
| `/codey trigger <action>` | `action` | Manage trigger permissions (who can say "Codey answer") |
| `/codey stay [hours]` | `hours` | Keep bot in channel (max 24h) |
| `/codey status` | — | Display session info: uptime, chunks captured, token costs |

---

## Voice Profiles

Switch voices with `/codey voice <profile>`:

| Profile | Voice Name | Type | Cost | Language |
|---------|-----------|------|------|----------|
| `kanya-compact` | Kanya | macOS native | Free | Thai |
| `niwat` | Niwat | Edge TTS | Free | Thai (male) |
| `premwadee` | Premwadee | Edge TTS | Free | Thai (female) |
| `leda` | Leda | Google Chirp | ~$30/1M chars | Thai (premium) |

---

## Key Features

### Real-Time Transcription
- **Per-speaker** labeling with Discord user names
- **Timestamps** for every utterance
- **Language support** (default Thai, configurable)
- **Silence detection** (1.5s threshold, configurable)

### AI Replies
- **Trigger phrase**: Say "Codey answer" in voice channel
- **Backend**: Groq Llama 3.3 70B (free tier)
- **Response**: Queued and spoken via TTS
- **Fallback**: Canned reply if brain disabled

### Text-to-Speech
- **macOS**: System `say` command (free, Thai voice Kanya)
- **Edge TTS**: Free cloud voices (Niwat/Premwadee)
- **Google Chirp**: Premium HD voice (paid)
- **Custom**: Set via `TTS_VOICE` env var

### Session Management
- **Auto-flush**: Snapshot transcript every 15 min (configurable)
- **Auto-leave**: Exit if alone >5 min (configurable)
- **Auto-leave silence**: Exit if silent >15 min (configurable)
- **Stay override**: `/codey stay 4` keeps bot for 4 hours max

### Output & Exports
- **Markdown transcript** (.md) with speaker names + timestamps
- **Raw audio** (.wav) — full session recording
- **Save location**: `~/Downloads/codey-discord-voice/`
- **Cost tracking**: Per-session STT/TTS/LLM costs displayed in `/codey status`

### Web UI (Optional)
- **Live view** of current transcript at `localhost:8080` (if enabled)
- **Password protected** (set `UI_PASSWORD`)
- **Real-time updates** from audio pipeline

---

## Tech Stack

| Component | Tool | Cost Model |
|-----------|------|-----------|
| **Runtime** | Bun + TypeScript | Free |
| **STT** | Groq Whisper Large V3 | Free tier |
| **Brain (LLM)** | Groq Llama 3.3 70B | Free tier |
| **TTS (Voice)** | macOS say / Edge TTS / Google Chirp | Mostly free; Chirp $30/1M chars |
| **Discord** | discord.js v14.16 | Free |
| **Audio Codec** | Opus (discord.js) + FFmpeg | Free |
| **Web UI** | Node HTTP server | Free (optional) |

---

## Architecture

### Core Modules
- **`voice-session.ts`** — Main session state, lifecycle
- **`audio-pipeline.ts`** — Audio capture, chunking, silence detection
- **`transcriber.ts`** — Groq Whisper STT integration
- **`brain.ts`** — Groq Llama LLM integration
- **`tts.ts`** — TTS backend selection (mac-say, Edge, Google)
- **`commands.ts`** — Slash command definitions
- **`discord-transcript.ts`** — Markdown transcript writer
- **`ui-server.ts`** — Optional web UI HTTP server
- **`auto-shutdown.ts`** — Auto-leave + session cleanup
- **`cost.ts`** — Token cost calculation & reporting

### Command Processing
- **Slash commands** registered via `/register` (interactive)
- **Command watcher** polls for new guild commands
- **Think bridge** routes `/codey think` to Claude API
- **Speak state** tracks speaker mode (on/off/trigger permissions)

### Auto-Shutdown Pipeline
1. **Alone check** — if no users in channel >5 min → auto-leave
2. **Silence check** — if no speech >15 min → auto-leave
3. **Stale replies** — old AI responses auto-discarded
4. **Session archive** — transcripts + audio backed up on exit

---

## Limitations & Known Issues

### Current Constraints
- **macOS TTS only** — `say` command works on macOS; Edge TTS is cloud-based (works on Linux)
- **Single language per session** — Language code fixed at startup; switch requires restart
- **Groq free tier limits** — STT/LLM requests rate-limited; check Groq console for quota
- **Google Chirp credentials** — Requires `GOOGLE_APPLICATION_CREDENTIALS` set; omit for free TTS only
- **Audio format** — Saves WAV at 48 kHz; MP3 export not supported yet
- **Discord gateway** — Bot must have voice permissions in target channels

### Known Workarounds
- **Voice permission denied** → Check bot role + channel permissions in Discord
- **No STT output** → Verify Groq API key + language code matches recording language
- **TTS not playing** → Check `TTS_VOICE` matches available voices; fall back to `niwat` if unsure
- **Session hangs** → Check `AUTO_LEAVE_SILENCE_MS` setting; manually `/codey leave` if stuck

---

## Development

### NPM Scripts
```bash
bun start                # Same as `bun src/index.ts`
bun dev                  # Watch mode (reload on file change)
bun run register         # Register Discord slash commands
bun typecheck            # TypeScript type checking
bun run fix-opus         # Fix Opus codec build issues (macOS)
```

### Debugging
- Set `DEBUG=*` before running to see verbose logs
- Check `TRANSCRIPT_DIR` for saved `.md` + `.wav` files
- Use `/codey status` to inspect live session state
- Monitor memory with `MEMORY_REPORT_MS` interval logs

---

## Cost Estimation

### Free Tier (Monthly)
- **Groq Whisper STT**: Free up to rate limits (~100 req/min)
- **Groq Llama LLM**: Free tier available
- **macOS say / Edge TTS**: Free (no billing)
- **Discord.js**: Free

### Paid (Optional)
- **Google Chirp3-HD**: ~$30 per 1 million characters (premium voice quality)

---

## Links

- **Repo**: https://github.com/Soul-Brews-Studio/voice-bot
- **Bun**: https://bun.sh
- **Discord.js**: https://discord.js.org
- **Groq API**: https://console.groq.com
- **Google Cloud Speech**: https://cloud.google.com/speech-to-text

---

**Last Updated**: 2026-06-06  
**Version**: v0.1.0  
**License**: MIT
