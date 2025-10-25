#!/bin/bash
# AgentFlow Basic - Fast click recording

echo "🚀 Starting AgentFlow Basic..."

# Setup venv if needed
if [ ! -d "venv_gui" ]; then
    echo "📦 First-time setup..."
    /usr/bin/python3 -m venv venv_gui
    ./venv_gui/bin/pip install -q pyautogui pynput pillow
    echo "✅ Setup complete!"
fi

# Launch
echo "🎨 Launching overlay (top-right corner)..."
./venv_gui/bin/python src/minimal_overlay.py
