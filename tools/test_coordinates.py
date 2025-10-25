#!/usr/bin/env python3
"""
Test coordinate systems to debug positioning issues
"""

import pyautogui
from pynput import mouse

print("Screen Information:")
print("=" * 60)

# PyAutoGUI screen info
screen_width, screen_height = pyautogui.size()
print(f"PyAutoGUI screen size: {screen_width} x {screen_height}")

# Get current mouse position
current_pos = pyautogui.position()
print(f"Current mouse position (pyautogui): {current_pos}")

print("\nTesting coordinate capture...")
print("Move your mouse and click somewhere - we'll compare coordinates")
print("-" * 60)

clicks_recorded = []

def on_click(x, y, button, pressed):
    if pressed:
        print(f"\npynput captured: ({x}, {y})")
        print(f"  - Raw: x={x}, y={y}")
        print(f"  - Rounded: x={round(x)}, y={round(y)}")
        print(f"  - Int: x={int(x)}, y={int(y)}")

        # Get pyautogui's version
        pyauto_pos = pyautogui.position()
        print(f"pyautogui says: ({pyauto_pos.x}, {pyauto_pos.y})")

        clicks_recorded.append({
            'pynput_raw': (x, y),
            'pynput_rounded': (round(x), round(y)),
            'pynput_int': (int(x), int(y)),
            'pyautogui': (pyauto_pos.x, pyauto_pos.y)
        })

        if len(clicks_recorded) >= 3:
            print("\n" + "=" * 60)
            print("Summary of coordinate differences:")
            for i, click in enumerate(clicks_recorded, 1):
                print(f"\nClick {i}:")
                pn_x, pn_y = click['pynput_rounded']
                pa_x, pa_y = click['pyautogui']
                diff_x = abs(pn_x - pa_x)
                diff_y = abs(pn_y - pa_y)
                print(f"  pynput: ({pn_x}, {pn_y})")
                print(f"  pyautogui: ({pa_x}, {pa_y})")
                print(f"  difference: ({diff_x}, {diff_y})")

            listener.stop()
            return False

# Start listener
with mouse.Listener(on_click=on_click) as listener:
    print("\nClick 3 times anywhere on screen...")
    listener.join()

print("\nTest complete!")
