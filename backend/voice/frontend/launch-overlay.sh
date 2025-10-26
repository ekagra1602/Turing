#!/bin/bash

echo "======================================="
echo "AgentFlow Voice - Desktop Overlay"
echo "======================================="

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 First time setup - installing dependencies..."
    npm install
fi

echo ""
echo "🚀 Launching desktop overlay..."
echo ""
echo "The overlay will appear in the top-right corner of your screen!"
echo "Press Ctrl+C to stop."
echo ""

npm run electron:dev
