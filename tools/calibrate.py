#!/usr/bin/env python3
"""
Calibration tool to fix coordinate mismatches
"""

import pyautogui
from pynput import mouse
import time
import json
import os

CALIBRATION_FILE = "calibration.json"


def calibrate():
    """
    Run calibration by having user click known positions
    """
    print("=" * 70)
    print("AgentFlow Coordinate Calibration")
    print("=" * 70)
    print()
    print("This will help fix coordinate positioning issues.")
    print("You'll click 4 corners of your screen to build a coordinate map.")
    print()

    screen_w, screen_h = pyautogui.size()
    print(f"Screen size: {screen_w} x {screen_h}")
    print()

    # Define calibration points (in pyautogui coordinates)
    cal_points = [
        (100, 100, "top-left"),
        (screen_w - 100, 100, "top-right"),
        (100, screen_h - 100, "bottom-left"),
        (screen_w - 100, screen_h - 100, "bottom-right"),
    ]

    recordings = []

    for target_x, target_y, corner in cal_points:
        print(f"Calibration point: {corner}")
        print(f"Target: ({target_x}, {target_y})")
        print()

        # Move mouse to target
        print("Moving mouse to target position...")
        pyautogui.moveTo(target_x, target_y, duration=1)
        time.sleep(0.5)

        print("Click at this EXACT position...")
        print()

        # Record click
        clicks = []

        def on_click(x, y, button, pressed):
            if pressed:
                clicks.append((x, y))
                return False

        listener = mouse.Listener(on_click=on_click)
        listener.start()
        listener.join()

        if clicks:
            recorded_x, recorded_y = clicks[0]
            print(f"✓ Recorded: ({recorded_x:.2f}, {recorded_y:.2f})")

            # Calculate offset
            offset_x = target_x - round(recorded_x)
            offset_y = target_y - round(recorded_y)

            recordings.append({
                'target': (target_x, target_y),
                'recorded': (round(recorded_x), round(recorded_y)),
                'offset': (offset_x, offset_y),
                'corner': corner
            })

            print(f"  Offset: ({offset_x:+d}, {offset_y:+d})")
        else:
            print("✗ No click recorded")

        print()

    # Analyze results
    print("=" * 70)
    print("Calibration Results")
    print("=" * 70)
    print()

    if not recordings:
        print("No calibration data collected!")
        return None

    # Calculate average offset
    avg_offset_x = sum(r['offset'][0] for r in recordings) / len(recordings)
    avg_offset_y = sum(r['offset'][1] for r in recordings) / len(recordings)

    print(f"Average offset: ({avg_offset_x:+.1f}, {avg_offset_y:+.1f})")
    print()

    # Check if offset is consistent
    offsets_x = [r['offset'][0] for r in recordings]
    offsets_y = [r['offset'][1] for r in recordings]

    var_x = max(offsets_x) - min(offsets_x)
    var_y = max(offsets_y) - min(offsets_y)

    print(f"Offset variation: ({var_x}, {var_y}) pixels")
    print()

    if var_x <= 5 and var_y <= 5:
        print("✅ Consistent offset detected!")
        print("   This can be easily fixed with a simple offset correction.")
    else:
        print("⚠️  Inconsistent offsets detected!")
        print("   This might indicate a scaling issue or non-linear mapping.")

    print()

    # Create calibration data
    calibration_data = {
        'screen_size': (screen_w, screen_h),
        'average_offset': (round(avg_offset_x), round(avg_offset_y)),
        'recordings': recordings,
        'offset_variation': (var_x, var_y),
        'calibration_type': 'simple_offset' if (var_x <= 5 and var_y <= 5) else 'complex'
    }

    # Save calibration
    with open(CALIBRATION_FILE, 'w') as f:
        json.dump(calibration_data, f, indent=2)

    print(f"✓ Calibration saved to {CALIBRATION_FILE}")
    print()

    return calibration_data


def load_calibration():
    """Load calibration data"""
    if os.path.exists(CALIBRATION_FILE):
        with open(CALIBRATION_FILE, 'r') as f:
            return json.load(f)
    return None


def apply_calibration(x, y):
    """Apply calibration correction to coordinates"""
    cal = load_calibration()
    if not cal:
        return x, y

    offset_x, offset_y = cal['average_offset']
    return x + offset_x, y + offset_y


def test_calibration():
    """Test if calibration works"""
    cal = load_calibration()
    if not cal:
        print("No calibration file found. Run calibration first!")
        return

    print("=" * 70)
    print("Testing Calibration")
    print("=" * 70)
    print()

    offset_x, offset_y = cal['average_offset']
    print(f"Calibration offset: ({offset_x:+d}, {offset_y:+d})")
    print()

    print("Click anywhere...")

    clicks = []

    def on_click(x, y, button, pressed):
        if pressed:
            clicks.append((x, y))
            return False

    listener = mouse.Listener(on_click=on_click)
    listener.start()
    listener.join()

    if clicks:
        recorded_x, recorded_y = clicks[0]
        corrected_x, corrected_y = apply_calibration(round(recorded_x), round(recorded_y))

        print(f"Recorded: ({round(recorded_x)}, {round(recorded_y)})")
        print(f"Corrected: ({corrected_x}, {corrected_y})")
        print()
        print("Moving mouse to corrected position in 2 seconds...")
        time.sleep(2)

        pyautogui.moveTo(corrected_x, corrected_y, duration=0.5)
        print("✓ Mouse moved")
        print()
        print("Did it move back to where you clicked? (y/n)")

        response = input().strip().lower()
        if response == 'y':
            print("✅ Calibration is working!")
        else:
            print("❌ Calibration needs adjustment")
            print("   Try running calibration again")


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_calibration()
    else:
        calibration_data = calibrate()

        if calibration_data:
            print()
            print("=" * 70)
            print("Next Steps")
            print("=" * 70)
            print()
            print("1. Test calibration:")
            print("   ./venv_gui/bin/python calibrate.py test")
            print()
            print("2. If test works, AgentFlow will use this calibration automatically")
            print()


if __name__ == "__main__":
    main()
