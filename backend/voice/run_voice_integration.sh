#!/bin/bash

echo "======================================="
echo "AgentFlow Voice Integration Launcher"
echo "======================================="
echo ""

# Check if we're in the right directory
if [ ! -f "agent.py" ]; then
    echo "❌ Please run this script from backend/voice/ directory"
    echo "   cd backend/voice && ./run_voice_integration.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/pyvenv.cfg" ] || [ ! -d "venv/lib" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Test the integration
echo ""
echo "🧪 Testing voice integration..."
python test_voice_integration.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Integration test passed!"
    echo ""
    echo "🚀 Starting voice agent with workflow integration..."
    echo ""
    echo "The voice agent will now:"
    echo "  • Listen for voice commands"
    echo "  • Detect workflow execution requests"
    echo "  • Execute AgentFlow workflows automatically"
    echo "  • Provide voice feedback on execution status"
    echo ""
    echo "Start the frontend in another terminal:"
    echo "  cd frontend && npm run dev"
    echo ""
    echo "Then open http://localhost:3000 and try:"
    echo "  • 'Send an email to John'"
    echo "  • 'Open my Canvas class'"
    echo "  • 'Remember what I'm going to do now'"
    echo ""
    
    # Start the voice agent
    python agent.py dev
else
    echo ""
    echo "❌ Integration test failed!"
    echo "Please check the error messages above and fix any issues."
    echo ""
    echo "Common issues:"
    echo "  • Missing API keys in .env.local"
    echo "  • AgentFlow system not properly set up"
    echo "  • Missing dependencies"
    echo ""
    exit 1
fi
