"""
Coordinate Normalization System
Converts between pixel coordinates and normalized 0-1000 scale for resolution independence
"""

from typing import Tuple, List
import pyautogui


class CoordinateNormalizer:
    """
    Handle conversion between pixel and normalized coordinates.
    
    Normalized coordinates use a 0-1000 scale where:
    - (0, 0) = top-left corner
    - (1000, 1000) = bottom-right corner
    - (500, 500) = center of screen
    
    Benefits:
    - Resolution-independent workflows
    - Easier to reason about positions
    - Compatible with vision models that output normalized coords
    """
    
    def __init__(self, screen_width: int = None, screen_height: int = None):
        """
        Initialize normalizer
        
        Args:
            screen_width: Screen width in pixels (auto-detected if None)
            screen_height: Screen height in pixels (auto-detected if None)
        """
        if screen_width is None or screen_height is None:
            self.screen_width, self.screen_height = self._get_screen_size()
        else:
            self.screen_width = screen_width
            self.screen_height = screen_height
        
        print(f"📐 Coordinate Normalizer initialized")
        print(f"   Screen: {self.screen_width}x{self.screen_height}")
    
    def _get_screen_size(self) -> Tuple[int, int]:
        """Get current screen resolution"""
        size = pyautogui.size()
        return size.width, size.height
    
    def normalize(self, x: int, y: int) -> Tuple[int, int]:
        """
        Convert pixel coordinates to 0-1000 scale
        
        Args:
            x: X pixel coordinate
            y: Y pixel coordinate
        
        Returns:
            (norm_x, norm_y) in 0-1000 scale
        """
        norm_x = int((x / self.screen_width) * 1000)
        norm_y = int((y / self.screen_height) * 1000)
        
        # Clamp to valid range
        norm_x = max(0, min(1000, norm_x))
        norm_y = max(0, min(1000, norm_y))
        
        return (norm_x, norm_y)
    
    def denormalize(self, norm_x: int, norm_y: int) -> Tuple[int, int]:
        """
        Convert 0-1000 coordinates back to pixels
        
        Args:
            norm_x: Normalized X (0-1000)
            norm_y: Normalized Y (0-1000)
        
        Returns:
            (x, y) in pixel coordinates
        """
        x = int((norm_x / 1000) * self.screen_width)
        y = int((norm_y / 1000) * self.screen_height)
        
        # Clamp to screen bounds
        x = max(0, min(self.screen_width - 1, x))
        y = max(0, min(self.screen_height - 1, y))
        
        return (x, y)
    
    def normalize_bbox(self, bbox: List[List[int]]) -> List[List[int]]:
        """
        Normalize a bounding box (4 corner points)
        
        Args:
            bbox: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        
        Returns:
            Normalized bbox in same format
        """
        return [list(self.normalize(p[0], p[1])) for p in bbox]
    
    def denormalize_bbox(self, norm_bbox: List[List[int]]) -> List[List[int]]:
        """
        Denormalize a bounding box
        
        Args:
            norm_bbox: Normalized [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        
        Returns:
            Pixel bbox in same format
        """
        return [list(self.denormalize(p[0], p[1])) for p in norm_bbox]
    
    def get_region_description(self, norm_x: int, norm_y: int) -> str:
        """
        Get human-readable description of region
        
        Returns strings like: "top-left", "center", "bottom-right", etc.
        """
        # Divide screen into 3x3 grid
        if norm_x < 333:
            h_region = "left"
        elif norm_x < 666:
            h_region = "center"
        else:
            h_region = "right"
        
        if norm_y < 333:
            v_region = "top"
        elif norm_y < 666:
            v_region = "middle"
        else:
            v_region = "bottom"
        
        if h_region == "center" and v_region == "middle":
            return "center"
        elif h_region == "center":
            return f"{v_region}"
        elif v_region == "middle":
            return f"{h_region}"
        else:
            return f"{v_region}-{h_region}"
    
    def is_same_region(self, 
                       pos1: Tuple[int, int], 
                       pos2: Tuple[int, int], 
                       threshold: int = 50) -> bool:
        """
        Check if two normalized positions are in the same region
        
        Args:
            pos1: (norm_x1, norm_y1)
            pos2: (norm_x2, norm_y2)
            threshold: Maximum distance in normalized units (0-1000)
        
        Returns:
            True if positions are close enough
        """
        distance = ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
        return distance <= threshold
    
    def refresh_screen_size(self):
        """Refresh screen size (call if resolution changes)"""
        self.screen_width, self.screen_height = self._get_screen_size()
        print(f"🔄 Screen size refreshed: {self.screen_width}x{self.screen_height}")


def test_normalizer():
    """Test coordinate normalization"""
    print("=" * 70)
    print("Coordinate Normalizer Test")
    print("=" * 70)
    print()
    
    normalizer = CoordinateNormalizer()
    
    # Test various positions
    test_positions = [
        (0, 0, "Top-left corner"),
        (normalizer.screen_width, normalizer.screen_height, "Bottom-right corner"),
        (normalizer.screen_width // 2, normalizer.screen_height // 2, "Center"),
        (100, 100, "Near top-left"),
        (normalizer.screen_width - 100, normalizer.screen_height - 100, "Near bottom-right"),
    ]
    
    print("\n📍 Testing normalization:")
    print("-" * 70)
    
    for x, y, desc in test_positions:
        norm_x, norm_y = normalizer.normalize(x, y)
        back_x, back_y = normalizer.denormalize(norm_x, norm_y)
        region = normalizer.get_region_description(norm_x, norm_y)
        
        print(f"{desc:20s} | ({x:4d}, {y:4d}) → ({norm_x:3d}, {norm_y:3d}) → ({back_x:4d}, {back_y:4d}) | {region}")
    
    # Test bbox normalization
    print("\n" + "=" * 70)
    print("📦 Testing bounding box normalization:")
    print("-" * 70)
    
    bbox = [[100, 100], [200, 100], [200, 150], [100, 150]]
    print(f"\nOriginal bbox: {bbox}")
    
    norm_bbox = normalizer.normalize_bbox(bbox)
    print(f"Normalized:    {norm_bbox}")
    
    back_bbox = normalizer.denormalize_bbox(norm_bbox)
    print(f"Denormalized:  {back_bbox}")
    
    # Test region comparison
    print("\n" + "=" * 70)
    print("🎯 Testing region comparison:")
    print("-" * 70)
    
    pos1 = (500, 500)  # Center
    pos2 = (520, 480)  # Near center
    pos3 = (200, 200)  # Far away
    
    same_region_1_2 = normalizer.is_same_region(pos1, pos2, threshold=50)
    same_region_1_3 = normalizer.is_same_region(pos1, pos3, threshold=50)
    
    print(f"Pos1 {pos1} and Pos2 {pos2}: {same_region_1_2} (same region)")
    print(f"Pos1 {pos1} and Pos3 {pos3}: {same_region_1_3} (different region)")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_normalizer()

