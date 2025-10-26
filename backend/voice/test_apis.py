#!/usr/bin/env python3
"""
Quick test to verify Groq and ElevenLabs APIs are working
"""

import os
from dotenv import load_dotenv

load_dotenv(".env.local")

print("=" * 60)
print("API Keys Test")
print("=" * 60)

# Check Groq
groq_key = os.getenv("GROQ_API_KEY")
if groq_key:
    print(f"✅ GROQ_API_KEY: {groq_key[:20]}...")
else:
    print("❌ GROQ_API_KEY: NOT SET")

# Check ElevenLabs
eleven_key = os.getenv("ELEVEN_API_KEY")
if eleven_key:
    print(f"✅ ELEVEN_API_KEY: {eleven_key[:20]}...")
else:
    print("❌ ELEVEN_API_KEY: NOT SET")

# Check LiveKit
livekit_url = os.getenv("LIVEKIT_URL")
if livekit_url:
    print(f"✅ LIVEKIT_URL: {livekit_url}")
else:
    print("❌ LIVEKIT_URL: NOT SET")

print("=" * 60)

# Test Groq API
if groq_key:
    print("\n🔍 Testing Groq API...")
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)

        # Test LLM
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say hello in 3 words"}],
            max_tokens=10
        )
        print(f"✅ Groq LLM works! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Groq API error: {e}")

# Test ElevenLabs API
if eleven_key:
    print("\n🔍 Testing ElevenLabs API...")
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=eleven_key)

        # List voices to verify API works
        voices = client.voices.get_all()
        print(f"✅ ElevenLabs API works! Found {len(voices.voices)} voices")
    except Exception as e:
        print(f"❌ ElevenLabs API error: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
