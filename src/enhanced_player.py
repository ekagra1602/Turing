"""
Enhanced Action Player - Plays back complete interactions including:
- Mouse movements (smooth cursor path)
- Clicks
- Keyboard input
- Scrolling
- Drags
"""

import time
import pyautogui
from window_manager import WindowManager

# Try to load calibration
try:
    from calibrate import apply_calibration
    CALIBRATION_AVAILABLE = True
except:
    CALIBRATION_AVAILABLE = False


class EnhancedPlayer:
    """Plays back complete user interactions"""

    def __init__(self, instant_click=False):
        self.window_manager = WindowManager()
        self.is_playing = False
        self.instant_click = instant_click  # For click-only actions
        self.smooth_movements = True  # Smooth mouse movement for moves
        self.playback_speed = 1.0  # Speed multiplier

        # Configure pyautogui
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.05  # Small pause between actions

    def play_recording(self, window_state, actions, on_progress=None):
        """
        Play back a recording with full interaction replay

        Args:
            window_state: List of window positions to restore
            actions: List of actions to perform
            on_progress: Optional callback function(current, total)
        """
        if self.is_playing:
            print("Already playing a recording!")
            return False

        self.is_playing = True
        print("Starting enhanced playback...")

        try:
            # Step 1: Restore window positions (if any)
            if window_state:
                print(f"Restoring {len(window_state)} windows...")
                try:
                    self.window_manager.restore_windows(window_state)
                except Exception as e:
                    print(f"Warning: Window restoration failed: {e}")
                    print("Continuing with playback...")
                time.sleep(0.5)
            else:
                print("No window state to restore")

            # Step 2: Play back actions
            print(f"Playing back {len(actions)} actions...")

            for i, action in enumerate(actions):
                if not self.is_playing:
                    print("Playback stopped by user")
                    break

                # Wait before performing this action (scaled by playback speed)
                wait_time = action.get('wait_before', 0) / self.playback_speed
                if wait_time > 0:
                    time.sleep(wait_time)

                # Perform the action based on type
                action_type = action.get('type', 'unknown')

                try:
                    if action_type == 'move':
                        self._play_move(action, i + 1, len(actions))
                    elif action_type == 'click_down':
                        self._play_click_down(action, i + 1, len(actions))
                    elif action_type == 'click_up':
                        self._play_click_up(action, i + 1, len(actions))
                    elif action_type == 'click':
                        self._play_click(action, i + 1, len(actions))
                    elif action_type == 'scroll':
                        self._play_scroll(action, i + 1, len(actions))
                    elif action_type == 'key':
                        self._play_key(action, i + 1, len(actions))
                    else:
                        print(f"[{i+1}/{len(actions)}] Unknown action type: {action_type}")

                except Exception as e:
                    print(f"Error playing action {i+1}: {e}")

                # Update progress callback
                if on_progress:
                    on_progress(i + 1, len(actions))

            print("Playback complete!")
            return True

        except Exception as e:
            print(f"Error during playback: {e}")
            return False

        finally:
            self.is_playing = False

    def _apply_calibration(self, x, y):
        """Apply calibration to coordinates if available"""
        if CALIBRATION_AVAILABLE:
            return apply_calibration(x, y)
        return x, y

    def _play_move(self, action, step, total):
        """Play a mouse movement"""
        x = action['x']
        y = action['y']
        x, y = self._apply_calibration(x, y)

        if self.smooth_movements:
            # Smooth movement
            duration = 0.1 / self.playback_speed
            pyautogui.moveTo(x, y, duration=duration)
        else:
            # Instant move
            pyautogui.moveTo(x, y, duration=0)

    def _play_click(self, action, step, total):
        """Play a simple click (old format)"""
        x = action['x']
        y = action['y']
        x, y = self._apply_calibration(x, y)
        button = action.get('button', 'Button.left')

        print(f"[{step}/{total}] Click at ({x}, {y})")

        if self.instant_click:
            # Instant click
            if 'right' in button.lower():
                pyautogui.click(x, y, button='right')
            elif 'middle' in button.lower():
                pyautogui.click(x, y, button='middle')
            else:
                pyautogui.click(x, y, button='left')
        else:
            # Move then click
            pyautogui.moveTo(x, y, duration=0.3 / self.playback_speed)
            time.sleep(0.1)
            pyautogui.click()

    def _play_click_down(self, action, step, total):
        """Play mouse button press"""
        x = action['x']
        y = action['y']
        x, y = self._apply_calibration(x, y)
        button = action.get('button', 'Button.left')

        # Move to position
        pyautogui.moveTo(x, y, duration=0.05 / self.playback_speed)

        # Press button
        if 'right' in button.lower():
            pyautogui.mouseDown(button='right')
        elif 'middle' in button.lower():
            pyautogui.mouseDown(button='middle')
        else:
            pyautogui.mouseDown(button='left')

    def _play_click_up(self, action, step, total):
        """Play mouse button release"""
        x = action['x']
        y = action['y']
        x, y = self._apply_calibration(x, y)
        button = action.get('button', 'Button.left')

        print(f"[{step}/{total}] Click at ({x}, {y})")

        # Move to position
        pyautogui.moveTo(x, y, duration=0.05 / self.playback_speed)

        # Release button
        if 'right' in button.lower():
            pyautogui.mouseUp(button='right')
        elif 'middle' in button.lower():
            pyautogui.mouseUp(button='middle')
        else:
            pyautogui.mouseUp(button='left')

    def _play_scroll(self, action, step, total):
        """Play scroll action"""
        x = action['x']
        y = action['y']
        x, y = self._apply_calibration(x, y)
        dx = action.get('dx', 0)
        dy = action.get('dy', 0)

        print(f"[{step}/{total}] Scroll at ({x}, {y}): dy={dy}")

        # Move to position first
        pyautogui.moveTo(x, y, duration=0.05 / self.playback_speed)

        # Scroll (dy is usually the vertical scroll amount)
        if dy != 0:
            pyautogui.scroll(int(dy * 10))  # Scale scroll amount

    def _play_key(self, action, step, total):
        """Play keyboard input"""
        key = action.get('key', '')

        print(f"[{step}/{total}] Key: {key}")

        # Handle special keys
        special_keys = {
            'space': ' ',
            'enter': '\n',
            'tab': '\t',
            'backspace': 'backspace',
            'delete': 'delete',
            'shift': 'shift',
            'ctrl': 'ctrl',
            'alt': 'alt',
            'cmd': 'command',
            'esc': 'esc',
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right'
        }

        key_lower = key.lower()
        if key_lower in special_keys:
            pyautogui.press(special_keys[key_lower])
        elif len(key) == 1:
            # Regular character
            pyautogui.write(key, interval=0.01 / self.playback_speed)
        else:
            # Try as a special key name
            try:
                pyautogui.press(key_lower)
            except:
                print(f"Warning: Unknown key '{key}'")

    def stop_playback(self):
        """Stop the current playback"""
        if self.is_playing:
            print("Stopping playback...")
            self.is_playing = False
            return True
        return False

    def set_speed(self, speed):
        """Set playback speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = half speed)"""
        self.playback_speed = max(0.1, min(10.0, speed))
        print(f"Playback speed: {self.playback_speed}x")
