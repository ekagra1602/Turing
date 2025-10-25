#!/usr/bin/env python3
"""
Check if necessary permissions are granted for AgentFlow.
"""

import subprocess
import sys


def check_accessibility():
    """Check if Terminal has Accessibility permissions."""
    print("Checking Accessibility permissions...")

    try:
        # Try to get mouse position (requires accessibility)
        import pyautogui
        pos = pyautogui.position()
        print(f"✅ Accessibility: Granted (mouse at {pos})")
        return True
    except Exception as e:
        print(f"❌ Accessibility: Not granted")
        print(f"   Error: {e}")
        return False


def check_screen_recording():
    """Check if Terminal can take screenshots."""
    print("\nChecking Screen Recording permissions...")

    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        print(f"✅ Screen Recording: Granted (captured {screenshot.size})")
        return True
    except Exception as e:
        print(f"❌ Screen Recording: Not granted")
        print(f"   Error: {e}")
        return False


def main():
    print("=" * 70)
    print("AgentFlow Permission Checker")
    print("=" * 70)
    print()

    accessibility_ok = check_accessibility()
    screen_recording_ok = check_screen_recording()

    print()
    print("=" * 70)

    if accessibility_ok and screen_recording_ok:
        print("✅ All permissions granted! You're ready to use AgentFlow.")
        print()
        print("Run: ./agent_interface.py")
    else:
        print("⚠️  Some permissions are missing.")
        print()
        print("To grant permissions:")
        print()
        print("1. Open System Settings")
        print("2. Go to Privacy & Security")
        print()

        if not accessibility_ok:
            print("3. Click 'Accessibility'")
            print("4. Click the '+' button")
            print("5. Add Terminal (or your Python app)")
            print()

        if not screen_recording_ok:
            print("3. Click 'Screen Recording'")
            print("4. Check the box next to Terminal")
            print()

        print("Then restart your terminal and run this script again.")

    print("=" * 70)

    sys.exit(0 if (accessibility_ok and screen_recording_ok) else 1)


if __name__ == "__main__":
    main()
