"""
Enhanced Action Recorder - Records complete interaction including:
- Mouse movements (full path)
- Clicks
- Keyboard input
- Scrolling
- Drags
"""

import time
import json
from datetime import datetime
from pynput import mouse, keyboard
from window_manager import WindowManager


class EnhancedRecorder:
    """Records complete user interactions"""

    def __init__(self):
        self.is_recording = False
        self.actions = []
        self.start_time = None
        self.last_action_time = None
        self.window_manager = WindowManager()
        self.initial_window_state = None
        self.mouse_listener = None
        self.keyboard_listener = None

        # Recording options
        self.record_movements = True
        self.record_keyboard = True
        self.movement_sample_rate = 0.05  # Record position every 50ms

        # State tracking
        self.last_mouse_pos = None
        self.is_dragging = False
        self.drag_start = None

    def start_recording(self):
        """Start recording all user actions"""
        if self.is_recording:
            print("Already recording!")
            return False

        print("Starting enhanced recording...")
        print("⚠️  If you see 'not trusted' error, grant Accessibility permissions!")
        print("   See PERMISSIONS_FIX.md for instructions.")
        print()

        self.is_recording = True
        self.actions = []
        self.start_time = time.time()
        self.last_action_time = self.start_time
        self.last_mouse_pos = None
        self.is_dragging = False

        # Capture initial window positions
        self.initial_window_state = self.window_manager.get_all_windows()
        print(f"Captured {len(self.initial_window_state)} window positions")

        # Start listening for mouse events
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self.mouse_listener.start()

        # Start listening for keyboard events
        if self.record_keyboard:
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press
            )
            self.keyboard_listener.start()

        print("👂 Recording:")
        print(f"   - Mouse movements: {'ON' if self.record_movements else 'OFF'}")
        print(f"   - Mouse clicks: ON")
        print(f"   - Keyboard: {'ON' if self.record_keyboard else 'OFF'}")
        print(f"   - Scrolling: ON")
        print()

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

        # Stop the keyboard listener
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        print(f"Recorded {len(self.actions)} actions")
        self._print_summary()
        return True

    def _record_action(self, action):
        """Helper to record an action with timing"""
        current_time = time.time()
        wait_time = current_time - self.last_action_time

        action['wait_before'] = round(wait_time, 3)
        action['timestamp'] = datetime.fromtimestamp(current_time).isoformat()

        self.actions.append(action)
        self.last_action_time = current_time

    def _on_move(self, x, y):
        """Callback for mouse movement"""
        if not self.is_recording:
            return

        # Sample movements to avoid too many data points
        current_time = time.time()

        if self.last_mouse_pos is None or \
           (current_time - self.last_action_time) >= self.movement_sample_rate:

            # Only record if moved significantly (> 5 pixels)
            if self.last_mouse_pos is None or \
               abs(x - self.last_mouse_pos[0]) > 5 or \
               abs(y - self.last_mouse_pos[1]) > 5:

                if self.record_movements:
                    action = {
                        'type': 'move',
                        'x': round(x),
                        'y': round(y)
                    }
                    self._record_action(action)

                self.last_mouse_pos = (x, y)

    def _on_click(self, x, y, button, pressed):
        """Callback for mouse click events"""
        if not self.is_recording:
            return

        if pressed:
            # Mouse button pressed - might be start of drag
            action = {
                'type': 'click_down',
                'x': round(x),
                'y': round(y),
                'button': str(button)
            }
            self._record_action(action)
            self.drag_start = (round(x), round(y))

            print(f"Click at ({round(x)}, {round(y)})")
        else:
            # Mouse button released
            action = {
                'type': 'click_up',
                'x': round(x),
                'y': round(y),
                'button': str(button)
            }
            self._record_action(action)

            # Check if it was a drag
            if self.drag_start:
                dx = abs(round(x) - self.drag_start[0])
                dy = abs(round(y) - self.drag_start[1])
                if dx > 10 or dy > 10:
                    print(f"Drag detected: {self.drag_start} -> ({round(x)}, {round(y)})")

            self.drag_start = None

    def _on_scroll(self, x, y, dx, dy):
        """Callback for scroll events"""
        if not self.is_recording:
            return

        action = {
            'type': 'scroll',
            'x': round(x),
            'y': round(y),
            'dx': dx,
            'dy': dy
        }
        self._record_action(action)
        print(f"Scroll at ({round(x)}, {round(y)}): dx={dx}, dy={dy}")

    def _on_key_press(self, key):
        """Callback for keyboard events"""
        if not self.is_recording:
            return

        try:
            # Regular character keys
            key_char = key.char
            action = {
                'type': 'key',
                'key': key_char
            }
        except AttributeError:
            # Special keys (enter, shift, etc)
            action = {
                'type': 'key',
                'key': str(key).replace('Key.', '')
            }

        self._record_action(action)
        print(f"Key pressed: {action['key']}")

    def _print_summary(self):
        """Print summary of recorded actions"""
        if not self.actions:
            return

        types = {}
        for action in self.actions:
            action_type = action['type']
            types[action_type] = types.get(action_type, 0) + 1

        print("\nRecording Summary:")
        print(f"  Total actions: {len(self.actions)}")
        for action_type, count in sorted(types.items()):
            print(f"    {action_type}: {count}")

    def save_recording(self, filename):
        """Save the recording to a JSON file"""
        if not self.actions and not self.initial_window_state:
            print("No recording to save!")
            return False

        recording_data = {
            'metadata': {
                'recorded_at': datetime.now().isoformat(),
                'duration': round(time.time() - self.start_time, 3) if self.start_time else 0,
                'action_count': len(self.actions),
                'recording_mode': 'enhanced',
                'options': {
                    'movements': self.record_movements,
                    'keyboard': self.record_keyboard,
                    'sample_rate': self.movement_sample_rate
                }
            },
            'windows': self.initial_window_state or [],
            'actions': self.actions
        }

        try:
            with open(filename, 'w') as f:
                json.dump(recording_data, f, indent=2)
            print(f"Recording saved to {filename}")
            print(f"  File size: {len(json.dumps(recording_data))} bytes")
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

            metadata = recording_data.get('metadata', {})
            print(f"Loaded recording:")
            print(f"  Actions: {len(self.actions)}")
            print(f"  Duration: {metadata.get('duration', 0):.2f}s")
            print(f"  Mode: {metadata.get('recording_mode', 'standard')}")

            return True
        except Exception as e:
            print(f"Error loading recording: {e}")
            return False

    def get_recording_info(self):
        """Get information about the current recording"""
        return {
            'is_recording': self.is_recording,
            'action_count': len(self.actions),
            'window_count': len(self.initial_window_state) if self.initial_window_state else 0,
            'has_movements': any(a['type'] == 'move' for a in self.actions),
            'has_keyboard': any(a['type'] == 'key' for a in self.actions)
        }
