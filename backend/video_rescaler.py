"""
Video Rescaler - Fixes timing sync issues
Re-encodes video to match actual recorded duration
"""

import cv2
import json
from pathlib import Path
from typing import Optional


def rescale_video_to_duration(recording_path: Path, show_progress: bool = True) -> bool:
    """
    Rescale video to match actual recording duration from events.json
    
    This solves the core sync issue:
    - Events are timestamped with real wall-clock time
    - Video may have been captured at different effective FPS
    - We re-encode the video to match the actual duration
    
    Args:
        recording_path: Path to recording directory
        show_progress: Print progress messages
        
    Returns:
        True if successful, False otherwise
    """
    if show_progress:
        print(f"\n🎬 Rescaling video to match recording duration...")
    
    # Load events to get actual duration
    events_path = recording_path / "events.json"
    if not events_path.exists():
        print(f"   ❌ No events.json found")
        return False
    
    with open(events_path, 'r') as f:
        events_data = json.load(f)
    
    actual_duration = events_data.get('duration', 0)
    if actual_duration <= 0:
        print(f"   ❌ Invalid duration: {actual_duration}")
        return False
    
    # Load original video
    video_path = recording_path / "screen_recording.mp4"
    if not video_path.exists():
        print(f"   ❌ No video file found")
        return False
    
    video = cv2.VideoCapture(str(video_path))
    if not video.isOpened():
        print(f"   ❌ Could not open video")
        return False
    
    # Get video properties
    original_fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    original_duration = total_frames / original_fps if original_fps > 0 else 0
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if show_progress:
        print(f"   Original video:")
        print(f"   - Duration: {original_duration:.2f}s")
        print(f"   - Frames: {total_frames}")
        print(f"   - FPS: {original_fps:.2f}")
        print(f"   - Resolution: {width}x{height}")
        print(f"   ")
        print(f"   Actual recording duration: {actual_duration:.2f}s")
        print(f"   Speed ratio: {actual_duration / original_duration:.2f}x")
    
    # Check if rescaling is needed
    duration_diff = abs(actual_duration - original_duration)
    if duration_diff < 0.5:  # Less than 0.5 second difference
        if show_progress:
            print(f"   ✅ Video duration is already correct (diff: {duration_diff:.2f}s)")
        video.release()
        return True
    
    # Calculate new FPS to match actual duration
    # We keep the same number of frames but change the FPS
    new_fps = total_frames / actual_duration
    
    if show_progress:
        print(f"   ")
        print(f"   🔄 Re-encoding video...")
        print(f"   - Target duration: {actual_duration:.2f}s")
        print(f"   - New FPS: {new_fps:.2f}")
    
    # Create temporary output path
    temp_path = recording_path / "screen_recording_rescaled.mp4"
    
    # Initialize video writer with new FPS
    # Try multiple codecs for compatibility
    writer = None
    for codec in ['avc1', 'mp4v', 'MJPG']:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(
            str(temp_path),
            fourcc,
            new_fps,  # This is the key - new FPS to match actual duration
            (width, height)
        )
        
        if writer.isOpened():
            if show_progress:
                print(f"   Using codec: {codec}")
            break
        writer.release()
    
    if not writer or not writer.isOpened():
        print(f"   ❌ Could not create output video with any codec")
        video.release()
        return False
    
    # Copy all frames (same frames, but with different FPS metadata)
    frame_count = 0
    while True:
        ret, frame = video.read()
        if not ret:
            break
        
        writer.write(frame)
        frame_count += 1
        
        if show_progress and frame_count % 100 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"   Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
    
    # Cleanup
    video.release()
    writer.release()
    
    if show_progress:
        print(f"   ✅ Re-encoded {frame_count} frames")
    
    # Verify the new video
    verify_video = cv2.VideoCapture(str(temp_path))
    if verify_video.isOpened():
        verify_fps = verify_video.get(cv2.CAP_PROP_FPS)
        verify_frames = int(verify_video.get(cv2.CAP_PROP_FRAME_COUNT))
        verify_duration = verify_frames / verify_fps if verify_fps > 0 else 0
        verify_video.release()
        
        if show_progress:
            print(f"   ")
            print(f"   Verification:")
            print(f"   - New duration: {verify_duration:.2f}s")
            print(f"   - New FPS: {verify_fps:.2f}")
            print(f"   - Frames: {verify_frames}")
            print(f"   - Duration match: {abs(verify_duration - actual_duration):.3f}s difference")
        
        # Replace original with rescaled version
        backup_path = recording_path / "screen_recording_original.mp4"
        video_path.rename(backup_path)
        temp_path.rename(video_path)
        
        if show_progress:
            print(f"   ")
            print(f"   ✅ Video rescaled successfully!")
            print(f"   - Original backed up to: screen_recording_original.mp4")
            print(f"   - New video duration: {verify_duration:.2f}s")
        
        return True
    else:
        print(f"   ❌ Failed to verify rescaled video")
        if temp_path.exists():
            temp_path.unlink()
        return False


def rescale_recording(recording_id: str, recordings_dir: Optional[Path] = None) -> bool:
    """
    Rescale a specific recording by ID
    
    Args:
        recording_id: Recording ID (e.g., "20251025_184554")
        recordings_dir: Path to recordings directory (default: backend/recordings)
        
    Returns:
        True if successful
    """
    if recordings_dir is None:
        recordings_dir = Path(__file__).parent / "recordings"
    
    recording_path = recordings_dir / recording_id
    
    if not recording_path.exists():
        print(f"❌ Recording {recording_id} not found")
        return False
    
    return rescale_video_to_duration(recording_path)


def rescale_all_recordings(recordings_dir: Optional[Path] = None) -> int:
    """
    Rescale all recordings in the recordings directory
    
    Returns:
        Number of successfully rescaled recordings
    """
    if recordings_dir is None:
        recordings_dir = Path(__file__).parent / "recordings"
    
    if not recordings_dir.exists():
        print(f"❌ Recordings directory not found: {recordings_dir}")
        return 0
    
    recordings = [d for d in recordings_dir.iterdir() if d.is_dir()]
    
    print(f"📹 Found {len(recordings)} recordings")
    print("=" * 70)
    
    success_count = 0
    for i, recording_path in enumerate(recordings, 1):
        print(f"\n[{i}/{len(recordings)}] Processing: {recording_path.name}")
        
        if rescale_video_to_duration(recording_path, show_progress=True):
            success_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ Successfully rescaled {success_count}/{len(recordings)} recordings")
    
    return success_count


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Rescale specific recording
        recording_id = sys.argv[1]
        rescale_recording(recording_id)
    else:
        # Rescale all recordings
        print("=" * 70)
        print("Video Rescaler - Fix Timing Sync Issues")
        print("=" * 70)
        print()
        rescale_all_recordings()

