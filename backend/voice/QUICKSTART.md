# AgentFlow Voice - Quick Start Guide

Get up and running with voice-controlled AgentFlow in under 5 minutes!

## Prerequisites

- Python 3.8+ (for backend)
- Node.js 18+ (for frontend)
- Microphone and speakers
- API keys (all FREE!)

## Step 1: Get API Keys (2 minutes)

### Groq (100% FREE)
1. Go to https://console.groq.com
2. Sign up / log in
3. Get API key: https://console.groq.com/keys

### ElevenLabs (FREE tier)
1. Go to https://elevenlabs.io
2. Sign up / log in
3. Get API key: https://elevenlabs.io/app/settings/api-keys

### LiveKit Cloud (10k min/month FREE)
```bash
# Install CLI
brew install livekit-cli

# Authenticate
lk cloud auth

# Create project and get credentials
lk app env -w -d backend/voice/.env.local
```

Or get manually at: https://cloud.livekit.io

## Step 2: Set Up Backend (1 minute)

```bash
cd backend/voice

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add API keys to .env.local
nano .env.local
```

Your `.env.local` should have:
```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
GROQ_API_KEY=your_groq_api_key
ELEVEN_API_KEY=your_elevenlabs_api_key
```

## Step 3: Test Backend (30 seconds)

```bash
# Verify setup
python test_apis.py

# You should see all ✅ green checkmarks!
```

## Step 4: Set Up Frontend (1 minute)

```bash
cd frontend/

# Install dependencies
npm install

# Copy environment (use SAME values as backend)
cp .env.example .env.local
nano .env.local
```

Your `frontend/.env.local`:
```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
```

## Step 5: Run Everything! (30 seconds)

### Terminal 1 - Backend Agent
```bash
cd backend/voice
source venv/bin/activate
python agent.py dev
```

You should see:
```
INFO Starting AgentFlow voice assistant in room: agentflow-voice
INFO Voice assistant is ready and listening
```

### Terminal 2 - Frontend UI
```bash
cd backend/voice/frontend
npm run dev
```

Open http://localhost:3000 in your browser.

## Step 6: Test Voice Interaction

1. Click **"Start Voice Session"** button
2. Grant microphone permissions
3. Wait for blue orb (listening state)
4. Say: **"Hey AgentFlow, remember what I'm going to do now"**
5. Agent responds with voice and orb turns green!

## Example Interactions

Try saying:
- "Hey AgentFlow, remember what I'm going to do now"
- "Send an email to John"
- "Open my Canvas class"
- "What can you help me with?"

## Troubleshooting

### Backend won't start
```bash
# Check API keys
python test_apis.py

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend can't connect
```bash
# Ensure backend is running first
# Check browser console for errors
# Verify .env.local credentials match backend
```

### No audio
- Check microphone permissions in browser
- Verify speakers/headphones are working
- Look for errors in browser console

### Orb doesn't animate
- Hard refresh browser (Cmd+Shift+R)
- Check that framer-motion installed: `npm install framer-motion`

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  User speaks into microphone                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Frontend (localhost:3000)                               │
│  - Animated voice orb                                    │
│  - Audio visualization                                   │
│  - LiveKit Client SDK                                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼ WebRTC
┌─────────────────────────────────────────────────────────┐
│  LiveKit Cloud                                           │
│  - Real-time audio streaming                             │
│  - Room management                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Backend Agent (Python)                                  │
│  - STT: Groq Whisper (speech → text)                    │
│  - LLM: Groq Llama 3.3 (text → response)                │
│  - TTS: ElevenLabs (response → speech)                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  User hears agent response through speakers              │
└─────────────────────────────────────────────────────────┘
```

## What's Next?

1. **Integrate with Workflow System**: Connect voice commands to actual workflow recording/execution
2. **Add Computer Vision**: Let agent see what's on screen during recording
3. **Deploy**: Host frontend on Vercel, backend on your server
4. **Customize Voice**: Try different ElevenLabs voices
5. **Improve Prompts**: Tune AGENT_INSTRUCTIONS for your use case

## Cost Breakdown (per month)

| Service      | Free Tier         | Cost |
|--------------|-------------------|------|
| Groq         | Generous usage    | $0   |
| ElevenLabs   | 10k chars         | $0   |
| LiveKit      | 10k minutes       | $0   |
| **Total**    | **Perfect for hackathons** | **$0** |

## Need Help?

- Check `backend/voice/README.md` for backend details
- Check `backend/voice/frontend/README.md` for frontend details
- Look at error logs in terminal and browser console
- Verify all API keys are correct

---

**You're all set! Happy hacking!** 🚀

*Made for CalHacks 2025*
