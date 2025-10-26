#!/bin/bash
# Quick setup script for AgentFlow Voice Assistant

set -e  # Exit on error

echo "🚀 AgentFlow Voice Assistant - Quick Setup"
echo "=========================================="

# Check Python version
echo ""
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found: Python $python_version"

# Check if version is >= 3.9
required_version="3.9"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "   ❌ Python 3.9 or higher is required"
    exit 1
fi
echo "   ✅ Python version OK"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo ""
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt
echo "   ✅ Dependencies installed"

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo ""
    echo "⚙️  Creating .env.local from example..."
    cp .env.example .env.local
    echo "   ✅ .env.local created"
    echo ""
    echo "   ⚠️  IMPORTANT: Edit .env.local and add your API keys!"
    echo "   See README.md for instructions on getting API keys"
else
    echo ""
    echo "⚙️  .env.local already exists"
fi

# Check if LiveKit CLI is installed
echo ""
echo "🔍 Checking for LiveKit CLI..."
if command -v lk &> /dev/null; then
    echo "   ✅ LiveKit CLI found"
    echo ""
    echo "   You can auto-populate LiveKit credentials with:"
    echo "   lk cloud auth"
    echo "   lk app env -w -d .env.local"
else
    echo "   ⚠️  LiveKit CLI not found (optional)"
    echo ""
    echo "   To install (macOS):"
    echo "   brew install livekit-cli"
    echo ""
    echo "   To install (Linux):"
    echo "   curl -sSL https://get.livekit.io/cli | bash"
fi

# Run tests
echo ""
echo "🧪 Running setup tests..."
python test_voice.py

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env.local with your API keys (see README.md)"
echo "  2. Test in console: python agent.py console"
echo "  3. Run dev mode: python agent.py dev"
echo ""
echo "=========================================="
