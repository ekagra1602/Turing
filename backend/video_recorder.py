#!/usr/bin/env python3
"""
Video-Based Screen Recorder
Records screen activity as video for VLM analysis
"""

import cv2
import numpy as np
import mss
import time
import threading
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime


class VideoRecorder:
    """
    Records screen activity as video for later VLM analysis.

    Much simpler than screenshot-based approach:
    - Records entire screen as MP4
    - Let Gemini watch the video and understand the workflow
    - No complex event tracking needed
    """

    def __init__(self, fps: int = 10, output_dir: Path = None):
        """
        Initialize video recorder

        Args:
            fps: Frames per second (10 is plenty for UI interactions)
            output_dir: Directory to save recordings
        """
        self.fps = fps
        self.output_dir = output_dir or Path(__file__).parent / "recordings"
        self.output_dir.mkdir(exist_ok=True)

        self.is_recording = False
        self.recording_thread = None
        self.current_video_path = None
        self.start_time = None
        self.frame_count = 0

        # Video writer
        self.video_writer = None
        self.sct = mss.mss()

        # Get screen dimensions
        monitor = self.sct.monitors[1]  # Primary monitor
        self.screen_width = monitor["width"]
        self.screen_height = monitor["height"]

        print(f"✅ Video Recorder initialized")
        print(f"   Resolution: {self.screen_width}x{self.screen_height}")
        print(f"   FPS: {fps}")

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

        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            str(self.current_video_path),
            fourcc,
            self.fps,
            (self.screen_width, self.screen_height)
        )

        if not self.video_writer.isOpened():
            print("❌ Failed to initialize video writer!")
            return None

        # Start recording
        self.is_recording = True
        self.start_time = time.time()
        self.frame_count = 0

        # Start recording thread
        self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.recording_thread.start()

        print(f"🎥 Recording started: {filename}")
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

        # Wait for thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)

        # Release video writer
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        duration = time.time() - self.start_time

        print(f"⏹️  Recording stopped")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Frames: {self.frame_count}")
        print(f"   File: {self.current_video_path}")

        return self.current_video_path

    def _record_loop(self):
        """Main recording loop (runs in separate thread)"""
        monitor = self.sct.monitors[1]  # Primary monitor

        frame_delay = 1.0 / self.fps
        next_frame_time = time.time()

        while self.is_recording:
            try:
                # Capture screen
                screenshot = self.sct.grab(monitor)

                # Convert to numpy array
                frame = np.array(screenshot)

                # Convert BGRA to BGR (OpenCV format)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # Write frame
                self.video_writer.write(frame)
                self.frame_count += 1

                # Maintain consistent frame rate
                next_frame_time += frame_delay
                sleep_time = next_frame_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    # We're behind, skip sleep but update next_frame_time
                    next_frame_time = time.time()

            except Exception as e:
                print(f"⚠️  Recording error: {e}")
                break

    def get_recording_info(self) -> dict:
        """Get current recording status and info"""
        if self.is_recording:
            duration = time.time() - self.start_time
            return {
                'is_recording': True,
                'duration': duration,
                'frames': self.frame_count,
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

        if hasattr(self, 'sct'):
            self.sct.close()


def test_video_recorder():
    """Test the video recorder"""
    print("=" * 70)
    print("Video Recorder Test")
    print("=" * 70)
    print()

    recorder = VideoRecorder(fps=10)

    print("Starting 5-second test recording...")
    print("Move your mouse and click around!")
    print()

    video_path = recorder.start_recording("test_workflow")

    # Record for 5 seconds
    for i in range(5, 0, -1):
        print(f"Recording... {i}s remaining")
        time.sleep(1)

    # Stop recording
    final_path = recorder.stop_recording()

    print()
    print("=" * 70)
    print("✅ Test complete!")
    print(f"Video saved to: {final_path}")
    print()
    print("You can now:")
    print(f"  1. Play the video: open {final_path}")
    print(f"  2. Upload to Gemini for analysis")
    print("=" * 70)


if __name__ == "__main__":
    test_video_recorder()
