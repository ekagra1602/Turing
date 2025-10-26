#!/usr/bin/env python3
"""
Quick test to verify video encoding works on macOS
"""

import cv2
import numpy as np
from pathlib import Path

print("Testing video encoding on macOS...")
print()

test_dir = Path(__file__).parent / "test_recordings"
test_dir.mkdir(exist_ok=True)

width, height = 640, 480
fps = 10

codecs_to_test = [
    ('avc1', '.mp4', 'H.264 (Apple)'),
    ('mp4v', '.mp4', 'MPEG-4'),
    ('MJPG', '.avi', 'Motion JPEG'),
]

results = []

for codec, ext, name in codecs_to_test:
    print(f"Testing {name} ({codec})...")

    test_file = test_dir / f"test_{codec}{ext}"

    try:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(
            str(test_file),
            fourcc,
            fps,
            (width, height)
        )

        if not writer.isOpened():
            print(f"  ❌ Failed to open writer")
            results.append((codec, False, "Writer didn't open"))
            continue

        # Write 30 test frames (3 seconds)
        for i in range(30):
            # Create a gradient frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = [i * 8, 128, 255 - i * 8]
            writer.write(frame)

        writer.release()

        # Check file was created and is valid
        if test_file.exists():
            file_size = test_file.stat().st_size
            if file_size > 0:
                # Try to read it back
                cap = cv2.VideoCapture(str(test_file))
                if cap.isOpened():
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    cap.release()

                    print(f"  ✅ SUCCESS!")
                    print(f"     File size: {file_size / 1024:.1f} KB")
                    print(f"     Frames: {frame_count}")
                    results.append((codec, True, f"{file_size / 1024:.1f} KB"))
                else:
                    print(f"  ❌ File created but can't be read (corrupted)")
                    results.append((codec, False, "Corrupted"))
            else:
                print(f"  ❌ File is empty")
                results.append((codec, False, "Empty file"))
        else:
            print(f"  ❌ File not created")
            results.append((codec, False, "No file"))

    except Exception as e:
        print(f"  ❌ Exception: {e}")
        results.append((codec, False, str(e)))

    print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)

working_codecs = [r for r in results if r[1]]

if working_codecs:
    print(f"\n✅ {len(working_codecs)} codec(s) working:")
    for codec, _, info in working_codecs:
        print(f"   • {codec}: {info}")
    print(f"\nRecommendation: Use {working_codecs[0][0]} for best results")
else:
    print("\n❌ No codecs working!")
    print("   This is unusual. You may need to install ffmpeg:")
    print("   brew install ffmpeg")

print()
print("Test files saved in:", test_dir)
print("=" * 70)
