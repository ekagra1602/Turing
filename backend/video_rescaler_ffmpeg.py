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
    
    # Check if video has constant frame rate (not distorted by setpts)
    # We need to check if frame timing is correct, not just duration
    needs_reencoding = False
    
    if original_duration > 0:
        duration_diff = abs(actual_duration - original_duration)
        
        # Get actual FPS from video file
        probe_fps_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        try:
            result = subprocess.run(probe_fps_cmd, capture_output=True, text=True, timeout=10)
            fps_str = result.stdout.strip()
            # Parse fraction like "173/6"
            if '/' in fps_str:
                num, denom = fps_str.split('/')
                video_fps = float(num) / float(denom)
            else:
                video_fps = float(fps_str)
        except:
            video_fps = 30  # Default fallback
        
        # Get frame count
        probe_count_cmd = [
            'ffprobe',
            '-v', 'error',
            '-count_frames',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=nb_read_frames',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        try:
            result = subprocess.run(probe_count_cmd, capture_output=True, text=True, timeout=10)
            frame_count = int(result.stdout.strip())
        except:
            frame_count = 0
        
        # Calculate what FPS should be for proper frame extraction
        expected_fps = frame_count / actual_duration if actual_duration > 0 else video_fps
        
        # Check if video needs re-encoding
        # Re-encode if:c
        # 1. FPS metadata doesn't match expected FPS (off by more than 10%)
        # 2. Video was previously rescaled with setpts (check for "corrected_fps" flag)
        events_path = recording_path / "events.json"
        was_rescaled = False
        if events_path.exists():
            try:
                with open(events_path, 'r') as f:
                    events_data = json.load(f)
                was_rescaled = events_data.get('corrected_fps', False)
            except:
                pass
        
        fps_mismatch = abs(video_fps - expected_fps) / expected_fps > 0.1 if expected_fps > 0 else False
        
        if duration_diff < 0.5 and not fps_mismatch and not was_rescaled:
            if show_progress:
                print(f"   ✅ Video already has correct timing (duration: {original_duration:.2f}s, FPS: {video_fps:.2f})")
            return True
        
        if was_rescaled or fps_mismatch:
            needs_reencoding = True
            if show_progress:
                print(f"   ⚠️  Video needs re-encoding for proper frame timing")
                print(f"   - Current FPS: {video_fps:.2f}")
                print(f"   - Expected FPS: {expected_fps:.2f}")
                if was_rescaled:
                    print(f"   - Previous rescaling used distorting method")
    
    # Get frame count to calculate proper output FPS
    probe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-count_frames',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=nb_read_frames',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(video_path)
    ]
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        frame_count = int(result.stdout.strip())
    except Exception as e:
        print(f"   ❌ Could not count frames: {e}")
        return False
    
    # Calculate the target FPS to match actual duration
    # This is CRITICAL: we need to re-encode at constant FPS, not just stretch timestamps
    target_fps = frame_count / actual_duration
    
    if show_progress:
        print(f"   ")
        print(f"   🔄 Re-encoding video with ffmpeg...")
        print(f"   - Frame count: {frame_count}")
        print(f"   - Target duration: {actual_duration:.2f}s")
        print(f"   - Target FPS: {target_fps:.2f}")
        print(f"   - Method: Re-encode at constant frame rate")
    
    # Create temporary output path
    temp_path = recording_path / "screen_recording_rescaled.mp4"
    
    # CRITICAL FIX: Re-encode video at constant FPS instead of using setpts
    # setpts distorts frame timing and breaks OpenCV frame seeking
    # Instead, we re-encode with -r flag to set exact output FPS
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-r', str(target_fps),  # Set output frame rate (re-encodes frames)
        '-vsync', 'cfr',        # Constant frame rate (ensures even spacing)
        '-an',                  # No audio
        '-y',                   # Overwrite output file
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
    
    # CRITICAL: Update events.json with corrected FPS for the rescaled video
    # The video now has the correct duration, but we need to update the FPS metadata
    # so the recording processor can extract frames correctly
    events_path = recording_path / "events.json"
    if events_path.exists():
        try:
            with open(events_path, 'r') as f:
                events_data = json.load(f)
            
            # Get the actual frame count and duration
            probe_cmd = [
                'ffprobe',
                '-v', 'error',
                '-count_frames',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=nb_read_frames',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(video_path)
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            frame_count = int(result.stdout.strip())
            
            # Calculate the actual FPS needed for correct frame extraction
            # This is critical: duration is correct, but FPS metadata needs updating
            actual_fps = frame_count / actual_duration
            
            # Update events.json with corrected FPS
            events_data['fps'] = actual_fps
            events_data['corrected_fps'] = True  # Flag that we corrected it
            events_data['original_fps'] = fps if 'original_fps' not in events_data else events_data.get('original_fps')
            
            with open(events_path, 'w') as f:
                json.dump(events_data, f, indent=2)
            
            if show_progress:
                print(f"   📝 Updated events.json with corrected FPS: {actual_fps:.2f}")
        except Exception as e:
            if show_progress:
                print(f"   ⚠️  Could not update events.json FPS: {e}")
    
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

