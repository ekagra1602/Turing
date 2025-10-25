#!/usr/bin/env python3
"""
Basic test to verify imports and functionality
"""

print("Testing AgentFlow components...")
print("-" * 60)

# Test imports
print("\n1. Testing imports...")
try:
    from action_recorder import ActionRecorder
    print("   ✓ ActionRecorder imported")
except Exception as e:
    print(f"   ✗ ActionRecorder failed: {e}")

try:
    from action_player import ActionPlayer
    print("   ✓ ActionPlayer imported")
except Exception as e:
    print(f"   ✗ ActionPlayer failed: {e}")

try:
    from window_manager import WindowManager
    print("   ✓ WindowManager imported")
except Exception as e:
    print(f"   ✗ WindowManager failed: {e}")

# Test basic instantiation
print("\n2. Testing object creation...")
try:
    recorder = ActionRecorder()
    print("   ✓ ActionRecorder created")
except Exception as e:
    print(f"   ✗ ActionRecorder creation failed: {e}")

try:
    player = ActionPlayer()
    print("   ✓ ActionPlayer created")
except Exception as e:
    print(f"   ✗ ActionPlayer creation failed: {e}")

try:
    wm = WindowManager()
    print("   ✓ WindowManager created")
except Exception as e:
    print(f"   ✗ WindowManager creation failed: {e}")

# Test window capture
print("\n3. Testing window capture...")
try:
    windows = wm.get_all_windows()
    print(f"   ✓ Captured {len(windows)} window states")
except Exception as e:
    print(f"   ✗ Window capture failed: {e}")

# Test recorder info
print("\n4. Testing recorder info...")
try:
    info = recorder.get_recording_info()
    print(f"   ✓ Recorder info: {info}")
except Exception as e:
    print(f"   ✗ Recorder info failed: {e}")

print("\n" + "=" * 60)
print("All basic tests completed!")
print("\nYou can now run the app with:")
print("  ./venv/bin/python simple_cli.py")
print("\nOr with the GUI (if tkinter is available):")
print("  ./venv/bin/python main.py")
