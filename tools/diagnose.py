#!/usr/bin/env python3
"""
Diagnostic script to identify issues with AgentFlow
"""

import sys
import os

print("=" * 70)
print(" " * 20 + "AgentFlow Diagnostics")
print("=" * 70)
print()

# Test 1: Python version
print("1. Checking Python version...")
print(f"   Python {sys.version}")
if sys.version_info < (3, 7):
    print("   ⚠️  Warning: Python 3.7+ recommended")
else:
    print("   ✅ Python version OK")
print()

# Test 2: Required modules
print("2. Checking required modules...")
modules_ok = True

required_modules = [
    ('pyautogui', 'GUI automation'),
    ('pynput', 'Input monitoring'),
    ('tkinter', 'GUI framework')
]

for module_name, description in required_modules:
    try:
        __import__(module_name)
        print(f"   ✅ {module_name:15} - {description}")
    except ImportError as e:
        print(f"   ❌ {module_name:15} - MISSING ({description})")
        modules_ok = False

print()

# Test 3: Screen info
print("3. Checking screen information...")
try:
    import pyautogui
    width, height = pyautogui.size()
    pos = pyautogui.position()
    print(f"   Screen size: {width}x{height}")
    print(f"   Current mouse position: {pos}")
    print("   ✅ PyAutoGUI working")
except Exception as e:
    print(f"   ❌ PyAutoGUI error: {e}")
print()

# Test 4: Accessibility permissions
print("4. Checking accessibility permissions...")
print("   Testing if we can monitor mouse events...")

try:
    from pynput import mouse
    import time

    clicks_detected = []

    def on_click(x, y, button, pressed):
        if pressed:
            clicks_detected.append((x, y))
            return False  # Stop after first click

    print("   👉 Click anywhere on the screen once...")

    listener = mouse.Listener(on_click=on_click)
    listener.start()

    # Wait up to 5 seconds for a click
    start = time.time()
    while len(clicks_detected) == 0 and (time.time() - start) < 5:
        time.sleep(0.1)

    listener.stop()

    if clicks_detected:
        x, y = clicks_detected[0]
        print(f"   ✅ Detected click at ({x:.0f}, {y:.0f})")
        print("   ✅ Accessibility permissions are working!")
    else:
        print("   ❌ No click detected")
        print("   ⚠️  You may need to grant Accessibility permissions")
        print("      See PERMISSIONS_FIX.md for instructions")

except Exception as e:
    print(f"   ❌ Error testing permissions: {e}")
    print("   ⚠️  You need to grant Accessibility permissions")
    print("      See PERMISSIONS_FIX.md for instructions")

print()

# Test 5: Coordinate accuracy
print("5. Testing coordinate accuracy...")
if clicks_detected:
    x_pynput, y_pynput = clicks_detected[0]
    try:
        import pyautogui
        x_pyauto, y_pyauto = pyautogui.position()

        # Check if coordinates roughly match (within 50 pixels)
        diff_x = abs(x_pynput - x_pyauto)
        diff_y = abs(y_pynput - y_pyauto)

        print(f"   pynput captured: ({x_pynput:.0f}, {y_pynput:.0f})")
        print(f"   pyautogui says:  ({x_pyauto}, {y_pyauto})")
        print(f"   Difference: ({diff_x:.0f}, {diff_y:.0f}) pixels")

        if diff_x < 50 and diff_y < 50:
            print("   ✅ Coordinates match well")
        else:
            print("   ⚠️  Large coordinate difference detected")
            print("      This may cause clicks to go to wrong locations")
    except:
        print("   ⚠️  Could not verify coordinates")
else:
    print("   ⏭️  Skipped (no click detected)")

print()

# Test 6: AgentFlow modules
print("6. Checking AgentFlow modules...")
agentflow_modules = [
    'action_recorder',
    'action_player',
    'window_manager',
    'minimal_overlay'
]

for module in agentflow_modules:
    try:
        __import__(module)
        print(f"   ✅ {module}.py")
    except Exception as e:
        print(f"   ❌ {module}.py - {e}")

print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)

if modules_ok and clicks_detected:
    print("✅ All tests passed! AgentFlow should work.")
    print()
    print("To start AgentFlow:")
    print("  ./start_overlay.sh")
elif not clicks_detected:
    print("⚠️  Accessibility permissions need to be granted.")
    print()
    print("ACTION REQUIRED:")
    print("1. Open System Preferences → Security & Privacy → Privacy")
    print("2. Click 'Accessibility' in the left sidebar")
    print("3. Add Terminal (or python3) and check the box")
    print("4. Restart this script")
    print()
    print("See PERMISSIONS_FIX.md for detailed step-by-step instructions")
else:
    print("❌ Some tests failed. Check the output above.")
    print()
    print("Try:")
    print("  ./venv_gui/bin/pip install pyautogui pynput")

print()
print("For more help, see:")
print("  - README.md")
print("  - PERMISSIONS_FIX.md")
print("  - QUICKSTART.md")
print()
