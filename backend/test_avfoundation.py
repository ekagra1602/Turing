#!/usr/bin/env python3
"""
Test avfoundation screen capture directly
"""

import subprocess
import time
from pathlib import Path

print("Testing ffmpeg avfoundation screen capture...")
print()

# List available devices
print("1. Listing available devices:")
result = subprocess.run(
    ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
    capture_output=True,
    text=True
)
print("STDERR:")
print(result.stderr)
print()

# Try capturing screen
output_file = Path(__file__).parent / "test_avfoundation.mp4"

print(f"2. Testing screen capture to {output_file}")
print("   Recording for 3 seconds...")
print()

process = subprocess.Popen(
    [
        'ffmpeg',
        '-f', 'avfoundation',
        '-framerate', '15',
        '-i', '1:none',
        '-t', '3',  # 3 seconds
        '-vcodec', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-y',
        str(output_file)
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for completion
stdout, stderr = process.communicate()

print("STDOUT:")
print(stdout)
print()
print("STDERR:")
print(stderr)
print()

# Check result
if output_file.exists():
    size = output_file.stat().st_size
    print(f"✅ Success! File created: {size / 1024 / 1024:.1f} MB")
else:
    print("❌ File not created")
