#!/bin/bash

# AgentFlow FAST Computer Use - Quick Start Script
# Ultra-fast, accurate computer use system

echo "======================================================================="
echo "🚀 AgentFlow FAST Computer Use"
echo "======================================================================="
echo ""
echo "🎯 Gemini 2.5 Flash Computer Use"
echo "  • Native screen understanding (no OCR needed!)"
echo "  • Accurate clicking & interaction"
echo "  • ~1-2s per action (vision + reasoning)"
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Error: Run this script from the agentflow root directory"
    exit 1
fi

# Load .env file if it exists
if [ -f ".env" ]; then
    source .env
fi

# Check API keys
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Error: GOOGLE_API_KEY not set (required for Gemini Computer Use)"
    echo ""
    echo "Get your API key at: https://aistudio.google.com/apikey"
    echo ""
    echo "Then run:"
    echo "  export GOOGLE_API_KEY='your_key_here'"
    echo "  ./start_fast_computer_use.sh"
    echo ""
    exit 1
fi

if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  Note: GROQ_API_KEY not set (optional, for fast LLM reasoning)"
    echo "   Get your API key at: https://console.groq.com/keys"
    echo ""
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

echo ""
echo "======================================================================="
echo "✨ Fast Computer Use System Ready!"
echo "======================================================================="
echo ""
echo "What would you like to do?"
echo ""
echo "1. ⭐ Start Intelligent Workflow System (learn & execute workflows)"
echo "2. Test Gemini Computer Use (element detection & clicking)"
echo "3. Test Groq Client (fast LLM reasoning)"
echo "4. Test Coordinate Normalizer (resolution-independent coords)"
echo "5. Run all tests"
echo ""

read -p "Choose [1-5] or Enter to skip: " choice

cd backend

case $choice in
    1)
        echo ""
        echo "🚀 Starting Intelligent Workflow System..."
        echo "======================================================================="
        python workflow_cli.py
        ;;
    2)
        echo ""
        echo "🧪 Testing Gemini Computer Use..."
        echo "======================================================================="
        python gemini_computer_use.py
        ;;
    3)
        echo ""
        echo "🧪 Testing Groq Client..."
        echo "======================================================================="
        python groq_client.py
        ;;
    4)
        echo ""
        echo "🧪 Testing Coordinate Normalizer..."
        echo "======================================================================="
        python coordinate_normalizer.py
        ;;
    5)
        echo ""
        echo "🧪 Running all tests (non-interactive)..."
        echo "======================================================================="
        echo ""
        echo "Test 1: Gemini Computer Use"
        echo "-------------------------------------------------------------------"
        python gemini_computer_use.py
        echo ""
        echo ""
        echo "Test 2: Groq Client"
        echo "-------------------------------------------------------------------"
        python groq_client.py
        echo ""
        echo ""
        echo "Test 3: Coordinate Normalizer"
        echo "-------------------------------------------------------------------"
        python coordinate_normalizer.py
        echo ""
        ;;
    *)
        echo ""
        echo "Skipping tests."
        ;;
esac

cd ..

echo ""
echo "======================================================================="
echo "📚 Documentation"
echo "======================================================================="
echo ""
echo "Architecture:     docs/FAST_COMPUTER_USE_ARCHITECTURE.md"
echo "Implementation:   docs/FAST_COMPUTER_USE_IMPLEMENTATION.md"
echo "Requirements:     backend/requirements_fast.txt"
echo ""
echo "Components:"
echo "  • intelligent_workflow_system.py - ⭐ Learn & execute workflows from prompts"
echo "  • gemini_computer_use.py         - Gemini 2.5 native computer use"
echo "  • semantic_workflow_matcher.py   - Find similar workflows"
echo "  • gemini_workflow_executor.py    - Execute workflows with adaptation"
echo "  • groq_client.py                 - Ultra-fast LLM reasoning"
echo "  • coordinate_normalizer.py       - Resolution-independent coords"
echo ""
echo "======================================================================="
echo ""

# Deactivate on exit
deactivate

