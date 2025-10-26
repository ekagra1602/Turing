"""
Video Recording Subprocess
Runs independently from tkinter to avoid threading conflicts on macOS
"""

import cv2
import time
import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
from pynput import mouse, keyboard

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    import pyautogui


class VideoRecorderProcess:
    """Standalone video recorder that runs in its own process"""
    
    def __init__(self, recording_id: str, output_dir: str, fps: int = 30):
        self.recording_id = recording_id
        self.output_dir = Path(output_dir)
        self.fps = fps
        self.frame_interval = 1.0 / fps
        
        self.is_recording = True
        self.start_time = time.time()
        self.events = []
        
        # Setup video writer
        video_path = self.output_dir / self.recording_id / "screen_recording.mp4"
        
        # Get ACTUAL screen size by taking a test screenshot
        # This is critical for Retina displays where logical size != physical size
        print(f"   Detecting screen resolution...")
        if HAS_MSS:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                test_shot = sct.grab(monitor)
                test_frame = np.array(test_shot)
                screen_height, screen_width = test_frame.shape[:2]
                print(f"   Detected via MSS: {screen_width}x{screen_height}")
        else:
            test_shot = pyautogui.screenshot()
            test_frame = np.array(test_shot)
            screen_height, screen_width = test_frame.shape[:2]
            print(f"   Detected via pyautogui: {screen_width}x{screen_height}")
        
        # Try different codecs for better compatibility
        # avc1 (H.264) is more compatible but may not be available
        # Try in order: avc1, MJPG, mp4v
        video_writer = None
        for codec in ['avc1', 'MJPG', 'mp4v']:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            video_writer = cv2.VideoWriter(
                str(video_path),
                fourcc,
                fps,
                (screen_width, screen_height)
            )
            if video_writer.isOpened():
                print(f"   Using codec: {codec}")
                break
            video_writer.release()
        
        if not video_writer or not video_writer.isOpened():
            raise RuntimeError("Failed to initialize video writer with any codec")
        
        self.video_writer = video_writer
        
        print(f"📹 Subprocess started: {recording_id}")
        print(f"   Resolution: {screen_width}x{screen_height}")
        print(f"   Video: {video_path}")
        
        # Start listeners
        print(f"🎯 Starting event listeners...")
        try:
            self.mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            
            self.mouse_listener.start()
            self.keyboard_listener.start()
            
            # Give listeners a moment to start
            time.sleep(0.1)
            
            if self.mouse_listener.running and self.keyboard_listener.running:
                print(f"✅ Event listeners started successfully")
            else:
                print(f"⚠️  WARNING: Event listeners may not have started")
                print(f"   Mouse listener: {'running' if self.mouse_listener.running else 'NOT running'}")
                print(f"   Keyboard listener: {'running' if self.keyboard_listener.running else 'NOT running'}")
                print(f"")
                print(f"⚠️  macOS PERMISSION REQUIRED:")
                print(f"   Go to: System Settings > Privacy & Security > Accessibility")
                print(f"   Add and enable: Terminal (or your terminal app)")
                print(f"")
        except Exception as e:
            print(f"❌ Failed to start event listeners: {e}")
            print(f"   Video recording will continue but events won't be captured")
    
    def _on_mouse_click(self, x, y, button, pressed):
        try:
            if pressed:
                event = {
                    'timestamp': time.time() - self.start_time,
                    'event_type': 'click',
                    'data': {'x': x, 'y': y, 'button': str(button)}
                }
                self.events.append(event)
                print(f"   🖱️  Click at ({x}, {y}) [{len(self.events)} events]")
        except Exception as e:
            print(f"   ⚠️  Mouse event error: {e}")
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        self.events.append({
            'timestamp': time.time() - self.start_time,
            'event_type': 'scroll',
            'data': {'x': x, 'y': y, 'dx': dx, 'dy': dy}
        })
    
    def _on_key_press(self, key):
        try:
            try:
                key_str = key.char if hasattr(key, 'char') else str(key)
            except:
                key_str = str(key)
            
            event = {
                'timestamp': time.time() - self.start_time,
                'event_type': 'key_press',
                'data': {'key': key_str}
            }
            self.events.append(event)
            print(f"   ⌨️  Key: {key_str} [{len(self.events)} events]")
        except Exception as e:
            print(f"   ⚠️  Keyboard event error: {e}")
    
    def _on_key_release(self, key):
        pass
    
    def record_loop(self):
        """Main recording loop"""
        frame_count = 0
        last_frame_time = time.time()
        
        # Check for stop signal file
        stop_signal = self.output_dir / self.recording_id / "STOP_SIGNAL"
        
        while self.is_recording:
            # Check for stop signal
            if stop_signal.exists():
                print("🛑 Stop signal received")
                break
            
            current_time = time.time()
            
            # Maintain FPS
            if current_time - last_frame_time < self.frame_interval:
                time.sleep(0.001)
                continue
            
            last_frame_time = current_time
            
            # Capture frame
            try:
                if HAS_MSS:
                    with mss.mss() as sct:
                        monitor = sct.monitors[1]
                        screenshot = sct.grab(monitor)
                        frame = np.array(screenshot)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                else:
                    screenshot = pyautogui.screenshot()
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Verify frame properties
                if frame_count == 0:
                    print(f"   Frame info: shape={frame.shape}, dtype={frame.dtype}")
                    if not self.video_writer.isOpened():
                        print(f"   ⚠️  WARNING: VideoWriter is not opened!")
                
                # Write frame
                success = self.video_writer.write(frame)
                if success is not None and not success:
                    print(f"   ⚠️  WARNING: Frame {frame_count} write returned False")
                
                frame_count += 1
                
                # Progress indicator every 100 frames
                if frame_count % 100 == 0:
                    elapsed = time.time() - self.start_time
                    print(f"   Recording: {elapsed:.1f}s ({frame_count} frames)")
                
            except Exception as e:
                print(f"⚠️  Frame capture error: {e}")
                import traceback
                traceback.print_exc()
        
        # Cleanup
        print(f"   Finalizing video...")
        self.video_writer.release()
        print(f"   Video writer released")
        
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        
        # Check video file size
        video_path = self.output_dir / self.recording_id / "screen_recording.mp4"
        if video_path.exists():
            file_size = video_path.stat().st_size
            print(f"   Video file size: {file_size} bytes")
            if file_size < 1000:
                print(f"   ⚠️  WARNING: Video file suspiciously small!")
        
        # Save events
        events_path = self.output_dir / self.recording_id / "events.json"
        with open(events_path, 'w') as f:
            json.dump({
                'recording_id': self.recording_id,
                'duration': time.time() - self.start_time,
                'event_count': len(self.events),
                'events': self.events,
                'fps': self.fps
            }, f, indent=2)
        
        print(f"✅ Recording complete: {frame_count} frames, {len(self.events)} events")


if __name__ == '__main__':
    # Usage: python video_recorder_subprocess.py <recording_id> <output_dir> <fps>
    if len(sys.argv) < 3:
        print("Usage: python video_recorder_subprocess.py <recording_id> <output_dir> [fps]")
        sys.exit(1)
    
    recording_id = sys.argv[1]
    output_dir = sys.argv[2]
    fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    recorder = VideoRecorderProcess(recording_id, output_dir, fps)
    recorder.record_loop()

