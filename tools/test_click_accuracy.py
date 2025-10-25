#!/usr/bin/env python3
"""
Test click recording and playback accuracy
This will help us identify coordinate system issues
"""

import pyautogui
from pynput import mouse
import time

print("=" * 70)
print("Click Accuracy Test")
print("=" * 70)
print()

# Get screen info
screen_w, screen_h = pyautogui.size()
print(f"Screen size: {screen_w} x {screen_h}")
print()

# Step 1: Record a click
print("STEP 1: Record a click")
print("-" * 70)
print("Click anywhere on your screen...")

recorded_clicks = []

def on_click(x, y, button, pressed):
    if pressed:
        recorded_clicks.append((x, y))
        print(f"✓ Recorded click at: ({x:.2f}, {y:.2f})")
        print(f"  Rounded to: ({round(x)}, {round(y)})")
        return False  # Stop listening

listener = mouse.Listener(on_click=on_click)
listener.start()
listener.join()

if not recorded_clicks:
    print("No click recorded!")
    exit(1)

recorded_x, recorded_y = recorded_clicks[0]
playback_x = round(recorded_x)
playback_y = round(recorded_y)

print()

# Step 2: Show where we'll click
print("STEP 2: Playback test")
print("-" * 70)
print(f"I will click at: ({playback_x}, {playback_y})")
print()

# Get current mouse position
current_pos = pyautogui.position()
print(f"Your mouse is currently at: ({current_pos.x}, {current_pos.y})")
print()

# Move mouse to show where we'll click
print("Moving mouse to recorded position in 2 seconds...")
time.sleep(2)

pyautogui.moveTo(playback_x, playback_y, duration=0.5)
print(f"✓ Mouse moved to: ({playback_x}, {playback_y})")

# Check where mouse actually ended up
actual_pos = pyautogui.position()
print(f"  pyautogui reports mouse at: ({actual_pos.x}, {actual_pos.y})")

# Calculate error
error_x = abs(playback_x - actual_pos.x)
error_y = abs(playback_y - actual_pos.y)
print(f"  Position error: ({error_x}, {error_y}) pixels")

if error_x <= 1 and error_y <= 1:
    print("  ✅ Position is accurate!")
else:
    print(f"  ⚠️  Position is off by {max(error_x, error_y)} pixels")

print()
print("Visual check: Is the mouse where you clicked? (y/n)")
user_check = input().strip().lower()

if user_check == 'y':
    print("✅ Visual position confirmed!")
else:
    print("❌ Position mismatch detected")
    print()
    print("This suggests a coordinate system issue.")
    print("Possible causes:")
    print("  - Display scaling/retina display")
    print("  - Multiple monitors")
    print("  - pynput vs pyautogui coordinate mismatch")

print()

# Step 3: Actually click
print("STEP 3: Click test")
print("-" * 70)
print(f"I will click at ({playback_x}, {playback_y}) in 2 seconds...")
print("Watch if the click happens at the right spot!")
time.sleep(2)

pyautogui.click(playback_x, playback_y)
print("✓ Click executed")

print()
print("=" * 70)
print("Did the click happen where you originally clicked? (y/n)")
final_check = input().strip().lower()

if final_check == 'y':
    print("✅ SUCCESS! Click accuracy is working!")
else:
    print("❌ Click went to wrong place")
    print()
    print("Debugging info:")
    print(f"  Recorded: ({recorded_x:.2f}, {recorded_y:.2f})")
    print(f"  Rounded:  ({playback_x}, {playback_y})")
    print(f"  Actual:   ({actual_pos.x}, {actual_pos.y})")
    print()
    print("Next steps:")
    print("  1. Check if you have a Retina display (might need scaling)")
    print("  2. Check display settings for resolution/scaling")
    print("  3. Try clicking in different areas of the screen")

print()
