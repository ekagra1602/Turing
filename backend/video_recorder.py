"""
Video-Based Workflow Recorder
Records full screen video + timestamped events for post-processing
"""

import cv2
import time
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict

import numpy as np
from PIL import Image
import pyautogui
from pynput import mouse, keyboard


@dataclass
class ActionEvent:
    """A single user action with precise timestamp"""
    timestamp: float  # Seconds from recording start
    event_type: str  # 'click', 'scroll', 'key_press', 'type'
    data: Dict[str, Any]  # Event-specific data
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'data': self.data
        }


class ScreenVideoRecorder:
    """
    Records screen video at 30 FPS with synchronized event logging.
    
    This is the foundation for robust workflow learning:
    - Continuous video capture (can reprocess with better algorithms)
    - Precise event timestamps (match to video frames)
    - Minimal overhead during recording (processing happens after)
    """
    
    def __init__(self, output_dir: Path = None, fps: int = 30):
        if output_dir is None:
            output_dir = Path(__file__).parent / "recordings"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.fps = fps
        self.frame_interval = 1.0 / fps
        
        # Recording state
        self.is_recording = False
        self.recording_id = None
        self.start_time = None
        
        # Video writer
        self.video_writer = None
        self.video_thread = None
        
        # Event logging
        self.events: List[ActionEvent] = []
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Keyboard text buffer for typing detection
        self.text_buffer = []
        self.last_key_time = 0
        self.typing_timeout = 0.5  # Group keys within 500ms as typing
        
        print("✅ Video Recorder initialized")
        print(f"   - FPS: {fps}")
        print(f"   - Output dir: {output_dir}")
    
    def start_recording(self, recording_name: str, description: str = "") -> str:
        """
        Start recording screen video and events.
        
        Returns:
            recording_id: Unique ID for this recording
        """
        if self.is_recording:
            raise RuntimeError("Already recording!")
        
        # Generate recording ID
        self.recording_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        recording_path = self.output_dir / self.recording_id
        recording_path.mkdir(exist_ok=True)
        
        # Save metadata
        metadata = {
            'recording_id': self.recording_id,
            'name': recording_name,
            'description': description,
            'created': datetime.now().isoformat(),
            'fps': self.fps,
            'status': 'recording'
        }
        
        with open(recording_path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Initialize video writer
        screen_width, screen_height = pyautogui.size()
        video_path = str(recording_path / "screen_recording.mp4")
        
        # Use H.264 codec for good compression
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            video_path,
            fourcc,
            self.fps,
            (screen_width, screen_height)
        )
        
        # Reset state
        self.events = []
        self.text_buffer = []
        self.start_time = time.time()
        self.is_recording = True
        
        # Start video recording thread
        self.video_thread = threading.Thread(target=self._record_video_loop, daemon=True)
        self.video_thread.start()
        
        # Start event listeners
        self._start_event_listeners()
        
        print(f"\n✅ Recording started: {recording_name}")
        print(f"   ID: {self.recording_id}")
        print(f"   Resolution: {screen_width}x{screen_height}")
        print(f"   Video: {video_path}")
        
        return self.recording_id
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and save events log.
        
        Returns:
            recording_id: ID of completed recording
        """
        if not self.is_recording:
            print("⚠️  Not currently recording")
            return None
        
        print("\n🛑 Stopping recording...")
        
        self.is_recording = False
        
        # Stop event listeners
        self._stop_event_listeners()
        
        # Wait for video thread to finish
        if self.video_thread:
            self.video_thread.join(timeout=2.0)
        
        # Release video writer
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        # Save events log
        recording_path = self.output_dir / self.recording_id
        events_path = recording_path / "events.json"
        
        events_data = {
            'recording_id': self.recording_id,
            'duration': time.time() - self.start_time,
            'event_count': len(self.events),
            'events': [event.to_dict() for event in self.events]
        }
        
        with open(events_path, 'w') as f:
            json.dump(events_data, f, indent=2)
        
        # Update metadata
        metadata_path = recording_path / "metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        metadata['status'] = 'recorded'
        metadata['duration'] = events_data['duration']
        metadata['event_count'] = len(self.events)
        metadata['completed'] = datetime.now().isoformat()
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Recording stopped")
        print(f"   Duration: {events_data['duration']:.1f}s")
        print(f"   Events captured: {len(self.events)}")
        print(f"   Saved to: {recording_path}")
        
        recording_id = self.recording_id
        self.recording_id = None
        self.start_time = None
        
        return recording_id
    
    def _record_video_loop(self):
        """Background thread that continuously captures screen frames"""
        last_frame_time = time.time()
        
        while self.is_recording:
            current_time = time.time()
            
            # Maintain target FPS
            if current_time - last_frame_time < self.frame_interval:
                time.sleep(0.001)  # Small sleep to avoid busy waiting
                continue
            
            last_frame_time = current_time
            
            # Capture screen
            try:
                screenshot = pyautogui.screenshot()
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                self.video_writer.write(frame)
            except Exception as e:
                print(f"⚠️  Frame capture error: {e}")
    
    def _start_event_listeners(self):
        """Start pynput listeners for mouse and keyboard"""
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
    
    def _stop_event_listeners(self):
        """Stop all event listeners"""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def _get_timestamp(self) -> float:
        """Get timestamp relative to recording start"""
        return time.time() - self.start_time
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events"""
        if not self.is_recording or not pressed:
            return
        
        timestamp = self._get_timestamp()
        
        event = ActionEvent(
            timestamp=timestamp,
            event_type='click',
            data={
                'x': int(x),
                'y': int(y),
                'button': str(button).replace('Button.', '')
            }
        )
        
        self.events.append(event)
        print(f"  📍 Click at ({x}, {y}) @ {timestamp:.2f}s")
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events"""
        if not self.is_recording:
            return
        
        timestamp = self._get_timestamp()
        
        # Determine direction
        if dy > 0:
            direction = 'up'
        elif dy < 0:
            direction = 'down'
        elif dx > 0:
            direction = 'right'
        else:
            direction = 'left'
        
        event = ActionEvent(
            timestamp=timestamp,
            event_type='scroll',
            data={
                'x': int(x),
                'y': int(y),
                'direction': direction,
                'dx': int(dx),
                'dy': int(dy)
            }
        )
        
        self.events.append(event)
        print(f"  📜 Scroll {direction} @ {timestamp:.2f}s")
    
    def _on_key_press(self, key):
        """Handle keyboard press events"""
        if not self.is_recording:
            return
        
        timestamp = self._get_timestamp()
        
        # Handle special keys
        try:
            key_name = key.char
            is_char = True
        except AttributeError:
            key_name = str(key).replace('Key.', '')
            is_char = False
        
        # Group characters into typing events
        if is_char:
            current_time = time.time()
            
            # Start new typing event or add to existing
            if current_time - self.last_key_time < self.typing_timeout:
                self.text_buffer.append(key_name)
            else:
                # Flush previous typing event if exists
                if self.text_buffer:
                    self._flush_typing_event()
                self.text_buffer = [key_name]
            
            self.last_key_time = current_time
        
        # Special keys (Enter, Tab, etc.) - always create separate events
        elif key_name in ['enter', 'tab', 'esc', 'backspace', 'delete']:
            # Flush any pending typing
            if self.text_buffer:
                self._flush_typing_event()
            
            event = ActionEvent(
                timestamp=timestamp,
                event_type='key_press',
                data={'key': key_name}
            )
            
            self.events.append(event)
            print(f"  ⌨️  Key: {key_name} @ {timestamp:.2f}s")
    
    def _on_key_release(self, key):
        """Handle keyboard release events"""
        pass  # We only track presses
    
    def _flush_typing_event(self):
        """Flush accumulated text buffer as a typing event"""
        if not self.text_buffer:
            return
        
        text = ''.join(self.text_buffer)
        timestamp = self._get_timestamp()
        
        event = ActionEvent(
            timestamp=timestamp,
            event_type='type',
            data={'text': text}
        )
        
        self.events.append(event)
        print(f"  ⌨️  Type: '{text}' @ {timestamp:.2f}s")
        
        self.text_buffer = []
    
    def get_recording_info(self, recording_id: str) -> Dict:
        """Get information about a recording"""
        recording_path = self.output_dir / recording_id
        
        if not recording_path.exists():
            raise ValueError(f"Recording {recording_id} not found")
        
        # Load metadata
        with open(recording_path / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        # Load events
        with open(recording_path / "events.json", 'r') as f:
            events = json.load(f)
        
        return {
            'metadata': metadata,
            'events_count': events['event_count'],
            'duration': events['duration'],
            'video_path': str(recording_path / "screen_recording.mp4"),
            'events_path': str(recording_path / "events.json")
        }


def test_video_recorder():
    """Test the video recorder"""
    print("=" * 70)
    print("Video Recorder Test")
    print("=" * 70)
    print()
    
    recorder = ScreenVideoRecorder()
    
    print("This will record for 10 seconds.")
    print("Perform some actions: click around, type, scroll")
    print()
    
    input("Press Enter to start...")
    
    recording_id = recorder.start_recording(
        recording_name="Test Recording",
        description="Testing video recorder"
    )
    
    print("\n⏺️  RECORDING - perform your actions now!")
    time.sleep(10)
    
    recording_id = recorder.stop_recording()
    
    print("\n" + "=" * 70)
    print("Recording complete!")
    print("=" * 70)
    
    info = recorder.get_recording_info(recording_id)
    print(f"\nRecording info:")
    print(f"  Duration: {info['duration']:.1f}s")
    print(f"  Events: {info['events_count']}")
    print(f"  Video: {info['video_path']}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_video_recorder()

