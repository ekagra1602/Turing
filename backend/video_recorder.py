#!/usr/bin/env python3
"""
Robust Screen Video Recorder using ffmpeg native screen capture
Uses avfoundation on macOS for smooth, stable recording
"""

import subprocess
import time
import signal
from pathlib import Path
from typing import Optional
from datetime import datetime


class VideoRecorder:
    """
    Screen video recorder using ffmpeg's native screen capture.

    Why native capture instead of piping:
    - No Python frame loop timing issues
    - No color conversion overhead
    - ffmpeg handles frame timing internally
    - Much smoother and more stable
    """

    def __init__(self, fps: int = 30, output_dir: Path = None):
        """
        Initialize video recorder

        Args:
            fps: Frames per second (30 is required by avfoundation on macOS)
            output_dir: Directory to save recordings
        """
        self.fps = fps
        self.output_dir = output_dir or Path(__file__).parent / "recordings"
        self.output_dir.mkdir(exist_ok=True)

        self.is_recording = False
        self.ffmpeg_process = None
        self.current_video_path = None
        self.start_time = None

        # Get screen device index
        self.screen_device = self._get_screen_device()

        print(f"✅ Video Recorder initialized (ffmpeg native capture)")
        print(f"   Screen device: {self.screen_device}")
        print(f"   FPS: {fps}")

    def _get_screen_device(self) -> str:
        """Get the screen capture device index for avfoundation"""
        try:
            # List available devices
            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                capture_output=True,
                text=True,
                timeout=3
            )

            # Parse stderr output to find screen capture device
            stderr = result.stderr
            for line in stderr.split('\n'):
                # Look for line like "[3] Capture screen 0"
                if 'Capture screen' in line:
                    # Extract device index - pattern is "[N] Capture screen X"
                    if '[' in line and ']' in line:
                        start = line.find('[')
                        end = line.find(']')
                        if start != -1 and end != -1:
                            device_idx = line[start+1:end].strip()
                            # Make sure it's actually a number
                            if device_idx.isdigit():
                                print(f"   Found screen capture device: {device_idx}")
                                return device_idx

            # Default to device 3 (common for screen capture)
            print("   Using default screen device: 3")
            return "3"

        except Exception as e:
            print(f"⚠️  Could not detect screen device, using default: {e}")
            return "3"

    def start_recording(self, workflow_name: str) -> Optional[Path]:
        """
        Start recording screen to video

        Args:
            workflow_name: Name for this recording

        Returns:
            Path to video file (or None if already recording)
        """
        if self.is_recording:
            print("⚠️  Already recording!")
            return None

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in workflow_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{timestamp}_{safe_name}.mp4"
        self.current_video_path = self.output_dir / filename

        # Start ffmpeg with native screen capture
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'avfoundation',          # macOS screen capture
            '-framerate', str(self.fps),    # Input framerate (must be 30 or 60)
            '-i', self.screen_device,       # Screen device index
            '-vcodec', 'libx264',           # H.264 encoding
            '-preset', 'ultrafast',         # Fast encoding for real-time
            '-crf', '23',                   # Good quality (18-28 range, lower=better)
            '-pix_fmt', 'yuv420p',          # Standard compatibility
            '-movflags', '+faststart',      # Enable streaming
            '-y',                           # Overwrite
            str(self.current_video_path)
        ]

        try:
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,  # Capture errors
                text=True
            )
        except FileNotFoundError:
            print("❌ ffmpeg not found! Please install:")
            print("   brew install ffmpeg")
            return None
        except Exception as e:
            print(f"❌ Failed to start ffmpeg: {e}")
            return None

        # Give ffmpeg a moment to start
        time.sleep(0.5)

        # Check if process is still running (not immediately crashed)
        if self.ffmpeg_process.poll() is not None:
            stderr = self.ffmpeg_process.stderr.read() if self.ffmpeg_process.stderr else ""
            print(f"❌ ffmpeg failed to start properly")
            if stderr:
                print(f"   Error: {stderr[:500]}")
            return None

        # Start recording
        self.is_recording = True
        self.start_time = time.time()

        print(f"🎥 Recording started: {filename}")
        print(f"   ✓ Using ffmpeg native screen capture (avfoundation)")
        return self.current_video_path

    def stop_recording(self) -> Optional[Path]:
        """
        Stop recording and save video

        Returns:
            Path to saved video file
        """
        if not self.is_recording:
            print("⚠️  Not currently recording!")
            return None

        # Stop recording
        self.is_recording = False

        # Send graceful stop signal to ffmpeg (q key)
        if self.ffmpeg_process:
            try:
                # Send SIGINT (Ctrl+C) for graceful shutdown
                self.ffmpeg_process.send_signal(signal.SIGINT)

                # Wait for ffmpeg to finish encoding
                self.ffmpeg_process.wait(timeout=10.0)

            except subprocess.TimeoutExpired:
                print("⚠️  ffmpeg took too long, force killing")
                self.ffmpeg_process.kill()
            except Exception as e:
                print(f"⚠️  Error stopping ffmpeg: {e}")
                try:
                    self.ffmpeg_process.kill()
                except:
                    pass

        duration = time.time() - self.start_time

        print(f"⏹️  Recording stopped")
        print(f"   Duration: {duration:.1f}s")
        print(f"   File: {self.current_video_path}")

        # Verify file was created
        if self.current_video_path.exists():
            file_size = self.current_video_path.stat().st_size
            print(f"   Size: {file_size / (1024*1024):.1f} MB")

            if file_size < 1000:
                print("   ⚠️  WARNING: File is suspiciously small!")
        else:
            print("   ❌ Video file was not created!")

        return self.current_video_path

    def get_recording_info(self) -> dict:
        """Get current recording status and info"""
        if self.is_recording:
            duration = time.time() - self.start_time
            return {
                'is_recording': True,
                'duration': duration,
                'fps': self.fps,
                'file': str(self.current_video_path)
            }
        else:
            return {
                'is_recording': False
            }

    def __del__(self):
        """Cleanup on deletion"""
        if self.is_recording:
            self.stop_recording()


def test_video_recorder():
    """Test the video recorder"""
    print("=" * 70)
    print("Video Recorder Test (ffmpeg native screen capture)")
    print("=" * 70)
    print()

    # Check ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=2)
        print("✅ ffmpeg found")
        print()
    except FileNotFoundError:
        print("❌ ffmpeg not found!")
        print("   Install with: brew install ffmpeg")
        print()
        return

    recorder = VideoRecorder(fps=30)

    print("Starting 5-second test recording...")
    print("Move your mouse and click around!")
    print()

    video_path = recorder.start_recording("test_workflow")

    if not video_path:
        print("❌ Failed to start recording")
        return

    # Record for 5 seconds
    for i in range(5, 0, -1):
        print(f"Recording... {i}s remaining")
        time.sleep(1)

    # Stop recording
    final_path = recorder.stop_recording()

    print()
    print("=" * 70)
    print("✅ Test complete!")

    if final_path and final_path.exists():
        print(f"Video saved to: {final_path}")
        print()
        print("Verify with:")
        print(f"  ffprobe {final_path}")
        print(f"  open {final_path}")
    else:
        print("❌ Video file not created!")

    print("=" * 70)


if __name__ == "__main__":
    test_video_recorder()
