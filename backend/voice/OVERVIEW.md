# AgentFlow Voice - Complete Overview

## What You Have Now

A **complete voice-controlled AI assistant** with a beautiful ChatGPT-style UI!

### Backend (Python)
- ✅ Voice agent with Groq + ElevenLabs
- ✅ LiveKit integration for real-time audio
- ✅ Sub-600ms latency
- ✅ 100% FREE during development

### Frontend (Next.js)
- ✅ Animated voice orb (ChatGPT-style)
- ✅ Real-time audio visualization
- ✅ Dynamic color states (blue/green/purple)
- ✅ Smooth Framer Motion animations

## Project Structure

```
backend/voice/
├── agent.py                 # Main voice agent (Groq + ElevenLabs + LiveKit)
├── requirements.txt         # Python dependencies
├── .env.local              # API keys (YOU NEED TO CREATE THIS)
├── test_apis.py            # API verification script
│
├── frontend/               # React/Next.js UI
│   ├── app/
│   │   ├── page.tsx        # Main voice interface
│   │   ├── layout.tsx      # Root layout
│   │   ├── globals.css     # Styles
│   │   └── api/token/      # LiveKit token generation
│   ├── components/
│   │   └── VoiceOrb.tsx    # Animated orb component
│   ├── lib/
│   │   └── audioAnalyser.ts # Audio level detection
│   ├── package.json        # Node dependencies
│   ├── .env.local          # LiveKit config (YOU NEED TO CREATE THIS)
│   └── README.md           # Frontend docs
│
├── README.md               # Main documentation
├── QUICKSTART.md           # 5-minute setup guide ⭐ START HERE
├── OVERVIEW.md             # This file
└── run_all.sh              # Launch everything at once
```

## Quick Start (TL;DR)

```bash
# 1. Get API keys (see QUICKSTART.md)

# 2. Set up backend
cd backend/voice
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.local
# Add your API keys to .env.local

# 3. Set up frontend
cd frontend/
npm install
cp .env.example .env.local
# Add your LiveKit credentials to .env.local

# 4. Run everything
cd ..  # back to backend/voice/
./run_all.sh
```

Open http://localhost:3000 and start talking!

## How It Works

### 1. User Interaction Flow

```
User speaks
   ↓
Frontend captures audio via microphone
   ↓
LiveKit streams to backend via WebRTC
   ↓
Backend processes:
   - Groq Whisper: speech → text
   - Groq Llama: text → response
   - ElevenLabs: response → speech
   ↓
LiveKit streams audio back to frontend
   ↓
Frontend plays audio + animates orb
   ↓
User hears response
```

### 2. Visual Feedback

The animated orb changes based on state:

- **Purple (Idle)**: Ready to connect
- **Blue (Listening)**: Microphone active, capturing speech
- **Green (Speaking)**: Agent is responding

The orb **grows and pulses** based on audio level in real-time!

### 3. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| STT | Groq Whisper | Speech to text (ultra-fast) |
| LLM | Groq Llama 3.3 | Natural language understanding |
| TTS | ElevenLabs | Text to speech (premium quality) |
| Streaming | LiveKit Cloud | Real-time WebRTC audio |
| Backend | Python + livekit-agents | Voice pipeline orchestration |
| Frontend | Next.js + TypeScript | Web UI |
| Animation | Framer Motion | Smooth orb animations |
| Visualization | Web Audio API | Real-time audio levels |

## What Makes This Special

### 🚀 Speed
- Total latency: **~600ms** (industry-leading)
- Groq LPU inference: **~50-100ms**
- ElevenLabs TTS: **~200-300ms**
- Network latency: **~100-200ms**

### 💰 Cost
- **100% FREE** for hackathons/development
- Groq: Generous free tier
- ElevenLabs: 10k chars/month free
- LiveKit: 10k minutes/month free

### 🎨 Design
- Modern ChatGPT-inspired UI
- Smooth animations with Framer Motion
- Real-time audio visualization
- AMOLED-friendly dark theme

### 🔧 Architecture
- Modular and extensible
- Plugin-based (easy to swap STT/LLM/TTS)
- TypeScript for type safety
- Clean separation of concerns

## Example Interactions

Try these voice commands:

```
You: "Hey AgentFlow, remember what I'm going to do now"
Agent: "Sure! I'm ready to watch and learn your workflow. Go ahead!"

You: "Open my Canvas class"
Agent: "Got it! I'll help you open your Canvas class. What's the class name?"

You: "Send an email to John"
Agent: "I can help with that! What would you like the email to say?"
```

## Customization Ideas

### Change Voice
Edit `agent.py`:
```python
tts=elevenlabs.TTS(
    voice_id="pNInz6obpgDQGcFmaJgB",  # Adam (deep male)
    model="eleven_turbo_v2_5"
)
```

Browse voices: https://elevenlabs.io/app/voice-library

### Change Colors
Edit `frontend/components/VoiceOrb.tsx`:
```typescript
const getOrbColor = () => {
  if (isSpeaking) return "rgba(255, 0, 0, 0.6)"; // Red
  if (isListening) return "rgba(0, 255, 0, 0.6)"; // Green
  return "rgba(255, 255, 0, 0.4)"; // Yellow
};
```

### Change Agent Personality
Edit `agent.py` AGENT_INSTRUCTIONS:
```python
AGENT_INSTRUCTIONS = """You are a pirate AI assistant who speaks like a pirate..."""
```

## Integration with AgentFlow

This voice system is designed to integrate with the main AgentFlow workflow recording/execution:

1. **Recording Mode**: User says "remember what I'm going to do"
   → Agent acknowledges
   → Start workflow recording (future integration)

2. **Execution Mode**: User says "send that email to John"
   → Agent extracts intent + parameters
   → Execute learned workflow (future integration)

### Next Steps for Integration

1. Connect voice commands to `backend/recorder.py`
2. Add visual feedback during recording
3. Implement parameter extraction from voice
4. Enable workflow execution via voice triggers

## Troubleshooting

### Backend Issues

**Agent won't start**
```bash
python test_apis.py  # Check API keys
pip install -r requirements.txt --force-reinstall
```

**"Not trusted" error**
- Grant Accessibility permissions to Terminal
- System Preferences → Security & Privacy → Privacy → Accessibility

### Frontend Issues

**Can't connect to room**
- Ensure backend is running first
- Check browser console for errors
- Verify .env.local credentials match backend

**Orb doesn't animate**
- Hard refresh: Cmd+Shift+R
- Check `framer-motion` installed
- Open browser console for React errors

**No audio**
- Check microphone permissions
- Verify speakers/headphones working
- Look for WebRTC errors in console

### Network Issues

**LiveKit connection fails**
- Verify LIVEKIT_URL starts with `wss://`
- Check firewall allows WebRTC
- Try different network (some corporate networks block WebRTC)

## Performance Tips

### Backend
- Use `eleven_turbo_v2_5` for fastest TTS
- Adjust `temperature=0.7` in LLM for more/less creativity
- Enable `dynacast` in LiveKit for better streaming

### Frontend
- Use production build for better performance: `npm run build && npm start`
- Enable audio visualization only when needed
- Reduce animation complexity on slower devices

## Deployment

### Backend
- Deploy on cloud VM (AWS, GCP, DigitalOcean)
- Use `python agent.py start` for production
- Set up systemd service for auto-restart
- Use environment variables for secrets

### Frontend
- Deploy to Vercel (easiest): `vercel deploy`
- Or use any static host (Netlify, Cloudflare Pages)
- Set environment variables in hosting dashboard
- Enable HTTPS for microphone access

## Resources

- **QUICKSTART.md** - Follow this first! ⭐
- **README.md** - Main backend documentation
- **frontend/README.md** - Frontend-specific docs
- [Groq Docs](https://console.groq.com/docs)
- [ElevenLabs Docs](https://elevenlabs.io/docs)
- [LiveKit Docs](https://docs.livekit.io)
- [Next.js Docs](https://nextjs.org/docs)

## Support

If you run into issues:
1. Check the troubleshooting sections above
2. Read error messages carefully (they're usually helpful!)
3. Look at browser console and terminal logs
4. Verify API keys are correct
5. Ensure all dependencies installed

---

**Ready to build?** Start with `QUICKSTART.md`!

**Made for CalHacks 2025** 🚀
