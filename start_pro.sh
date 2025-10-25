#!/bin/bash

# AgentFlow PRO - Quick Start Script
# Professional-grade learn-by-observation system

echo "======================================================================="
echo "🚀 AgentFlow PRO - Professional Edition"
echo "======================================================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Error: Run this script from the agentflow root directory"
    exit 1
fi

# Check API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Error: GOOGLE_API_KEY not set"
    echo ""
    echo "Get your API key at: https://makersuite.google.com/app/apikey"
    echo ""
    echo "Then run:"
    echo "  export GOOGLE_API_KEY='your_key_here'"
    echo "  ./start_pro.sh"
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

# Check if dependencies are installed
if ! python -c "import sentence_transformers" 2>/dev/null; then
    echo "📦 Installing/updating dependencies..."
    echo "   (This may take a few minutes on first run)"
    pip install -q -r backend/requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies OK"
fi

echo ""
echo "======================================================================="
echo "✨ Starting AgentFlow PRO..."
echo "======================================================================="
echo ""

# Run the pro agent
cd backend
python agent_pro.py

# Deactivate on exit
deactivate
