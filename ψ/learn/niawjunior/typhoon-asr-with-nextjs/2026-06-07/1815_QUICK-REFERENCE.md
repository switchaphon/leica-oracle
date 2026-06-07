# Typhoon ASR with Next.js — Quick Reference

**Project**: Thai speech-to-text (STT) demo application  
**Stack**: Next.js 15 (frontend) + FastAPI (backend) + Typhoon ASR (Thai STT model)  
**Status**: Production-ready demo with three operation modes  
**Source**: https://github.com/niawjunior/typhoon-asr-with-nextjs

---

## What It Does

A full-stack web application for Thai speech recognition:

- **Record audio** from microphone → transcribe to Thai text
- **Upload audio files** (WAV, MP3, FLAC, OGG, OPUS) → transcribe
- **Real-time streaming** transcription as you speak (HTTP streaming)
- **Two backend modes**: Cloud API (Typhoon's service) or local model (self-hosted)
- **Word-level timestamps** visualization (when supported by backend)

---

## Architecture

```
Frontend (Next.js 15)
├── Page: /web/app/page.tsx
│   ├── Upload Tab: File selection + audio playback
│   ├── Record Tab: Microphone recording + transcribe
│   ├── HTTP Stream Tab: Real-time streaming transcription
│   └── Config Sidebar: API key, mode, device selection
└── Components: shadcn/ui (Card, Button, Textarea, Switch, Tabs)

Backend (FastAPI)
├── POST /transcribe → Single-shot transcription
├── POST /stream-transcribe → HTTP streaming transcription
├── GET /health → Health check
└── GET / → Root endpoint
```

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- `uv` (Python package manager, optional but recommended)

### Backend Setup

```bash
git clone https://github.com/niawjunior/typhoon-asr-with-nextjs.git
cd typhoon-asr-with-nextjs

# Python virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Optional: For local model (self-hosted transcription)
uv pip install typhoon-asr
```

**Backend Dependencies** (`requirements.txt`):
```
fastapi
uvicorn[standard]
python-multipart
websockets
typhoon-asr          # Optional: local model
openai               # For cloud API client
pydub                # Audio processing
numpy
```

### Frontend Setup

```bash
cd web
npm install
# or
yarn install
```

Create `.env.local` in `/web`:
```
NEXT_PUBLIC_API_KEY=your-typhoon-api-key
```

---

## Running the App

### Terminal 1: Start Backend

```bash
python main.py
```

Runs on `http://localhost:8000`  
API Docs: `http://localhost:8000/docs` (Swagger)

### Terminal 2: Start Frontend

```bash
cd web
npm run dev
```

Runs on `http://localhost:3000`

---

## API Endpoints

### POST /transcribe

Single-shot audio transcription.

**Request** (FormData):
- `file` (UploadFile, required): Audio file (.wav, .mp3, .flac, .ogg, .opus)
- `api_key` (str, optional if using local mode): Typhoon API key
- `use_api` (bool, default: true): Use cloud API (true) or local model (false)
- `with_timestamps` (bool, default: false): Include word-level timestamps
- `device` (str, default: "auto"): "auto", "cpu", or "cuda" (local mode only)

**Response** (JSON):
```json
{
  "text": "สวัสดีครับ",
  "processing_time": 1.234,
  "timestamps": []  // Empty if not requested or unsupported
}
```

**Example** (cURL):
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@audio.wav" \
  -F "api_key=your-api-key" \
  -F "use_api=true" \
  -F "with_timestamps=false"
```

---

### POST /stream-transcribe

HTTP streaming transcription (Server-Sent Events style).

**Request** (FormData): Same as `/transcribe`

**Response** (streaming text/event-stream, newline-delimited JSON):
```
{"status": "processing", "message": "Processing audio..."}
{"status": "interim", "text": "สวัสดีครับ"}
{"status": "interim", "text": "วันนี้"}
{"status": "complete", "result": {"text": "สวัสดีครับวันนี้", "processing_time": 2.456}}
```

**Streaming Pattern**:
- Initial: `status: "processing"`
- During: `status: "interim"` (simulated: sends 3 words at a time, 200ms delay)
- Final: `status: "complete"` with full result object
- On error: `status: "error"` with message

**Frontend Usage** (from `page.tsx`):
```typescript
const response = await fetch("http://localhost:8000/stream-transcribe", {
  method: "POST",
  body: formData,
});

const reader = response.body!.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value, { stream: true });
  const lines = chunk.split("\n").filter(line => line.trim());
  for (const line of lines) {
    const data = JSON.parse(line);
    console.log(data.status, data.text || data.message);
  }
}
```

---

### GET /health

Health check endpoint.

**Response**:
```json
{"status": "healthy"}
```

---

### GET /

Root endpoint.

**Response**:
```json
{"message": "Typhoon ASR API is running"}
```

---

## Streaming STT: Yes!

**Can it do streaming STT?** YES, but with caveats:

### Current Implementation (Simulated Streaming)

- **Upload/Record Mode** (`/transcribe`): Single-shot, no streaming
- **Stream Mode** (`/stream-transcribe`): HTTP streaming, but **simulated**
  - Transcribes the entire audio first (not true real-time)
  - Then streams the result back in 3-word chunks with 200ms delay
  - Useful for progressive UI updates, not true real-time STT

### True Real-Time Streaming (Not Currently Implemented)

For true chunk-by-chunk audio processing:
1. Client would send audio in chunks (e.g., 100ms frames)
2. Backend would process each chunk as it arrives (requires Typhoon ASR to support streaming)
3. Results would be yielded incrementally

**Limitation**: Typhoon ASR's OpenAI client doesn't expose streaming audio API endpoints in the current demo. Would require direct integration with Typhoon's WebSocket or chunk-based API.

---

## Key Code Patterns

### Frontend: Recording with Real-Time Transcription

```typescript
// Start recording
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const mediaRecorder = new MediaRecorder(stream);
const audioChunks: Blob[] = [];

mediaRecorder.ondataavailable = (event) => {
  if (event.data.size > 0) {
    audioChunks.push(event.data);
  }
};

mediaRecorder.start(300); // Collect data every 300ms

// Process chunks every 1.5 seconds
setInterval(async () => {
  const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
  const formData = new FormData();
  formData.append("file", new File([audioBlob], "recording.wav"));
  formData.append("api_key", apiKey);
  
  const response = await fetch("http://localhost:8000/stream-transcribe", {
    method: "POST",
    body: formData,
  });
  // Read streaming response...
}, 1500);
```

### Backend: API Mode Transcription

```python
from openai import OpenAI

def transcribe_with_api(audio_path: str, api_key: str, 
                       with_timestamps: bool = False) -> Dict:
    client = OpenAI(
        base_url="https://api.opentyphoon.ai/v1",
        api_key=api_key
    )
    
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="typhoon-asr-realtime",
            file=audio_file
        )
    
    return {
        "text": response.text,
        "processing_time": time.time() - start,
        "timestamps": []  # API doesn't return timestamps yet
    }
```

### Backend: Local Mode Transcription

```python
from typhoon_asr import transcribe as typhoon_transcribe

def transcribe_with_local_model(audio_path: str, device: str = "auto",
                               with_timestamps: bool = False) -> Dict:
    result = typhoon_transcribe(
        audio_path,
        model_name="scb10x/typhoon-asr-realtime",
        with_timestamps=with_timestamps,
        device=device
    )
    return result
```

### Frontend: Streaming Response Handler

```typescript
const response = await fetch("http://localhost:8000/stream-transcribe", {
  method: "POST",
  body: formData,
});

const reader = response.body!.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value, { stream: true });
  const lines = chunk.split("\n").filter(line => line.trim());
  
  for (const line of lines) {
    try {
      const data = JSON.parse(line);
      
      if (data.status === "error") {
        console.error(data.message);
      } else if (data.status === "interim") {
        setTranscription(prev => prev + " " + data.text);
      } else if (data.status === "complete") {
        setTranscription(data.result.text);
      }
    } catch (e) {
      console.error("Parse error:", e);
    }
  }
}
```

---

## Environment Variables

### Frontend (`.env.local`)

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `NEXT_PUBLIC_API_KEY` | string | No | Default Typhoon API key (can override in UI) |

### Backend

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `HOST` | string | "0.0.0.0" | Server host (in `main.py`) |
| `PORT` | int | 8000 | Server port (in `main.py`) |

**API Key**: Obtained from https://opentyphoon.ai/  
Get your API key from the Typhoon Web Playground.

---

## Configuration & Operation Modes

### Mode 1: API Mode (Cloud)

- Uses Typhoon's cloud service
- Requires valid API key
- Rate limit: 100 requests/minute
- No local GPU needed

**UI Toggle**: Configuration panel → "Transcription Mode" (ON = API Mode)

### Mode 2: Local Mode (Self-Hosted)

- Runs `typhoon-asr` locally on your device
- Requires `typhoon-asr` package installed
- No API key needed
- Supports device selection: auto, CPU, CUDA

**UI Toggle**: Configuration panel → "Transcription Mode" (OFF = Local Mode)  
**Device**: Select CPU, CUDA (GPU), or auto

---

## Model Information

**Model**: `typhoon-asr-realtime`  
**Size**: 114M parameters  
**Language**: Thai (Thai speech → Thai text)  
**Provider**: SCB 10X  
**Release Date**: 2025-09-08  
**Rate Limit**: 100 requests/minute (API mode)

---

## Supported Audio Formats

- `.wav` (WAV)
- `.mp3` (MP3)
- `.flac` (FLAC)
- `.ogg` (OGG)
- `.opus` (OPUS)

---

## Troubleshooting

### CORS Errors

**Problem**: Frontend can't reach backend  
**Solution**:
1. Ensure backend is running on `http://localhost:8000`
2. Check that CORS middleware is enabled (it is by default in `api.py`)
3. Verify frontend requests use correct backend URL

### API Key Issues

**Problem**: "API key is required for API mode"  
**Solution**:
1. Verify API key is valid (get from https://opentyphoon.ai/)
2. Check `.env.local` contains `NEXT_PUBLIC_API_KEY=<key>`
3. Or enter key directly in UI configuration panel
4. Ensure you have sufficient quota/credits

### Local Model Not Found

**Problem**: "typhoon-asr package is not installed"  
**Solution**:
```bash
uv pip install typhoon-asr
```

### Microphone Permissions

**Problem**: "Error accessing microphone"  
**Solution**:
1. Grant browser microphone permissions
2. Use HTTPS or localhost (required for getUserMedia)
3. Check browser console for specific permission errors

### Audio Format Issues

**Problem**: Upload fails with unsupported format  
**Solution**: Use one of the supported formats (.wav, .mp3, .flac, .ogg, .opus)  
Use `ffmpeg` to convert:
```bash
ffmpeg -i input.m4a -c:a pcm_s16le -ar 16000 output.wav
```

---

## Project Structure

```
typhoon-asr-with-nextjs/
├── README.md
├── main.py                    # FastAPI entry point
├── api.py                     # API endpoints
├── requirements.txt           # Python dependencies
└── web/                       # Next.js frontend
    ├── package.json
    ├── tsconfig.json
    ├── next.config.ts
    ├── app/
    │   ├── layout.tsx
    │   └── page.tsx           # Main app component
    ├── components/
    │   └── ui/                # shadcn/ui components
    └── lib/
        └── utils.ts
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/niawjunior/typhoon-asr-with-nextjs.git
cd typhoon-asr-with-nextjs

# Backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python main.py  # Runs on :8000

# Frontend (new terminal)
cd web
npm install
npm run dev     # Runs on :3000

# Visit http://localhost:3000 in browser
```

---

## Notes for Integration

### For Use with Flux (Backend Dev)

- FastAPI pattern is clean and extensible
- CORS is wide open (consider restricting in production)
- Streaming uses simple JSON-per-line format (easy to extend)
- Could add WebSocket support for true bidirectional streaming

### For Use with Chrome (Frontend Dev)

- Next.js 15 with Turbopack (fast rebuild)
- Uses React 19 (latest, experimental features available)
- shadcn/ui components (easily customizable)
- Streaming response handler is reusable pattern
- MediaRecorder API for microphone input

### For Production Deployment

1. Move API key to secure secret management (e.g., Vercel Environment Variables)
2. Add rate limiting on `/transcribe` and `/stream-transcribe` endpoints
3. Add request validation (file size, duration limits)
4. Consider Redis-based request queuing
5. Add logging/monitoring (FastAPI Prometheus metrics)
6. CORS should be restricted to known origins
7. Implement audio persistence if needed (currently uses temp files)

---

**Last Updated**: 2026-06-07 18:15  
**Reference Date**: 2026-06-07  
**Scope**: Complete feature analysis + deployment readiness
