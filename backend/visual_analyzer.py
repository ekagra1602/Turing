"""
Visual Analysis Engine
Analyzes screenshots for UI changes and visual signatures
Note: Text extraction is handled by VLMs, not OCR
"""

import os
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
import imagehash


class VisualAnalyzer:
    """
    Analyzes screenshots to extract visual information and understand UI elements.
    Text extraction is handled by VLMs in the recording processor.
    """
    
    def __init__(self):
        print("✅ Visual Analyzer initialized (VLM-powered)")
    
    def analyze_click_context(self, 
                              screenshot: Image.Image,
                              click_x: int,
                              click_y: int,
                              radius: int = 100) -> Dict[str, Any]:
        """
        Analyze visual context around a click location.
        Note: Text extraction is handled by VLMs, not OCR.
        
        Args:
            screenshot: PIL Image of screen
            click_x: X coordinate of click
            click_y: Y coordinate of click
            radius: Radius around click point to analyze
        
        Returns:
            Dictionary with visual context information
        """
        context = {
            'click_location': (click_x, click_y),
            'clicked_text': None,  # Will be filled by VLM
            'nearby_text': [],      # Will be filled by VLM
            'element_signature': None,
            'ocr_confidence': 0.0
        }
        
        # Crop region around click
        left = max(0, click_x - radius)
        top = max(0, click_y - radius)
        right = min(screenshot.width, click_x + radius)
        bottom = min(screenshot.height, click_y + radius)
        
        cropped = screenshot.crop((left, top, right, bottom))
        
        # Create visual signature (perceptual hash) for element matching
        context['element_signature'] = str(imagehash.average_hash(cropped))
        
        # Save cropped element for future matching
        context['cropped_element'] = cropped
        
        return context
    
    
    def detect_ui_change(self, 
                        before: Image.Image,
                        after: Image.Image,
                        threshold: int = 5) -> bool:
        """
        Detect if UI changed significantly between two screenshots.
        
        Args:
            before: Screenshot before action
            after: Screenshot after action
            threshold: Difference threshold (0-64)
        
        Returns:
            True if significant change detected
        """
        hash_before = imagehash.average_hash(before)
        hash_after = imagehash.average_hash(after)
        
        difference = hash_before - hash_after
        return difference > threshold
    
    def create_visual_signature(self, element_image: Image.Image) -> Dict[str, Any]:
        """
        Create a multi-modal signature of a UI element for future matching.
        
        Args:
            element_image: Cropped image of UI element
        
        Returns:
            Dictionary of signatures (hash, colors, edges, etc.)
        """
        signature = {}
        
        # Perceptual hash
        signature['phash'] = str(imagehash.phash(element_image))
        signature['average_hash'] = str(imagehash.average_hash(element_image))
        signature['dhash'] = str(imagehash.dhash(element_image))
        
        # Convert to array for analysis
        img_array = np.array(element_image)
        
        # Color histogram
        if len(img_array.shape) == 3:
            hist = cv2.calcHist([cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)], 
                               [0, 1, 2], None, [8, 8, 8], 
                               [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            signature['color_histogram'] = hist.tolist()[:100]  # Truncate for storage
        
        # Size
        signature['size'] = element_image.size
        
        # Dominant color
        img_small = element_image.resize((50, 50))
        pixels = list(img_small.getdata())
        if pixels:
            avg_color = tuple(int(sum(c) / len(pixels)) for c in zip(*pixels))
            signature['dominant_color'] = avg_color
        
        return signature
    
    def match_element(self,
                     current_screenshot: Image.Image,
                     target_signature: Dict[str, Any],
                     threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Find element in current screenshot matching target signature.
        
        Args:
            current_screenshot: Current screen state
            target_signature: Signature from recorded workflow
            threshold: Matching threshold (0-1)
        
        Returns:
            (x, y) coordinates of match, or None
        """
        # For now, use template matching with stored cropped element
        # In production, would use more sophisticated matching
        
        # This is a placeholder - full implementation would:
        # 1. Use sliding window to search screen
        # 2. Compare signatures at each location
        # 3. Use OCR to find text matches
        # 4. Combine multiple strategies
        
        return None  # TODO: Implement
    
    def annotate_screenshot(self,
                           screenshot: Image.Image,
                           annotations: List[Dict]) -> Image.Image:
        """
        Draw annotations on screenshot for visualization.
        
        Args:
            screenshot: Base image
            annotations: List of annotations (boxes, labels, etc.)
        
        Returns:
            Annotated image
        """
        img = screenshot.copy()
        draw = ImageDraw.Draw(img)
        
        for ann in annotations:
            ann_type = ann.get('type')
            
            if ann_type == 'bbox':
                bbox = ann['bbox']
                # Draw rectangle
                points = [(p[0], p[1]) for p in bbox]
                points.append(points[0])  # Close the box
                draw.line(points, fill='red', width=2)
                
                # Draw label if provided
                if 'label' in ann:
                    draw.text((bbox[0][0], bbox[0][1] - 10), 
                             ann['label'], fill='red')
            
            elif ann_type == 'point':
                x, y = ann['point']
                r = ann.get('radius', 5)
                draw.ellipse([x-r, y-r, x+r, y+r], fill='red', outline='darkred')
        
        return img


def test_visual_analyzer():
    """Test visual analysis capabilities."""
    print("=" * 70)
    print("Testing Visual Analyzer")
    print("=" * 70)
    
    analyzer = VisualAnalyzer()
    
    # Take a test screenshot
    import pyautogui
    print("\nCapturing screenshot...")
    screenshot = pyautogui.screenshot()
    
    # Test click analysis
    print("\nAnalyzing center of screen...")
    center_x = screenshot.width // 2
    center_y = screenshot.height // 2
    
    context = analyzer.analyze_click_context(screenshot, center_x, center_y)
    print(f"Element signature: {context['element_signature']}")
    print(f"Cropped element size: {context['cropped_element'].size}")
    
    # Test UI change detection
    print("\nTesting UI change detection...")
    screenshot2 = pyautogui.screenshot()
    changed = analyzer.detect_ui_change(screenshot, screenshot2)
    print(f"UI changed: {changed}")
    
    print("\n✅ Visual analyzer test complete!")
    print("Note: Text extraction is handled by VLMs in the recording processor")


if __name__ == "__main__":
    test_visual_analyzer()

