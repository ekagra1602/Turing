#!/usr/bin/env python3
"""
Quick test to verify screen control is working.
"""

import time
import sys
import os


def test_imports():
    """Test that all required libraries can be imported."""
    print("Testing imports...")
    try:
        import pyautogui
        print("  ✅ pyautogui")
    except ImportError as e:
        print(f"  ❌ pyautogui: {e}")
        return False

    try:
        from PIL import Image
        print("  ✅ PIL/Pillow")
    except ImportError as e:
        print(f"  ❌ PIL/Pillow: {e}")
        return False

    try:
        from google import genai
        print("  ✅ google-genai")
    except ImportError as e:
        print(f"  ❌ google-genai: {e}")
        return False

    return True


def test_screen_access():
    """Test that we can access the screen."""
    print("\nTesting screen access...")
    try:
        import pyautogui
        screen_width, screen_height = pyautogui.size()
        print(f"  ✅ Screen size: {screen_width}x{screen_height}")
        return True
    except Exception as e:
        print(f"  ❌ Cannot get screen size: {e}")
        return False


def test_mouse_position():
    """Test that we can get mouse position."""
    print("\nTesting mouse position...")
    try:
        import pyautogui
        x, y = pyautogui.position()
        print(f"  ✅ Mouse position: ({x}, {y})")
        return True
    except Exception as e:
        print(f"  ❌ Cannot get mouse position: {e}")
        print("     You may need Accessibility permissions!")
        return False


def test_screenshot():
    """Test that we can take screenshots."""
    print("\nTesting screenshot...")
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        print(f"  ✅ Screenshot captured: {screenshot.size}")
        return True
    except Exception as e:
        print(f"  ❌ Cannot take screenshot: {e}")
        print("     You may need Screen Recording permissions!")
        return False


def test_mouse_move():
    """Test that we can move the mouse."""
    print("\nTesting mouse control...")
    print("  Watch your mouse cursor...")

    try:
        import pyautogui
        pyautogui.PAUSE = 0.5

        # Get current position
        start_x, start_y = pyautogui.position()
        print(f"  Starting position: ({start_x}, {start_y})")

        # Move mouse slightly
        print("  Moving mouse...")
        pyautogui.move(50, 50, duration=0.5)
        time.sleep(0.5)

        # Check new position
        new_x, new_y = pyautogui.position()
        print(f"  New position: ({new_x}, {new_y})")

        # Move back
        print("  Moving back...")
        pyautogui.moveTo(start_x, start_y, duration=0.5)

        print("  ✅ Mouse control working!")
        return True

    except Exception as e:
        print(f"  ❌ Cannot move mouse: {e}")
        return False


def test_api_key():
    """Test that API key is set."""
    print("\nTesting API key...")
    if "GOOGLE_API_KEY" in os.environ:
        key = os.environ["GOOGLE_API_KEY"]
        if key and len(key) > 10:
            print(f"  ✅ API key set (length: {len(key)})")
            return True
        else:
            print(f"  ❌ API key too short or empty")
            return False
    else:
        print(f"  ❌ GOOGLE_API_KEY not set")
        return False


def main():
    print("=" * 70)
    print("AgentFlow - Screen Control Test")
    print("=" * 70)
    print()

    all_tests_passed = True

    # Run tests
    all_tests_passed &= test_imports()
    all_tests_passed &= test_screen_access()
    all_tests_passed &= test_mouse_position()
    all_tests_passed &= test_screenshot()
    all_tests_passed &= test_api_key()

    # Optional mouse movement test
    print()
    response = input("Test mouse movement? (your cursor will move) [Y/n]: ").strip().lower()
    if response != 'n':
        all_tests_passed &= test_mouse_move()

    # Summary
    print()
    print("=" * 70)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED!")
        print()
        print("Your system is ready for AgentFlow!")
        print("Run: ./agent_interface.py")
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Fix the issues above before running AgentFlow.")
        print()
        print("Common fixes:")
        print("1. Install missing packages:")
        print("   pip install pyautogui pillow google-genai")
        print()
        print("2. Grant permissions:")
        print("   System Settings > Privacy & Security")
        print("   - Accessibility: Add Terminal")
        print("   - Screen Recording: Enable for Terminal")
        print()
        print("3. Set API key:")
        print("   export GOOGLE_API_KEY='your_key_here'")

    print("=" * 70)

    sys.exit(0 if all_tests_passed else 1)


if __name__ == "__main__":
    main()
