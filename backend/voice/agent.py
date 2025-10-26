#!/usr/bin/env python3
"""
AgentFlow Voice Assistant - LiveKit Integration
Voice interface for AgentFlow using Groq and ElevenLabs.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
)
from livekit.plugins import noise_cancellation, silero, groq, elevenlabs

logger = logging.getLogger("agentflow-voice")
logger.setLevel(logging.INFO)

# Enable debug logging for livekit
logging.getLogger("livekit.agents").setLevel(logging.DEBUG)

# Load environment variables
load_dotenv(".env.local")


AGENT_INSTRUCTIONS = """You are AgentFlow, a helpful voice AI assistant that learns workflows by observation.

You help users in two main ways:
1. RECORDING MODE: When users say things like "remember what I'm going to do now" or "watch me do this",
   you acknowledge that you're ready to observe and learn their workflow.

2. EXECUTION MODE: When users ask you to perform tasks like "send this email" or "open my Canvas class",
   you confirm you understand the request and are ready to execute the learned workflow.

Your responses should be:
- Conversational and natural (you're speaking, not writing)
- Brief and to the point (avoid long explanations)
- Friendly and encouraging
- Without special formatting, emojis, or asterisks
- Confirming you understand before taking action

You have a sense of humor and are curious about what users are teaching you.
"""


def prewarm(proc: JobProcess):
    """Prewarm function to load models before agent starts."""
    # Load Voice Activity Detection model
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("VAD model preloaded")


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the voice agent.

    This function is called when an agent connects to a room.
    It sets up the voice pipeline with STT, LLM, and TTS.
    """

    # Set logging context
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    logger.info(f"Starting AgentFlow voice assistant in room: {ctx.room.name}")

    # Connect to room
    await ctx.connect()
    logger.info("Connected to LiveKit room")

    # Create simple agent with instructions
    assistant = Agent(instructions=AGENT_INSTRUCTIONS)

    # Create agent session with voice pipeline using plugin objects:
    # - STT: Groq Whisper (ultra-fast, FREE)
    # - LLM: Groq Llama 3.3 (powerful, FREE)
    # - TTS: ElevenLabs (premium quality, FREE tier)
    session = AgentSession(
        stt=groq.STT(model="whisper-large-v3-turbo"),
        llm=groq.LLM(model="llama-3.3-70b-versatile", temperature=0.7),
        tts=elevenlabs.TTS(voice_id="EXAVITQu4vr4xnSDxMaL", model="eleven_turbo_v2_5"),
        vad=ctx.proc.userdata["vad"],
    )

    # Start the agent session
    await session.start(room=ctx.room, agent=assistant)

    logger.info("Voice assistant is ready and listening")

    # Keep the session alive indefinitely
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()


if __name__ == "__main__":
    """
    Run the voice agent.

    Usage:
        # Test in console mode (speak directly in terminal)
        python agent.py console

        # Run in dev mode (connect to LiveKit room)
        python agent.py dev

        # Run in production mode
        python agent.py start
    """
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
