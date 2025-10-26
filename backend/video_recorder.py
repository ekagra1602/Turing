"""
Video-Based Workflow Recorder
Records full screen video + timestamped events for post-processing
"""

import time
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import pyautogui


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
        
        # Subprocess for video recording (avoids tkinter conflicts)
        self.recording_process = None
        
        print("✅ Video Recorder initialized")
        print(f"   - FPS: {fps}")
        print(f"   - Output dir: {output_dir}")
    
    def start_recording(self, recording_name: str, description: str = "") -> str:
        """
        Start recording screen video and events using subprocess (avoids tkinter conflicts).
        
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
        
        # Get screen size
        screen_width, screen_height = pyautogui.size()
        video_path = recording_path / "screen_recording.mp4"
        
        # Start subprocess for video recording (completely separate from tkinter)
        subprocess_script = Path(__file__).parent / "video_recorder_subprocess.py"
        
        self.recording_process = subprocess.Popen(
            [
                'python',
                str(subprocess_script),
                self.recording_id,
                str(self.output_dir),
                str(self.fps)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        self.start_time = time.time()
        self.is_recording = True
        
        print(f"\n✅ Recording started: {recording_name}")
        print(f"   ID: {self.recording_id}")
        print(f"   Resolution: {screen_width}x{screen_height}")
        print(f"   Video: {video_path}")
        print(f"   Process PID: {self.recording_process.pid}")
        
        return self.recording_id
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording by signaling subprocess and waiting for completion.
        
        Returns:
            recording_id: ID of completed recording
        """
        if not self.is_recording:
            print("⚠️  Not currently recording")
            return None
        
        print("\n🛑 Stopping recording...")
        
        self.is_recording = False
        
        # Signal subprocess to stop by creating stop signal file
        recording_path = self.output_dir / self.recording_id
        stop_signal = recording_path / "STOP_SIGNAL"
        stop_signal.touch()
        
        # Wait for subprocess to finish
        if self.recording_process:
            print("   Waiting for video recording to finish...")
            try:
                # Wait up to 10 seconds for graceful shutdown
                stdout, _ = self.recording_process.communicate(timeout=10)
                print(f"   Subprocess exited with code: {self.recording_process.returncode}")
                
                # Print subprocess output for debugging
                if stdout:
                    print("\n   📹 Subprocess output:")
                    for line in stdout.strip().split('\n'):
                        print(f"      {line}")
                    print()
            except subprocess.TimeoutExpired:
                print("   ⚠️  Subprocess didn't finish, terminating...")
                self.recording_process.terminate()
                try:
                    stdout, _ = self.recording_process.communicate(timeout=2)
                    if stdout:
                        print("\n   📹 Subprocess output:")
                        for line in stdout.strip().split('\n'):
                            print(f"      {line}")
                except:
                    pass
        
        # Clean up stop signal
        if stop_signal.exists():
            stop_signal.unlink()
        
        # Load events from subprocess output
        events_path = recording_path / "events.json"
        if events_path.exists():
            with open(events_path, 'r') as f:
                events_data = json.load(f)
        else:
            print("   ⚠️  No events file found")
            events_data = {
                'recording_id': self.recording_id,
                'duration': time.time() - self.start_time,
                'events': []
            }
        
        # Update metadata
        metadata_path = recording_path / "metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        metadata['status'] = 'recorded'
        metadata['duration'] = events_data.get('duration', 0)
        metadata['event_count'] = len(events_data.get('events', []))
        metadata['completed'] = datetime.now().isoformat()
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Recording stopped")
        print(f"   Duration: {events_data.get('duration', 0):.1f}s")
        print(f"   Events captured: {len(events_data.get('events', []))}")
        print(f"   Saved to: {recording_path}")
        
        recording_id = self.recording_id
        self.recording_id = None
        self.start_time = None
        self.recording_process = None
        
        return recording_id
    
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

