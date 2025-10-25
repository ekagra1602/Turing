#!/bin/bash
# Quick test to diagnose click positioning issues

echo "========================================"
echo "  AgentFlow Click Position Test"
echo "========================================"
echo ""
echo "This will help us figure out why clicks aren't accurate"
echo ""
echo "Test 1: Screen size check"
./venv_gui/bin/python -c "
import pyautogui
w, h = pyautogui.size()
print(f'Screen size: {w} x {h}')
pos = pyautogui.position()
print(f'Current mouse: ({pos.x}, {pos.y})')
"

echo ""
echo "Test 2: Record and replay a single click"
echo ""
echo "Running test_click_accuracy.py..."
echo "Follow the instructions to click once."
echo ""

./venv_gui/bin/python test_click_accuracy.py
