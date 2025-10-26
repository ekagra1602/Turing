#!/bin/bash

# AgentFlow Pro - Video-Based Recorder
# This script starts the professional recording UI

echo "=================================================="
echo "🚀 AgentFlow Pro - Video Recorder"
echo "=================================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo ""
    echo "Please run:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements_fast.txt"
    echo ""
    exit 1
fi

# Activate venv
source venv/bin/activate

echo "✅ Environment ready"
echo ""
echo "Starting recorder UI..."
echo ""

# Run the recorder UI
python recorder_ui.py
