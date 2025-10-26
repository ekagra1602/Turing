#!/bin/bash

echo "=========================================="
echo "AgentFlow Voice - Desktop Overlay Mode"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "agent.py" ]; then
    echo "❌ Error: Must run from backend/voice/ directory"
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check .env.local
if [ ! -f ".env.local" ]; then
    echo "❌ Error: .env.local not found!"
    echo "Copy .env.example to .env.local and add your API keys"
    exit 1
fi

# Check if frontend exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend/ directory not found!"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Check frontend .env.local
if [ ! -f "frontend/.env.local" ]; then
    echo "❌ Error: frontend/.env.local not found!"
    echo "Copy frontend/.env.example to frontend/.env.local"
    exit 1
fi

echo ""
echo "✅ All checks passed!"
echo ""
echo "🚀 Starting backend voice agent..."
echo ""

# Start backend in background
python agent.py dev &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 3

echo ""
echo "🎨 Launching Electron desktop overlay..."
echo "   The overlay will appear in top-right corner!"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Start Electron overlay (this blocks)
cd frontend
npm run electron:dev &
FRONTEND_PID=$!

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    # Also kill any remaining Node/Electron processes
    pkill -f "electron.*agentflow" 2>/dev/null
    pkill -f "next dev" 2>/dev/null
    exit 0
}

trap cleanup INT TERM EXIT

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
