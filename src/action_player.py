"""
Action Player - Plays back recorded actions
"""

import time
import pyautogui
from window_manager import WindowManager

# Try to load calibration (optional)
try:
    from calibrate import load_calibration, apply_calibration
    CALIBRATION_AVAILABLE = True
except:
    CALIBRATION_AVAILABLE = False


class ActionPlayer:
    """Plays back recorded user actions"""

    def __init__(self):
        self.window_manager = WindowManager()
        self.is_playing = False

        # Configure pyautogui
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Small pause between actions

    def play_recording(self, window_state, actions, on_progress=None):
        """
        Play back a recording

        Args:
            window_state: List of window positions to restore
            actions: List of actions to perform
            on_progress: Optional callback function(current, total) for progress updates
        """
        if self.is_playing:
            print("Already playing a recording!")
            return False

        self.is_playing = True
        print("Starting playback...")

        try:
            # Step 1: Restore window positions (if any)
            if window_state:
                print(f"Restoring {len(window_state)} windows...")
                try:
                    self.window_manager.restore_windows(window_state)
                except Exception as e:
                    print(f"Warning: Window restoration failed: {e}")
                    print("Continuing with playback...")

                # Give windows time to settle
                time.sleep(0.5)
            else:
                print("No window state to restore")

            # Step 2: Play back actions
            print(f"Playing back {len(actions)} actions...")
            for i, action in enumerate(actions):
                if not self.is_playing:
                    print("Playback stopped by user")
                    break

                # Wait before performing this action
                wait_time = action.get('wait_before', 0)
                if wait_time > 0:
                    time.sleep(wait_time)

                # Perform the action
                if action['type'] == 'click':
                    x = action['x']
                    y = action['y']
                    button = action.get('button', 'Button.left')

                    # Apply calibration if available
                    if CALIBRATION_AVAILABLE:
                        x, y = apply_calibration(x, y)
                        print(f"[{i+1}/{len(actions)}] Clicking at ({x}, {y}) [calibrated]")
                    else:
                        print(f"[{i+1}/{len(actions)}] Clicking at ({x}, {y})")

                    # Move mouse to position first (acts as visual indicator)
                    pyautogui.moveTo(x, y, duration=0.3)

                    # Small pause so you can see where it will click
                    time.sleep(0.2)

                    # Determine which button to click
                    if 'right' in button.lower():
                        pyautogui.click(x, y, button='right')
                    elif 'middle' in button.lower():
                        pyautogui.click(x, y, button='middle')
                    else:
                        pyautogui.click(x, y, button='left')

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

    def stop_playback(self):
        """Stop the current playback"""
        if self.is_playing:
            print("Stopping playback...")
            self.is_playing = False
            return True
        return False

    def preview_recording(self, window_state, actions):
        """
        Preview recording information without playing it

        Returns:
            Dictionary with preview information
        """
        total_wait_time = sum(action.get('wait_before', 0) for action in actions)

        preview = {
            'window_count': len(window_state),
            'action_count': len(actions),
            'total_duration': round(total_wait_time, 2),
            'actions_summary': []
        }

        for i, action in enumerate(actions[:10]):  # Show first 10 actions
            preview['actions_summary'].append({
                'step': i + 1,
                'type': action['type'],
                'location': f"({action['x']}, {action['y']})",
                'wait': f"{action.get('wait_before', 0):.2f}s"
            })

        if len(actions) > 10:
            preview['actions_summary'].append({
                'step': '...',
                'type': f'and {len(actions) - 10} more actions',
                'location': '',
                'wait': ''
            })

        return preview
