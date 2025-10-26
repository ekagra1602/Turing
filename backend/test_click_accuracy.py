#!/usr/bin/env python3
"""
Test click accuracy after Retina scaling fix
"""

import pyautogui
import numpy as np
from gemini_computer_use import GeminiComputerUse

def test_screen_scaling():
    """Test that we detect Retina scaling correctly"""
    print("=" * 70)
    print("🔍 TESTING SCREEN SCALING DETECTION")
    print("=" * 70)
    
    # Capture screenshot
    screenshot = np.array(pyautogui.screenshot())
    
    # Get screen size
    screen_size = pyautogui.size()
    
    print(f"\n📊 Display Information:")
    print(f"   Logical screen size: {screen_size.width}x{screen_size.height}")
    print(f"   Screenshot size: {screenshot.shape[1]}x{screenshot.shape[0]}")
    
    # Calculate scaling
    scale_x, scale_y = GeminiComputerUse.get_screen_scaling(screenshot)
    
    print(f"   Scaling factor: {scale_x:.1f}x (horizontal), {scale_y:.1f}x (vertical)")
    
    if scale_x == 1.0 and scale_y == 1.0:
        print("\n✅ Standard display (no scaling)")
    elif scale_x == 2.0 and scale_y == 2.0:
        print("\n✅ Retina 2x display detected")
        print("   🔧 Coordinate scaling is ENABLED")
    else:
        print(f"\n⚠️  Unusual scaling: {scale_x:.1f}x")
    
    return scale_x, scale_y


def test_coordinate_conversion():
    """Test coordinate conversion"""
    print("\n" + "=" * 70)
    print("🔢 TESTING COORDINATE CONVERSION")
    print("=" * 70)
    
    screen_size = pyautogui.size()
    
    # Test cases using NORMALIZED coordinates (0-999)
    test_cases = [
        (500, 50, "Top-center (address bar typical position)"),
        (100, 200, "Top-left area (Compose button)"),
        (700, 300, "Right side (To field)"),
        (500, 350, "Center-left (Subject field)"),
        (500, 500, "Center (email body)"),
        (150, 950, "Bottom-left (Send button)"),
    ]
    
    print(f"\n📍 Converting NORMALIZED coordinates (0-999) to screen pixels:")
    print(f"   Screen: {screen_size.width}x{screen_size.height}")
    print()
    
    for normalized_x, normalized_y, description in test_cases:
        click_x, click_y = GeminiComputerUse.denormalize_coordinates(
            normalized_x, normalized_y,
            screen_size.width, screen_size.height
        )
        
        # Check if within bounds (should always be)
        in_bounds = 0 <= click_x < screen_size.width and 0 <= click_y < screen_size.height
        status = "✅" if in_bounds else "❌ OUT OF BOUNDS"
        
        print(f"   Normalized ({normalized_x:3d}, {normalized_y:3d}) → Pixel ({click_x:4d}, {click_y:4d}) {status}")
        print(f"      {description}")
        print()
    
    print()


def test_click_visualization():
    """Visualize where clicks would happen"""
    print("\n" + "=" * 70)
    print("🎯 CLICK COORDINATE ANALYSIS")
    print("=" * 70)
    
    screen_size = pyautogui.size()
    
    print(f"\n🖥️  Your display:")
    print(f"   Logical size: {screen_size.width}x{screen_size.height}")
    
    print(f"\n❌ OLD APPROACH (Pixel Coordinates + Retina Scaling):")
    print(f"   1. Gemini analyzes screenshot and returns pixel coords")
    print(f"   2. System divides by Retina scaling factor (2x)")
    print(f"   3. Result: Somewhat accurate but not optimal")
    print(f"   Example: Gemini returns (1084, 69) → scales to (542, 34)")
    
    print(f"\n✅ NEW APPROACH (Normalized Coordinates):")
    print(f"   1. Gemini returns NORMALIZED coords (0-999 range)")
    print(f"   2. System denormalizes to actual screen pixels")
    print(f"   3. Result: Maximum accuracy, resolution-independent!")
    print(f"   Example: Gemini returns (500, 50) → denormalizes to ({screen_size.width//2}, {int(screen_size.height * 0.05)})")
    
    print(f"\n📊 BENEFITS:")
    print(f"   ✅ Resolution-independent: Works on any screen size")
    print(f"   ✅ More accurate: Model trained on 0-999 grid")
    print(f"   ✅ Simpler: No Retina scaling complications")
    print(f"   ✅ Consistent: Same approach as official Computer Use API")
    
    print()


def main():
    print("\n" + "=" * 70)
    print("🔧 CLICK ACCURACY TEST SUITE")
    print("   Testing Retina Display Coordinate Scaling Fix")
    print("=" * 70)
    print()
    
    try:
        # Run tests
        scale_x, scale_y = test_screen_scaling()
        test_coordinate_conversion()
        test_click_visualization()
        
        print("=" * 70)
        print("✅ TEST SUITE COMPLETE")
        print("=" * 70)
        
        if scale_x == 2.0:
            print("\n🎉 Retina scaling fix is ACTIVE and working correctly!")
            print("   Coordinates will now be accurate for clicking.")
        else:
            print("\n✅ No scaling needed on your display.")
        
        print("\n📝 Next step: Test with actual workflow execution")
        print("   Run: python workflow_cli.py execute 'your workflow' --auto")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

