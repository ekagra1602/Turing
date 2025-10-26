# AgentFlow Voice Assistant

Voice interface for AgentFlow using **Groq + ElevenLabs** via LiveKit.

**NEW:** Modern ChatGPT-style voice overlay UI in `frontend/` folder!

## Stack

- **STT**: Groq Whisper (ultra-fast, FREE)
- **LLM**: Groq Llama 3.3 70B (powerful, FREE)
- **TTS**: ElevenLabs (premium quality, FREE tier)
- **Framework**: LiveKit Agents (10k free min/month)

## Quick Start

### 1. Install Dependencies

```bash
cd backend/voice

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get API Keys (All FREE!)

#### Groq (100% FREE)
1. Sign up: https://console.groq.com
2. Get API key: https://console.groq.com/keys

#### ElevenLabs (FREE tier)
1. Sign up: https://elevenlabs.io
2. Get API key: https://elevenlabs.io/app/settings/api-keys

#### LiveKit Cloud (10k min/month FREE)
```bash
# Option A: CLI (easiest)
brew install livekit-cli
lk cloud auth
lk app env -w -d .env.local
```

Or manually at: https://cloud.livekit.io

### 3. Configure Environment

```bash
# Copy example
cp .env.example .env.local

# Edit with your keys
nano .env.local
```

### 4. Test Setup

```bash
python test_voice.py
```

Should show all ✅ green checkmarks!

### 5. Run

```bash
# Console mode - speak in terminal
python agent.py console

# Dev mode - connect via browser
python agent.py dev
```

## Example Interactions

```
You: "Hey AgentFlow, remember what I'm going to do now"
Agent: "Sure! I'm ready to watch and learn..."

You: "Hey agent, send an email to John"
Agent: "Got it! I'll send an email to John..."
```

## Architecture

```
User Voice → LiveKit → Groq Whisper (STT) → Groq Llama (LLM) → ElevenLabs (TTS) → User Hears
```

**Latency**: ~600ms total (ultra-fast!)

## Customization

### Change Voice

Edit `agent.py`:
```python
tts=elevenlabs.TTS(
    voice_id="YOUR_VOICE_ID",  # Change this
)
```

Popular voices:
- `"EXAVITQu4vr4xnSDxMaL"` - Sarah (default, professional female)
- `"21m00Tcm4TlvDq8ikWAM"` - Rachel (calm female)
- `"pNInz6obpgDQGcFmaJgB"` - Adam (deep male)

Browse all: https://elevenlabs.io/app/voice-library

### Change Model

Edit `agent.py`:
```python
llm=groq.LLM(
    model="llama-3.1-8b-instant",  # Faster
    # or "mixtral-8x7b-32768"      # Alternative
)
```

## Cost Breakdown

| Service | Free Tier | Enough For |
|---------|-----------|------------|
| Groq | Generous | Unlimited demos |
| ElevenLabs | 10k chars/mo | ~1-2 hours speech |
| LiveKit | 10k min/mo | ~167 hours |

**Total**: $0 for hackathons!

## Troubleshooting

### Import errors
```bash
pip install -r requirements.txt
```

### Missing API keys
```bash
python test_voice.py  # Diagnose issue
```

### No audio
- Check microphone permissions
- Ensure speakers connected
- Try `python agent.py console --verbose`

## File Structure

```
backend/voice/
├── agent.py           # Main voice agent
├── requirements.txt   # Dependencies
├── .env.example       # Config template
├── test_voice.py      # Setup verification
├── setup.sh           # Automated setup
└── README.md          # This file
```

## Voice Overlay UI

A beautiful ChatGPT-style voice interface is available in `frontend/`:

```bash
cd frontend/
npm install
npm run dev
```

Features:
- 🎨 Animated orb that grows when speaking
- 🎤 Real-time audio visualization
- 🌈 Dynamic colors (blue=listening, green=speaking)
- 🚀 Built with Next.js + Framer Motion

See `frontend/README.md` for full documentation.

## Next Steps

- Test voice interaction with frontend UI
- Integrate with main AgentFlow workflow system
- Add visual feedback during voice control

## Resources

- [Groq Console](https://console.groq.com)
- [ElevenLabs Docs](https://elevenlabs.io/docs)
- [LiveKit Agents](https://docs.livekit.io/agents/)

---

**Made for CalHacks 2025** 🚀
