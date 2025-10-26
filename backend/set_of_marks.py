"""
Set-of-Marks Visual Grounding System
Overlay numbered labels on UI elements for precise element identification
Inspired by Anthropic Claude Computer Use
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Tuple, Optional
import os


class SetOfMarks:
    """
    Create annotated screenshots with numbered overlays on UI elements.
    
    This technique improves accuracy by:
    - Providing unambiguous element references (numbers)
    - Enabling precise coordinate extraction
    - Reducing vision model hallucinations
    - Speeding up element location
    """
    
    def __init__(self, font_size: int = 16, mark_color: Tuple[int, int, int, int] = (255, 0, 0, 200)):
        """
        Initialize Set-of-Marks system
        
        Args:
            font_size: Size of mark numbers
            mark_color: RGBA color for marks
        """
        self.font_size = font_size
        self.mark_color = mark_color
        self.font = self._load_font()
    
    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Load system font"""
        try:
            # Try macOS system fonts
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/SFNS.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, self.font_size)
            
            # Fallback to default
            return ImageFont.load_default()
        except:
            return ImageFont.load_default()
    
    def create_annotated_screenshot(self, 
                                    screenshot: Image.Image,
                                    ocr_detections: List[Dict],
                                    show_boxes: bool = True,
                                    show_marks: bool = True,
                                    min_confidence: float = 0.6) -> Tuple[Image.Image, Dict[int, Dict]]:
        """
        Create screenshot with numbered marks on UI elements
        
        Args:
            screenshot: Original screenshot (PIL Image)
            ocr_detections: List of OCR detections with bboxes
            show_boxes: Draw bounding boxes around elements
            show_marks: Draw numbered circles on elements
            min_confidence: Minimum OCR confidence to show
        
        Returns:
            annotated_image: Screenshot with overlays
            element_map: {mark_id: {text, bbox, center, confidence, ...}}
        """
        # Create copy for annotation
        img = screenshot.copy()
        draw = ImageDraw.Draw(img, 'RGBA')
        
        element_map = {}
        mark_id = 1
        
        # Filter detections by confidence
        valid_detections = [d for d in ocr_detections if d['confidence'] >= min_confidence]
        
        for detection in valid_detections:
            text = detection['text']
            confidence = detection['confidence']
            center = detection.get('center', (0, 0))
            
            # Get bbox (with fallback for missing bbox)
            if 'bbox' in detection:
                bbox = detection['bbox']
            else:
                # Create synthetic bbox from center if missing
                cx, cy = center
                w = detection.get('width', 50)
                h = detection.get('height', 20)
                bbox = [[cx - w//2, cy - h//2], [cx + w//2, cy - h//2], 
                        [cx + w//2, cy + h//2], [cx - w//2, cy + h//2]]
            
            # Draw bounding box
            if show_boxes:
                self._draw_bbox(draw, bbox, outline=(255, 0, 0, 150), width=2)
            
            # Draw numbered mark
            if show_marks:
                self._draw_mark(draw, center, mark_id)
            
            # Store in element map
            element_map[mark_id] = {
                'mark_id': mark_id,
                'text': text,
                'bbox': bbox,
                'center': center,
                'confidence': confidence,
                'width': detection.get('width', 0),
                'height': detection.get('height', 0),
                'area': detection.get('area', 0)
            }
            
            mark_id += 1
        
        return img, element_map
    
    def _draw_bbox(self, draw: ImageDraw.ImageDraw, bbox: List[List[int]], 
                   outline: Tuple[int, int, int, int], width: int = 2):
        """Draw bounding box on image"""
        # Convert bbox to flat list of points
        points = [(p[0], p[1]) for p in bbox]
        points.append(points[0])  # Close the polygon
        draw.line(points, fill=outline, width=width)
    
    def _draw_mark(self, draw: ImageDraw.ImageDraw, center: Tuple[int, int], mark_id: int):
        """Draw numbered circle mark"""
        x, y = center
        radius = 14
        
        # Draw circle background
        circle_bbox = [
            x - radius,
            y - radius,
            x + radius,
            y + radius
        ]
        draw.ellipse(circle_bbox, fill=self.mark_color, outline=(255, 255, 255, 255), width=1)
        
        # Draw number
        number_text = str(mark_id)
        
        # Center text in circle (approximate)
        text_offset_x = -4 if mark_id < 10 else -7
        text_offset_y = -8
        
        draw.text(
            (x + text_offset_x, y + text_offset_y), 
            number_text, 
            fill=(255, 255, 255, 255), 
            font=self.font
        )
    
    def create_compact_reference(self, element_map: Dict[int, Dict], max_elements: int = 50) -> str:
        """
        Create compact text reference of marked elements
        
        Useful for passing to LLMs without images
        
        Returns:
            Multi-line string like:
            "#1: 'Submit' at (500, 300)
             #2: 'Cancel' at (600, 300)
             ..."
        """
        lines = []
        
        for mark_id in sorted(element_map.keys())[:max_elements]:
            info = element_map[mark_id]
            text = info['text'][:40]  # Truncate long text
            center = info['center']
            confidence = info['confidence']
            
            lines.append(f"#{mark_id}: '{text}' at {center} (conf: {confidence:.2f})")
        
        if len(element_map) > max_elements:
            lines.append(f"... and {len(element_map) - max_elements} more elements")
        
        return "\n".join(lines)
    
    def find_mark_by_text(self, 
                         element_map: Dict[int, Dict], 
                         target_text: str,
                         fuzzy: bool = True,
                         min_similarity: float = 0.8) -> Optional[int]:
        """
        Find mark ID that matches target text
        
        Args:
            element_map: Element map from create_annotated_screenshot
            target_text: Text to search for
            fuzzy: Allow fuzzy matching
            min_similarity: Minimum similarity for fuzzy match
        
        Returns:
            Mark ID or None
        """
        target_lower = target_text.lower().strip()
        
        if not fuzzy:
            # Exact match
            for mark_id, info in element_map.items():
                if info['text'].lower().strip() == target_lower:
                    return mark_id
            return None
        else:
            # Fuzzy match
            from fuzzywuzzy import fuzz
            
            best_mark_id = None
            best_score = 0
            
            for mark_id, info in element_map.items():
                score = fuzz.ratio(info['text'].lower(), target_lower) / 100.0
                if score > best_score and score >= min_similarity:
                    best_score = score
                    best_mark_id = mark_id
            
            return best_mark_id
    
    def get_element_by_mark(self, element_map: Dict[int, Dict], mark_id: int) -> Optional[Dict]:
        """Get element info by mark ID"""
        return element_map.get(mark_id)
    
    def create_legend(self, 
                     screenshot: Image.Image, 
                     element_map: Dict[int, Dict],
                     top_n: int = 10) -> Image.Image:
        """
        Create a legend showing top N marked elements with their text
        
        Useful for debugging or displaying to users
        """
        # Create white background for legend
        legend_height = min(300, 30 + top_n * 25)
        legend = Image.new('RGBA', (400, legend_height), (255, 255, 255, 230))
        draw = ImageDraw.Draw(legend)
        
        # Title
        draw.text((10, 5), "Marked Elements:", fill=(0, 0, 0, 255), font=self.font)
        
        # List top N elements
        y_offset = 30
        for mark_id in sorted(element_map.keys())[:top_n]:
            info = element_map[mark_id]
            text = info['text'][:35]  # Truncate
            
            # Draw mark number
            self._draw_mark(draw, (20, y_offset + 5), mark_id)
            
            # Draw text
            draw.text((45, y_offset), f"{text}", fill=(0, 0, 0, 255), font=self.font)
            
            y_offset += 25
        
        # Composite legend onto screenshot
        result = screenshot.copy()
        result.paste(legend, (10, 10), legend)
        
        return result


def test_set_of_marks():
    """Test set-of-marks system"""
    import pyautogui
    from vlm_ocr_engine import VLMOCREngine
    
    print("=" * 70)
    print("Set-of-Marks Test")
    print("=" * 70)
    print()
    
    # Initialize components
    print("Initializing components...")
    ocr = VLMOCREngine(verbose=False)
    som = SetOfMarks(font_size=16)
    
    # Take screenshot
    print("Capturing screenshot...")
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    
    # Detect text
    print("Running OCR...")
    detections = ocr.detect_text_with_boxes(screenshot_np)
    print(f"✓ Detected {len(detections)} text elements")
    
    # Create annotated screenshot
    print("\nCreating set-of-marks overlay...")
    annotated_img, element_map = som.create_annotated_screenshot(
        screenshot, 
        detections,
        show_boxes=True,
        show_marks=True,
        min_confidence=0.6
    )
    
    print(f"✓ Created {len(element_map)} marks")
    
    # Save annotated screenshot
    output_path = "/tmp/set_of_marks_test.png"
    annotated_img.save(output_path)
    print(f"\n💾 Saved annotated screenshot to: {output_path}")
    
    # Create compact reference
    print("\n" + "=" * 70)
    print("Compact Reference (first 20 elements):")
    print("=" * 70)
    reference = som.create_compact_reference(element_map, max_elements=20)
    print(reference)
    
    # Test text search
    print("\n" + "=" * 70)
    print("Testing mark search by text:")
    print("=" * 70)
    
    if element_map:
        # Search for first element's text
        first_element = element_map[1]
        target_text = first_element['text']
        
        print(f"\nSearching for: '{target_text}'")
        mark_id = som.find_mark_by_text(element_map, target_text, fuzzy=False)
        print(f"✓ Found mark #{mark_id}")
        
        # Fuzzy search
        partial = target_text[:len(target_text)//2] if len(target_text) > 1 else target_text
        print(f"\nFuzzy search for: '{partial}'")
        mark_id = som.find_mark_by_text(element_map, partial, fuzzy=True)
        if mark_id:
            matched_elem = element_map[mark_id]
            print(f"✓ Found mark #{mark_id}: '{matched_elem['text']}'")
    
    # Create legend version
    print("\nCreating screenshot with legend...")
    legend_img = som.create_legend(annotated_img, element_map, top_n=10)
    legend_path = "/tmp/set_of_marks_legend.png"
    legend_img.save(legend_path)
    print(f"💾 Saved with legend to: {legend_path}")
    
    print("\n✅ Test complete!")
    print(f"\nOpen the saved images to see the results:")
    print(f"  {output_path}")
    print(f"  {legend_path}")


if __name__ == "__main__":
    test_set_of_marks()

