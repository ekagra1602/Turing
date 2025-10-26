#!/bin/bash

echo "================================"
echo "AgentFlow Voice Overlay"
echo "================================"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check for .env.local
if [ ! -f ".env.local" ]; then
    echo "⚠️  Warning: .env.local not found!"
    echo "Copy .env.example to .env.local and add your LiveKit credentials"
    exit 1
fi

echo "🚀 Starting development server..."
npm run dev
