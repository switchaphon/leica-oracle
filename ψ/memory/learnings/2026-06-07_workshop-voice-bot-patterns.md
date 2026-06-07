---
name: workshop-voice-bot-patterns
description: Voice bot patterns learned from Oracle School Workshop 02 — TTS, daemon, streaming, fleet protocol
metadata:
  type: learning
---

## Voice Bot Patterns (Workshop 02)

1. **TTS pipeline**: edge-tts → ffmpeg → WAV → createAudioResource(wav) — don't specify inputType, let discord.js detect
2. **Daemon pattern**: HTTP IPC on localhost, PID file, same as atlas route
3. **async execFile**: never use execFileSync in voice daemon — blocks event loop → 20ms UDP gaps → warped audio
4. **@discordjs/voice >= 0.19.2**: older versions have encryption bugs
5. **Bun needs tweetnacl**: not libsodium (different from Node.js)
6. **Token sharing**: same bot token works for text MCP + voice daemon simultaneously — no conflict
7. **GuildVoiceStates**: not a privileged intent, no portal toggle needed
8. **Stream >50s risk**: UDP drop when multiple gateway sessions share token — fix: separate token or recreate-on-idle
9. **Fleet protocol**: react emoji for others' messages, reply only when tagged directly
10. **Workshop lifecycle**: when P'Nat says workshop ends → stop loop immediately
