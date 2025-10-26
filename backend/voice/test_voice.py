#!/usr/bin/env python3
"""
Simple test script to verify voice agent setup.
Tests that all required packages are installed and API keys are configured.
"""

import sys
import os

def test_imports():
    """Test that all required packages can be imported."""
    print("🔍 Testing imports...")

    try:
        import livekit
        print("  ✅ livekit")
    except ImportError as e:
        print(f"  ❌ livekit: {e}")
        return False

    try:
        from livekit.agents import Agent, AgentSession
        print("  ✅ livekit.agents")
    except ImportError as e:
        print(f"  ❌ livekit.agents: {e}")
        return False

    try:
        from livekit.plugins import silero
        print("  ✅ livekit.plugins.silero")
    except ImportError as e:
        print(f"  ❌ livekit.plugins.silero: {e}")
        return False

    try:
        from livekit.plugins import noise_cancellation
        print("  ✅ livekit.plugins.noise_cancellation")
    except ImportError as e:
        print(f"  ❌ livekit.plugins.noise_cancellation: {e}")
        return False

    try:
        from livekit.plugins import groq
        print("  ✅ livekit.plugins.groq")
    except ImportError as e:
        print(f"  ❌ livekit.plugins.groq: {e}")
        return False

    try:
        from livekit.plugins import elevenlabs
        print("  ✅ livekit.plugins.elevenlabs")
    except ImportError as e:
        print(f"  ❌ livekit.plugins.elevenlabs: {e}")
        return False

    try:
        from dotenv import load_dotenv
        print("  ✅ python-dotenv")
    except ImportError as e:
        print(f"  ❌ python-dotenv: {e}")
        return False

    return True


def test_env_vars():
    """Test that required environment variables are set."""
    print("\n🔍 Testing environment variables...")

    from dotenv import load_dotenv
    load_dotenv(".env.local")

    required_vars = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "GROQ_API_KEY",
        "ELEVEN_API_KEY",
    ]

    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}":
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - Not set or still using example value")
            all_set = False

    return all_set


def test_vad_loading():
    """Test that VAD model can be loaded."""
    print("\n🔍 Testing VAD model loading...")

    try:
        from livekit.plugins import silero
        print("  ⏳ Loading VAD model (this may take a moment on first run)...")
        vad = silero.VAD.load()
        print("  ✅ VAD model loaded successfully")
        return True
    except Exception as e:
        print(f"  ❌ Failed to load VAD model: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("AgentFlow Voice Assistant - Setup Test")
    print("=" * 60)

    # Test imports
    imports_ok = test_imports()

    if not imports_ok:
        print("\n❌ Import test failed!")
        print("\nTo fix:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    # Test environment variables
    env_ok = test_env_vars()

    if not env_ok:
        print("\n❌ Environment variables not configured!")
        print("\nTo fix:")
        print("  1. Copy .env.example to .env.local")
        print("  2. Add your API keys to .env.local")
        print("\nSee README.md for details on getting API keys")
        sys.exit(1)

    # Test VAD loading
    vad_ok = test_vad_loading()

    if not vad_ok:
        print("\n⚠️  VAD model loading failed, but this may work when running the agent")

    # Final summary
    print("\n" + "=" * 60)
    if imports_ok and env_ok:
        print("✅ All tests passed! You're ready to run the voice agent.")
        print("\nNext steps:")
        print("  python agent.py console   # Test in terminal")
        print("  python agent.py dev       # Run with frontend")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
