# voice-bot Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/Soul-Brews-Studio/voice-bot

## Explorations

### 2026-06-06 1804 (default)
- [[2026-06-06/1804_ARCHITECTURE|Architecture]]
- [[2026-06-06/1804_CODE-SNIPPETS|Code Snippets]]
- [[2026-06-06/1804_QUICK-REFERENCE|Quick Reference]]

**Key insights**:
- Discord voice transcriber + AI secretary — real-time per-speaker STT (Groq Whisper), AI replies (Groq Llama 3.3 70B), TTS playback
- Think-bridge: file-based IPC to Claude (Opus) for deep questions — request.json → maw notification → reply.txt polling
- Integrates with Leica Oracle ecosystem via maw handoff notifications
