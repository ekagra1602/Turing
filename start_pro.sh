#!/bin/bash
# AgentFlow Pro - Full interaction recording

echo "🚀 Starting AgentFlow Pro..."

# Setup venv if needed
if [ ! -d "venv_gui" ]; then
    echo "📦 First-time setup..."
    /usr/bin/python3 -m venv venv_gui
    ./venv_gui/bin/pip install -q pyautogui pynput pillow
    echo "✅ Setup complete!"
fi

# Launch
echo "🎨 Launching pro overlay (top-right corner)..."
echo ""
echo "✨ Pro Features:"
echo "   - 🖱️  Mouse movements"
echo "   - ⌨️  Keyboard input"
echo "   - 📜 Scrolling"
echo "   - ↔️  Drag & drop"
echo ""
./venv_gui/bin/python src/enhanced_overlay.py
