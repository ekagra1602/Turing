#!/usr/bin/env python3
"""
AgentFlow Voice Assistant - LiveKit Integration
Voice interface for AgentFlow using Groq and ElevenLabs.
Now with desktop workflow execution capabilities!
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

# Import our voice workflow bridge
from voice_workflow_bridge import get_voice_bridge

logger = logging.getLogger("agentflow-voice")
logger.setLevel(logging.INFO)

# Enable debug logging for livekit
logging.getLogger("livekit.agents").setLevel(logging.DEBUG)

# Load environment variables
load_dotenv(".env.local")


AGENT_INSTRUCTIONS = """You are AgentFlow, a helpful voice AI assistant that learns workflows by observation and can execute them automatically.

You help users in three main ways:
1. RECORDING MODE: When users say things like "remember what I'm going to do now" or "watch me do this",
   you acknowledge that you're ready to observe and learn their workflow.

2. EXECUTION MODE: When users ask you to perform tasks like "send this email" or "open my Canvas class",
   you automatically execute the learned workflow using desktop automation.

3. GENERAL ASSISTANCE: For other questions, you provide helpful responses.

IMPORTANT: When users give you execution commands, you should:
- Acknowledge the request briefly
- Automatically execute the workflow in the background
- Provide status updates on the execution
- Let them know when it's complete

Your responses should be:
- Conversational and natural (you're speaking, not writing)
- Brief and to the point (avoid long explanations)
- Friendly and encouraging
- Without special formatting, emojis, or asterisks
- Confirming actions before and after execution

You have a sense of humor and are curious about what users are teaching you.
"""


class WorkflowAwareAgent(Agent):
    """Custom Agent that can execute workflows based on voice commands"""
    
    def __init__(self, instructions: str, workflow_bridge=None):
        super().__init__(instructions=instructions)
        self.workflow_bridge = workflow_bridge
        self.is_executing_workflow = False
    
    async def on_user_message(self, message: str):
        """Override to handle workflow execution before normal processing"""
        if not self.workflow_bridge:
            return await super().on_user_message(message)
        
        # Check if this is a workflow command
        is_workflow, cmd_type = self.workflow_bridge.is_workflow_command(message)
        
        if is_workflow and cmd_type == 'execute':
            # This is a workflow execution command
            logger.info(f"Detected workflow execution command: {message}")
            
            # Acknowledge the request
            await self.say("Got it! I'll execute that for you right away.")
            
            # Execute the workflow asynchronously
            asyncio.create_task(self._execute_workflow_async(message))
            
        elif is_workflow and cmd_type == 'record':
            # This is a recording command
            logger.info(f"Detected recording command: {message}")
            result = self.workflow_bridge.prepare_recording_mode()
            await self.say(result['message'])
            
        else:
            # Normal conversation
            return await super().on_user_message(message)
    
    async def _execute_workflow_async(self, command: str):
        """Execute workflow asynchronously and provide updates"""
        try:
            self.is_executing_workflow = True
            
            # Execute the workflow
            result = await self.workflow_bridge.execute_workflow_from_voice(command)
            
            if result['success']:
                await self.say("Perfect! I've completed your request.")
                if result.get('workflow_name'):
                    await self.say(f"I used the {result['workflow_name']} workflow to do that.")
            else:
                await self.say(f"Sorry, I couldn't complete that request. {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in workflow execution: {e}")
            await self.say("Sorry, there was an error executing your request.")
        finally:
            self.is_executing_workflow = False


def prewarm(proc: JobProcess):
    """Prewarm function to load models before agent starts."""
    # Load Voice Activity Detection model
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("VAD model preloaded")
    
    # Initialize voice workflow bridge
    try:
        bridge = get_voice_bridge()
        proc.userdata["workflow_bridge"] = bridge
        logger.info("Voice workflow bridge initialized")
    except Exception as e:
        logger.error(f"Failed to initialize workflow bridge: {e}")
        proc.userdata["workflow_bridge"] = None


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

    # Get the workflow bridge from prewarm
    workflow_bridge = ctx.proc.userdata.get("workflow_bridge")
    
    # Create workflow-aware agent with instructions
    assistant = WorkflowAwareAgent(
        instructions=AGENT_INSTRUCTIONS,
        workflow_bridge=workflow_bridge
    )

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
    
    if workflow_bridge:
        workflows = workflow_bridge.get_available_workflows()
        logger.info(f"Workflow integration active - {len(workflows)} workflows available")
    else:
        logger.warning("Workflow integration not available")

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
