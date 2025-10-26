"""
Video Rescaler using ffmpeg - Fixes timing sync issues
Re-encodes video to match actual recorded duration using ffmpeg
"""

import json
import subprocess
from pathlib import Path
from typing import Optional


def rescale_video_to_duration(recording_path: Path, show_progress: bool = True) -> bool:
    """
    Rescale video to match actual recording duration from events.json using ffmpeg
    
    This solves the core sync issue:
    - Events are timestamped with real wall-clock time
    - Video may have been captured at different effective FPS
    - We re-encode the video to match the actual duration using ffmpeg
    
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
    
    # Check if video exists
    video_path = recording_path / "screen_recording.mp4"
    if not video_path.exists():
        print(f"   ❌ No video file found")
        return False
    
    # Get current video duration using ffprobe
    try:
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        original_duration = float(result.stdout.strip())
    except Exception as e:
        print(f"   ⚠️  Could not probe video duration: {e}")
        print(f"   Trying alternative method...")
        # Fallback: assume it needs rescaling
        original_duration = 0
    
    if show_progress and original_duration > 0:
        print(f"   Original video duration: {original_duration:.2f}s")
        print(f"   Actual recording duration: {actual_duration:.2f}s")
        print(f"   Speed ratio: {actual_duration / original_duration:.2f}x")
    
    # Check if rescaling is needed
    if original_duration > 0:
        duration_diff = abs(actual_duration - original_duration)
        if duration_diff < 0.5:  # Less than 0.5 second difference
            if show_progress:
                print(f"   ✅ Video duration is already correct (diff: {duration_diff:.2f}s)")
            return True
    
    # Calculate speed filter for ffmpeg
    # If video is 12s but should be 43s, we need to slow it down by 43/12 = 3.58x
    # ffmpeg setpts filter: larger multiplier = slower video
    speed_multiplier = actual_duration / original_duration if original_duration > 0 else 1.0
    
    if show_progress:
        print(f"   ")
        print(f"   🔄 Re-encoding video with ffmpeg...")
        print(f"   - Target duration: {actual_duration:.2f}s")
        print(f"   - Speed multiplier: {speed_multiplier:.3f}x")
    
    # Create temporary output path
    temp_path = recording_path / "screen_recording_rescaled.mp4"
    
    # Use ffmpeg to rescale video
    # setpts filter changes presentation timestamp to slow down/speed up video
    # PTS*multiplier: larger multiplier = slower video
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-vf', f'setpts={speed_multiplier}*PTS',  # Video filter to change speed
        '-an',  # No audio (we don't have audio anyway)
        '-y',   # Overwrite output file
        str(temp_path)
    ]
    
    try:
        if show_progress:
            # Run with output visible
            subprocess.run(ffmpeg_cmd, timeout=300, check=True)
        else:
            # Run silently
            subprocess.run(ffmpeg_cmd, capture_output=True, timeout=300, check=True)
    except subprocess.TimeoutExpired:
        print(f"   ❌ ffmpeg timed out (video too long?)")
        if temp_path.exists():
            temp_path.unlink()
        return False
    except subprocess.CalledProcessError as e:
        print(f"   ❌ ffmpeg failed: {e}")
        if temp_path.exists():
            temp_path.unlink()
        return False
    except FileNotFoundError:
        print(f"   ❌ ffmpeg not found. Please install ffmpeg:")
        print(f"      brew install ffmpeg")
        return False
    
    # Verify the new video duration
    try:
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(temp_path)
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        verify_duration = float(result.stdout.strip())
        
        if show_progress:
            print(f"   ")
            print(f"   Verification:")
            print(f"   - New duration: {verify_duration:.2f}s")
            print(f"   - Expected: {actual_duration:.2f}s")
            print(f"   - Difference: {abs(verify_duration - actual_duration):.3f}s")
        
        # Check if rescaling was successful (within 1 second tolerance)
        if abs(verify_duration - actual_duration) > 1.0:
            print(f"   ⚠️  WARNING: Rescaled duration doesn't match expected")
            print(f"   Expected {actual_duration:.2f}s, got {verify_duration:.2f}s")
    except Exception as e:
        print(f"   ⚠️  Could not verify new video: {e}")
    
    # Replace original with rescaled version
    backup_path = recording_path / "screen_recording_original.mp4"
    
    # Only backup if not already backed up
    if not backup_path.exists():
        video_path.rename(backup_path)
        if show_progress:
            print(f"   📦 Original backed up to: screen_recording_original.mp4")
    else:
        video_path.unlink()
        if show_progress:
            print(f"   📦 Replaced video (original backup already exists)")
    
    temp_path.rename(video_path)
    
    if show_progress:
        print(f"   ")
        print(f"   ✅ Video rescaled successfully!")
    
    return True


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
        print("Video Rescaler (ffmpeg) - Fix Timing Sync Issues")
        print("=" * 70)
        print()
        rescale_all_recordings()

