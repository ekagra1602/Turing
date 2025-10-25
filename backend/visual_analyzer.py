"""
Visual Analysis Engine
Extracts meaning from screenshots, identifies UI elements, performs OCR
"""

import os
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
import imagehash

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️  pytesseract not available. OCR will be limited.")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️  EasyOCR not available. Using fallback OCR.")


class VisualAnalyzer:
    """
    Analyzes screenshots to extract visual information and understand UI elements.
    """
    
    def __init__(self, use_easyocr: bool = True):
        self.use_easyocr = use_easyocr and EASYOCR_AVAILABLE
        
        # Initialize OCR
        if self.use_easyocr:
            try:
                print("🔧 Initializing EasyOCR...")
                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                print("✅ EasyOCR ready")
            except Exception as e:
                print(f"⚠️  EasyOCR initialization failed: {e}")
                self.ocr_reader = None
                self.use_easyocr = False
        else:
            self.ocr_reader = None
        
        print("✅ Visual Analyzer initialized")
    
    def analyze_click_context(self, 
                              screenshot: Image.Image,
                              click_x: int,
                              click_y: int,
                              radius: int = 100) -> Dict[str, Any]:
        """
        Analyze what was clicked in a screenshot.
        
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
            'clicked_text': None,
            'nearby_text': [],
            'element_signature': None,
            'ocr_confidence': 0.0
        }
        
        # Crop region around click
        left = max(0, click_x - radius)
        top = max(0, click_y - radius)
        right = min(screenshot.width, click_x + radius)
        bottom = min(screenshot.height, click_y + radius)
        
        cropped = screenshot.crop((left, top, right, bottom))
        
        # Perform OCR on region
        ocr_results = self.ocr_image(cropped)
        
        if ocr_results:
            # Find text nearest to click point
            # (click point is now at center of cropped image)
            crop_center_x = radius
            crop_center_y = radius
            
            closest_text = None
            min_distance = float('inf')
            
            for result in ocr_results:
                bbox = result['bbox']
                text = result['text']
                conf = result['confidence']
                
                # Calculate center of text box
                text_center_x = sum([p[0] for p in bbox]) / 4
                text_center_y = sum([p[1] for p in bbox]) / 4
                
                # Distance from click point
                distance = ((text_center_x - crop_center_x) ** 2 + 
                           (text_center_y - crop_center_y) ** 2) ** 0.5
                
                # Track all nearby text
                if distance < radius:
                    context['nearby_text'].append({
                        'text': text,
                        'distance': distance,
                        'confidence': conf
                    })
                
                # Find closest
                if distance < min_distance and conf > 0.5:
                    min_distance = distance
                    closest_text = text
                    context['ocr_confidence'] = conf
            
            context['clicked_text'] = closest_text
        
        # Create visual signature (perceptual hash)
        context['element_signature'] = str(imagehash.average_hash(cropped))
        
        # Save cropped element for future matching
        context['cropped_element'] = cropped
        
        return context
    
    def ocr_image(self, image: Image.Image) -> List[Dict]:
        """
        Perform OCR on image to extract text with bounding boxes.
        
        Returns:
            List of dict with 'bbox', 'text', 'confidence'
        """
        if self.use_easyocr and self.ocr_reader:
            return self._ocr_easyocr(image)
        elif TESSERACT_AVAILABLE:
            return self._ocr_tesseract(image)
        else:
            return []
    
    def _ocr_easyocr(self, image: Image.Image) -> List[Dict]:
        """OCR using EasyOCR."""
        try:
            # Convert PIL to numpy array
            img_array = np.array(image)
            
            # EasyOCR
            results = self.ocr_reader.readtext(img_array)
            
            # Format results
            formatted = []
            for bbox, text, confidence in results:
                formatted.append({
                    'bbox': bbox,
                    'text': text,
                    'confidence': confidence
                })
            
            return formatted
        except Exception as e:
            print(f"⚠️  EasyOCR failed: {e}")
            return []
    
    def _ocr_tesseract(self, image: Image.Image) -> List[Dict]:
        """OCR using Tesseract (fallback)."""
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            results = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf > 0:
                    x, y, w, h = (data['left'][i], data['top'][i], 
                                 data['width'][i], data['height'][i])
                    
                    # Create bbox in format similar to EasyOCR
                    bbox = [
                        [x, y],
                        [x + w, y],
                        [x + w, y + h],
                        [x, y + h]
                    ]
                    
                    results.append({
                        'bbox': bbox,
                        'text': text,
                        'confidence': conf / 100.0
                    })
            
            return results
        except Exception as e:
            print(f"⚠️  Tesseract failed: {e}")
            return []
    
    def find_text_in_screenshot(self, 
                               screenshot: Image.Image,
                               target_text: str,
                               fuzzy: bool = True) -> List[Dict]:
        """
        Find all occurrences of text in screenshot.
        
        Args:
            screenshot: PIL Image
            target_text: Text to search for
            fuzzy: Allow fuzzy matching
        
        Returns:
            List of matches with bbox and center coordinates
        """
        from fuzzywuzzy import fuzz
        
        ocr_results = self.ocr_image(screenshot)
        matches = []
        
        target_lower = target_text.lower()
        
        for result in ocr_results:
            text = result['text']
            bbox = result['bbox']
            conf = result['confidence']
            
            # Check for match
            is_match = False
            similarity = 0
            
            if fuzzy:
                # Fuzzy string matching
                similarity = fuzz.partial_ratio(target_lower, text.lower())
                is_match = similarity > 80
            else:
                # Exact substring match
                is_match = target_lower in text.lower()
                similarity = 100 if is_match else 0
            
            if is_match:
                # Calculate center
                center_x = sum([p[0] for p in bbox]) / 4
                center_y = sum([p[1] for p in bbox]) / 4
                
                matches.append({
                    'text': text,
                    'target': target_text,
                    'similarity': similarity,
                    'confidence': conf,
                    'bbox': bbox,
                    'center': (int(center_x), int(center_y))
                })
        
        # Sort by similarity
        matches.sort(key=lambda x: (x['similarity'], x['confidence']), reverse=True)
        return matches
    
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
    
    # Test OCR on full screen
    print("\nPerforming OCR on screenshot...")
    ocr_results = analyzer.ocr_image(screenshot)
    print(f"Found {len(ocr_results)} text regions")
    
    if ocr_results:
        print("\nSample text found:")
        for result in ocr_results[:5]:  # Show first 5
            print(f"  - '{result['text']}' (confidence: {result['confidence']:.2f})")
    
    # Test click analysis
    print("\nAnalyzing center of screen...")
    center_x = screenshot.width // 2
    center_y = screenshot.height // 2
    
    context = analyzer.analyze_click_context(screenshot, center_x, center_y)
    print(f"Clicked text: {context['clicked_text']}")
    print(f"Nearby text: {len(context['nearby_text'])} items")
    
    print("\n✅ Visual analyzer test complete!")


if __name__ == "__main__":
    test_visual_analyzer()

