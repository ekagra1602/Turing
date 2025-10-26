#!/usr/bin/env python3
"""
Simple Coordinate & Keystroke Recorder
Records exact mouse clicks and keyboard input for reliable playback
"""

import json
import time
import pyautogui
from pynput import mouse, keyboard
from datetime import datetime
from typing import List, Dict, Any
import os


class SimpleRecorder:
    """Records exact coordinates and keystrokes"""
    
    def __init__(self):
        self.recording = True  # Start recording immediately
        self.actions: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self.last_action_time = time.time()
        
        # Track last 4 characters to detect "stop"
        self.recent_chars = []
        
        # Listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        
        print("=" * 70)
        print("🎬 SIMPLE COORDINATE RECORDER")
        print("=" * 70)
        print()
        print("This tool records EXACT coordinates and keystrokes")
        print("for reliable workflow playback.")
        print()
        print("🔴 RECORDING STARTED!")
        print()
        print("Controls:")
        print("  - Type 'stop' (lowercase) to STOP and save")
        print("  - Press ESC to quit without saving")
        print()
        print("What gets recorded:")
        print("  ✓ Mouse clicks (exact pixel coordinates)")
        print("  ✓ Keyboard typing")
        print("  ✓ Keyboard shortcuts (Cmd+T, Cmd+L, etc.)")
        print("  ✓ Timing between actions")
        print()
        print("=" * 70)
        print()
        print("Perform your workflow now...")
        print("Type 'stop' when finished")
        print()
    
    def on_click(self, x, y, button, pressed):
        """Record mouse clicks"""
        if not self.recording:
            return
        
        if pressed and button == mouse.Button.left:
            timestamp = time.time()
            delay = timestamp - self.last_action_time if self.last_action_time else 0
            
            action = {
                "type": "click",
                "x": x,
                "y": y,
                "delay": round(delay, 2),
                "timestamp": timestamp
            }
            
            self.actions.append(action)
            self.last_action_time = timestamp
            
            print(f"  🖱️  Click recorded: ({x}, {y}) [delay: {delay:.2f}s]")
    
    def on_press(self, key):
        """Record keyboard presses"""
        # Check for ESC to quit
        try:
            if key == keyboard.Key.esc:
                print("\n👋 Exiting without saving...")
                return False
        except:
            pass
        
        if not self.recording:
            return
        
        timestamp = time.time()
        delay = timestamp - self.last_action_time if self.last_action_time else 0
        
        try:
            # Check for special keys
            if key == keyboard.Key.enter:
                action = {
                    "type": "key",
                    "key": "enter",
                    "delay": round(delay, 2),
                    "timestamp": timestamp
                }
                self.actions.append(action)
                self.last_action_time = timestamp
                print(f"  ⏎  Enter key recorded [delay: {delay:.2f}s]")
            elif key == keyboard.Key.tab:
                action = {
                    "type": "key",
                    "key": "tab",
                    "delay": round(delay, 2),
                    "timestamp": timestamp
                }
                self.actions.append(action)
                self.last_action_time = timestamp
                print(f"  ⇥  Tab key recorded [delay: {delay:.2f}s]")
            elif key == keyboard.Key.space:
                action = {
                    "type": "key",
                    "key": "space",
                    "delay": round(delay, 2),
                    "timestamp": timestamp
                }
                self.actions.append(action)
                self.last_action_time = timestamp
                print(f"  ␣  Space key recorded [delay: {delay:.2f}s]")
            elif hasattr(key, 'char') and key.char:
                # Regular character
                action = {
                    "type": "type",
                    "text": key.char,
                    "delay": round(delay, 2),
                    "timestamp": timestamp
                }
                self.actions.append(action)
                self.last_action_time = timestamp
                print(f"  ⌨️  Typed: '{key.char}' [delay: {delay:.2f}s]")
                
                # Track recent characters to detect "stop"
                self.recent_chars.append(key.char)
                if len(self.recent_chars) > 4:
                    self.recent_chars.pop(0)
                
                # Check if last 4 characters spell "stop"
                if ''.join(self.recent_chars) == 'stop':
                    print("\n⏹️  Detected 'stop' command - stopping recording...")
                    # Remove the last 4 actions (the "stop" typing)
                    self.actions = self.actions[:-4]
                    self.stop_recording()
                    return False  # Stop the listener
        except AttributeError:
            # Handle special keys we don't care about
            pass
    
    
    def stop_recording(self):
        """Stop recording and save"""
        if not self.recording:
            print("⚠️  Not recording!")
            return
        
        self.recording = False
        duration = time.time() - self.start_time
        
        print()
        print("=" * 70)
        print("⏹️  RECORDING STOPPED")
        print("=" * 70)
        print(f"Duration: {duration:.1f}s")
        print(f"Actions recorded: {len(self.actions)}")
        print()
        
        # Ask for workflow details
        print("Enter workflow details:")
        name = input("Workflow name (e.g., 'send gmail email'): ").strip()
        if not name:
            name = f"workflow_{int(time.time())}"
        
        description = input("Description (optional): ").strip()
        
        # Save workflow
        workflow = {
            "name": name,
            "description": description,
            "recorded_at": datetime.now().isoformat(),
            "duration": round(duration, 2),
            "actions": self.actions,
            "screen_resolution": {
                "width": pyautogui.size().width,
                "height": pyautogui.size().height
            }
        }
        
        # Save to file
        filename = f"recorded_workflow_{name.replace(' ', '_')}_{int(time.time())}.json"
        filepath = os.path.join(os.path.dirname(__file__), "workflows", filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        print(f"✅ Workflow saved: {filepath}")
        print()
        print("To replay this workflow, run:")
        print(f"  python simple_player.py {filepath}")
        print()
    
    def run(self):
        """Run the recorder"""
        # Start listeners
        with mouse.Listener(on_click=self.on_click) as mouse_listener, \
             keyboard.Listener(on_press=self.on_press) as keyboard_listener:
            
            self.mouse_listener = mouse_listener
            self.keyboard_listener = keyboard_listener
            
            # Keep running until "stop" is typed or ESC is pressed
            keyboard_listener.join()


def main():
    """Main entry point"""
    recorder = SimpleRecorder()
    try:
        recorder.run()
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

