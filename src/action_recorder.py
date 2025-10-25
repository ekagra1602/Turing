"""
Action Recorder - Records user actions (clicks) with timestamps
"""

import time
import json
from datetime import datetime
from pynput import mouse
from window_manager import WindowManager

# Try to load calibration
try:
    from calibrate import load_calibration
    CALIBRATION_AVAILABLE = True
except:
    CALIBRATION_AVAILABLE = False


class ActionRecorder:
    """Records user clicks and timing information"""

    def __init__(self):
        self.is_recording = False
        self.actions = []
        self.start_time = None
        self.last_action_time = None
        self.window_manager = WindowManager()
        self.initial_window_state = None
        self.mouse_listener = None

    def start_recording(self):
        """Start recording user actions"""
        if self.is_recording:
            print("Already recording!")
            return False

        print("Starting recording...")
        print("⚠️  If you see 'not trusted' error, you need to grant Accessibility permissions!")
        print("   See PERMISSIONS_FIX.md for step-by-step instructions.")
        print()

        self.is_recording = True
        self.actions = []
        self.start_time = time.time()
        self.last_action_time = self.start_time

        # Capture initial window positions
        self.initial_window_state = self.window_manager.get_all_windows()
        print(f"Captured {len(self.initial_window_state)} window positions")

        # Start listening for mouse clicks
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.mouse_listener.start()

        print("👂 Listening for clicks... (Don't click the overlay buttons!)")
        return True

    def stop_recording(self):
        """Stop recording user actions"""
        if not self.is_recording:
            print("Not currently recording!")
            return False

        print("Stopping recording...")
        self.is_recording = False

        # Stop the mouse listener
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        print(f"Recorded {len(self.actions)} actions")
        return True

    def _on_click(self, x, y, button, pressed):
        """Callback for mouse click events"""
        # Only record on button press, not release
        if not pressed or not self.is_recording:
            return

        current_time = time.time()
        wait_time = current_time - self.last_action_time

        # Round coordinates to nearest integer for consistency
        # Use round() instead of int() to minimize positioning errors
        rounded_x = round(x)
        rounded_y = round(y)

        action = {
            'type': 'click',
            'x': rounded_x,
            'y': rounded_y,
            'button': str(button),  # Button.left, Button.right, etc.
            'wait_before': round(wait_time, 3),  # seconds to wait before this action
            'timestamp': datetime.fromtimestamp(current_time).isoformat()
        }

        self.actions.append(action)
        self.last_action_time = current_time

        print(f"Recorded click at ({rounded_x}, {rounded_y}) with {wait_time:.2f}s wait")

    def save_recording(self, filename):
        """Save the recording to a JSON file"""
        if not self.actions and not self.initial_window_state:
            print("No recording to save!")
            return False

        recording_data = {
            'metadata': {
                'recorded_at': datetime.now().isoformat(),
                'duration': round(time.time() - self.start_time, 3) if self.start_time else 0,
                'action_count': len(self.actions)
            },
            'windows': self.initial_window_state or [],
            'actions': self.actions
        }

        try:
            with open(filename, 'w') as f:
                json.dump(recording_data, f, indent=2)
            print(f"Recording saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving recording: {e}")
            return False

    def load_recording(self, filename):
        """Load a recording from a JSON file"""
        try:
            with open(filename, 'r') as f:
                recording_data = json.load(f)

            self.initial_window_state = recording_data.get('windows', [])
            self.actions = recording_data.get('actions', [])

            print(f"Loaded recording with {len(self.actions)} actions")
            print(f"Recording duration: {recording_data['metadata'].get('duration', 0):.2f}s")
            return True
        except Exception as e:
            print(f"Error loading recording: {e}")
            return False

    def get_recording_info(self):
        """Get information about the current recording"""
        return {
            'is_recording': self.is_recording,
            'action_count': len(self.actions),
            'window_count': len(self.initial_window_state) if self.initial_window_state else 0
        }
