# AgentFlow Voice Overlay - Modern UI

Beautiful ChatGPT-style voice interface for AgentFlow with animated orb visualization.

## 🪟 Desktop Overlay Mode (NEW!)

Run AgentFlow Voice as a **true desktop overlay** that floats above all applications!

```bash
./launch-overlay.sh
```

Or manually:
```bash
npm install
npm run electron:dev
```

**[📖 Read the Electron Overlay Guide](./ELECTRON.md)** for more details.

---

## Features

- **🪟 Desktop Overlay** - Float above all apps as a transparent window
- **Dynamic Voice Orb** - Animated orb that grows and pulses with audio levels
- **Real-time Visualization** - Visual feedback when agent is listening or speaking
- **Smooth Animations** - Framer Motion powered animations for fluid UI
- **ChatGPT-Inspired Design** - Modern dark theme with gradient effects
- **LiveKit Integration** - Seamless connection to voice agent backend

## Quick Start (Browser Mode)

### 1. Install Dependencies

```bash
cd backend/voice/frontend
npm install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env.local

# Edit with your LiveKit credentials (same as backend)
nano .env.local
```

Your `.env.local` should have:
```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
```

### 3. Start the Voice Agent Backend

In a separate terminal:
```bash
cd backend/voice
source venv/bin/activate
python agent.py dev
```

### 4. Run the Frontend

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## How It Works

### Architecture

```
User Browser (localhost:3000)
    ↓
Next.js Frontend (React + LiveKit Client)
    ↓
LiveKit Cloud (WebRTC)
    ↓
Voice Agent Backend (Python + Groq + ElevenLabs)
```

### Visual States

1. **Idle (Purple)** - Ready to connect
2. **Listening (Blue)** - Microphone active, capturing user speech
3. **Speaking (Green)** - Agent is responding with voice

### Components

- **VoiceOrb** (`components/VoiceOrb.tsx`) - Animated orb with dynamic sizing and glow effects
- **AudioAnalyser** (`lib/audioAnalyser.ts`) - Real-time audio level analysis for visualization
- **Token API** (`app/api/token/route.ts`) - Generates LiveKit access tokens for secure connection

## Customization

### Change Orb Colors

Edit `components/VoiceOrb.tsx`:

```typescript
const getOrbColor = () => {
  if (isSpeaking) return "rgba(16, 185, 129, 0.6)"; // Green
  if (isListening) return "rgba(59, 130, 246, 0.6)"; // Blue
  return "rgba(99, 102, 241, 0.4)"; // Purple (idle)
};
```

### Adjust Animation Speed

In `VoiceOrb.tsx`, modify transition durations:

```typescript
transition={{
  duration: 2, // Change this value
  repeat: Infinity,
  ease: "easeInOut",
}}
```

### Change Background Gradient

Edit `app/page.tsx`:

```typescript
<div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-radial from-blue-500/10 via-purple-500/5 to-transparent rounded-full blur-3xl" />
```

## Troubleshooting

### "Failed to get token" error

- Ensure backend voice agent is running (`python agent.py dev`)
- Check that `.env.local` has correct LiveKit credentials
- Verify LIVEKIT_API_KEY and LIVEKIT_API_SECRET are set

### No audio visualization

- Check browser microphone permissions
- Ensure backend agent is running and connected
- Open browser console to check for WebRTC errors

### Orb doesn't animate

- Verify `framer-motion` is installed: `npm install framer-motion`
- Check browser console for React errors
- Try hard refresh (Cmd+Shift+R)

## Development

### Project Structure

```
frontend/
├── app/
│   ├── api/token/route.ts    # LiveKit token generation
│   ├── page.tsx               # Main voice interface
│   ├── layout.tsx             # Root layout
│   └── globals.css            # Global styles
├── components/
│   └── VoiceOrb.tsx           # Animated voice orb
├── lib/
│   └── audioAnalyser.ts       # Audio analysis utilities
├── package.json               # Dependencies
└── README.md                  # This file
```

### Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Animation library
- **LiveKit Client SDK** - WebRTC voice streaming
- **LiveKit Server SDK** - Token generation

## Deployment

### Build for Production

```bash
npm run build
npm start
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

Add environment variables in Vercel dashboard:
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `NEXT_PUBLIC_LIVEKIT_URL`

## Resources

- [LiveKit Docs](https://docs.livekit.io/)
- [Next.js Docs](https://nextjs.org/docs)
- [Framer Motion](https://www.framer.com/motion/)
- [Tailwind CSS](https://tailwindcss.com/)

---

**Made for CalHacks 2025** 🚀
