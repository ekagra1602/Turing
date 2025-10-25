#!/usr/bin/env python3
"""
Coordinate system fixer for macOS Retina displays
"""

import subprocess
import re


class CoordinateFixer:
    """Handles coordinate system conversions for macOS"""

    def __init__(self):
        self.scale_factor = self._detect_scale_factor()
        print(f"Detected display scale factor: {self.scale_factor}")

    def _detect_scale_factor(self):
        """
        Detect if we're on a Retina display and get scale factor
        """
        try:
            # Try to get display info using system_profiler
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout

            # Look for Retina in output
            if 'Retina' in output or 'retina' in output:
                print("Retina display detected")
                # Most Retina displays use 2x scaling
                return 2.0

            # Check for resolution info to determine scaling
            if 'Resolution' in output:
                # Try to parse resolution
                match = re.search(r'(\d+)\s*x\s*(\d+)', output)
                if match:
                    width = int(match.group(1))
                    # If width > 2560, likely a Retina display
                    if width >= 2560:
                        return 2.0

        except Exception as e:
            print(f"Could not detect display type: {e}")

        # Default to no scaling
        return 1.0

    def fix_recording_coords(self, x, y):
        """
        Convert pynput coordinates to pyautogui coordinates
        On Retina displays, pynput might report physical pixels
        while pyautogui expects logical pixels
        """
        # If scale factor is 2 and coordinates seem too large, divide by 2
        import pyautogui
        screen_w, screen_h = pyautogui.size()

        # Check if coordinates are out of bounds
        if x > screen_w or y > screen_h:
            print(f"Coordinates ({x}, {y}) exceed screen size ({screen_w}x{screen_h})")
            print(f"Applying scale factor: {self.scale_factor}")
            return int(x / self.scale_factor), int(y / self.scale_factor)

        return x, y

    def fix_playback_coords(self, x, y):
        """
        Ensure playback coordinates are in pyautogui's coordinate system
        """
        import pyautogui
        screen_w, screen_h = pyautogui.size()

        # Clamp to screen bounds
        x = max(0, min(x, screen_w - 1))
        y = max(0, min(y, screen_h - 1))

        return x, y


def test_coordinate_system():
    """Test the coordinate system"""
    import pyautogui
    from pynput import mouse
    import time

    fixer = CoordinateFixer()

    print("\n" + "=" * 70)
    print("Coordinate System Test")
    print("=" * 70)

    screen_w, screen_h = pyautogui.size()
    print(f"PyAutoGUI screen size: {screen_w} x {screen_h}")

    print("\nClick anywhere...")

    clicks = []

    def on_click(x, y, button, pressed):
        if pressed:
            clicks.append((x, y))
            print(f"\npynput raw: ({x:.2f}, {y:.2f})")

            # Apply fix
            fixed_x, fixed_y = fixer.fix_recording_coords(int(x), int(y))
            print(f"After fix: ({fixed_x}, {fixed_y})")

            # Check if in bounds
            if 0 <= fixed_x < screen_w and 0 <= fixed_y < screen_h:
                print("✅ Coordinates are within screen bounds")
            else:
                print("❌ Coordinates are out of bounds!")

            return False

    listener = mouse.Listener(on_click=on_click)
    listener.start()
    listener.join()

    if clicks:
        raw_x, raw_y = clicks[0]
        fixed_x, fixed_y = fixer.fix_recording_coords(int(raw_x), int(raw_y))

        print("\nTesting playback...")
        print(f"Moving mouse to fixed coordinates: ({fixed_x}, {fixed_y})")
        time.sleep(1)

        pyautogui.moveTo(fixed_x, fixed_y, duration=0.5)
        print("Did the mouse move to where you clicked? (y/n)")

        response = input().strip().lower()
        if response == 'y':
            print("✅ Coordinate fix is working!")
        else:
            print("❌ Still having issues")


if __name__ == "__main__":
    test_coordinate_system()
