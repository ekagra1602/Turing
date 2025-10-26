#!/bin/bash

# AgentFlow VIDEO - Quick Start Script
# Video-based learn-by-observation system with post-processing

echo "======================================================================="
echo "🎥 AgentFlow VIDEO - Learn by Observation"
echo "======================================================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Error: Run this script from the agentflow root directory"
    exit 1
fi

# load .env file
source .env

# Check API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Error: GOOGLE_API_KEY not set"
    echo ""
    echo "Get your API key at: https://makersuite.google.com/app/apikey"
    echo ""
    echo "Then run:"
    echo "  export GOOGLE_API_KEY='your_key_here'"
    echo "  ./start_video.sh"
    echo ""
    exit 1
fi

# Check if venv exists
if [ ! -d "backend/venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate venv
echo "📦 Activating virtual environment..."
source backend/venv/bin/activate

# Check for tkinter (required for GUI)
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo ""
    echo "⚠️  tkinter not available!"
    echo ""
    echo "On macOS with Homebrew Python, install with:"
    echo "  brew install python-tk@3.13"
    echo ""
    echo "Or reinstall Python with tk support:"
    echo "  brew reinstall python@3.13"
    echo ""
    exit 1
fi

# Check if dependencies are installed
if ! python -c "import cv2" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    echo "   (This includes OpenCV for video recording)"
    pip install -q -r backend/requirements.txt
    
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies OK"
fi

echo ""
echo "======================================================================="
echo "✨ Starting AgentFlow VIDEO..."
echo "======================================================================="
echo ""

# Run the video agent
cd backend
python agent_video.py "$@"

# Deactivate on exit
deactivate

