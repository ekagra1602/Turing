"""
VLM-Based OCR Engine
Uses Groq's vision models (Llama 4 Scout) for ultra-fast text detection
Perfect for slower laptops - all processing happens on Groq's servers!
"""

import numpy as np
import cv2
from PIL import Image
from typing import List, Dict, Optional
import time
import base64
import io
import json
import os


class VLMOCREngine:
    """
    VLM-based OCR engine using Groq's vision models.
    
    Features:
    - Blazingly fast (750+ tokens/sec on Groq)
    - Works great on slow laptops (server-side processing)
    - Accurate text detection with approximate positions
    - Low cost ($0.11/$0.34 per 1M tokens)
    """
    
    def __init__(self, model: str = "meta-llama/llama-4-scout-17b-16e-instruct", verbose: bool = False):
        """
        Initialize VLM OCR Engine
        
        Args:
            model: Groq vision model to use
                   - "meta-llama/llama-4-scout-17b-16e-instruct" (750 t/s, recommended)
                   - "meta-llama/llama-4-maverick-17b-128e-instruct" (600 t/s)
            verbose: Print debug information
        """
        self.verbose = verbose
        self.model = model
        self.api_key = os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set!")
        
        if self.verbose:
            print(f"✅ VLM OCR Engine initialized")
            print(f"   Model: {model}")
            print(f"   Speed: 750+ tokens/sec")
    
    def _encode_image(self, image: np.ndarray, max_size: int = 1920) -> str:
        """
        Encode image to base64 with compression
        
        Args:
            image: numpy array (RGB format)
            max_size: Max dimension (to keep under 20MB limit)
        
        Returns:
            base64 encoded image string
        """
        # Convert to PIL Image
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        pil_image = Image.fromarray(image)
        
        # Convert RGBA to RGB if needed (JPEG doesn't support alpha)
        if pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')
        
        # Resize if too large
        width, height = pil_image.size
        if max(width, height) > max_size:
            ratio = max_size / max(width, height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            if self.verbose:
                print(f"   Resized: {width}x{height} → {new_width}x{new_height}")
        
        # Encode as JPEG (better compression than PNG)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)
        
        # Base64 encode
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        if self.verbose:
            size_kb = len(img_base64) / 1024
            print(f"   Image size: {size_kb:.1f} KB")
        
        return img_base64
    
    def detect_text_with_boxes(self, image: np.ndarray) -> List[Dict]:
        """
        Detect all text in image using VLM
        
        Args:
            image: numpy array (RGB format)
        
        Returns:
            List of detections (compatible with FastOCREngine format):
            [
                {
                    'text': 'Submit',
                    'confidence': 0.95,
                    'center': (x, y),
                    'bbox': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # Synthetic bbox
                    'width': w,
                    'height': h,
                    'area': w * h
                },
                ...
            ]
            
            Note: bbox, width, height are estimated based on text length
            since VLM doesn't provide exact bounding boxes
        """
        start_time = time.time()
        
        # Encode image
        if self.verbose:
            print("📸 Encoding image...")
        
        img_base64 = self._encode_image(image)
        img_height, img_width = image.shape[:2]
        
        # Prepare prompt
        prompt = f"""You are an OCR system. Analyze this screenshot and extract ALL visible text.

For each text element, provide:
1. The exact text content
2. Approximate position (percentage from top-left): x% and y%
3. Confidence (0.0-1.0)

Return ONLY a JSON array (no markdown, no explanation):
[
  {{"text": "exact text", "x_percent": 25, "y_percent": 10, "confidence": 0.95}},
  ...
]

Image dimensions: {img_width}x{img_height}

Extract ALL text, including buttons, labels, menus, body text, etc."""
        
        # Call Groq API
        if self.verbose:
            print(f"🚀 Calling Groq ({self.model})...")
        
        try:
            import requests
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4096,
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse response
            content = result['choices'][0]['message']['content']
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            detections_raw = json.loads(content)
            
            # Convert to standard format
            detections = []
            for det in detections_raw:
                x_percent = det.get('x_percent', 0)
                y_percent = det.get('y_percent', 0)
                
                # Convert percentage to pixel coordinates
                center_x = int((x_percent / 100.0) * img_width)
                center_y = int((y_percent / 100.0) * img_height)
                
                # Estimate bounding box based on text length
                text = det['text']
                text_len = len(text)
                
                # Rough estimates: 8px per char width, 16px height
                estimated_width = max(text_len * 8, 20)
                estimated_height = 16
                
                # Create synthetic bbox around center point
                x1 = center_x - estimated_width // 2
                y1 = center_y - estimated_height // 2
                x2 = center_x + estimated_width // 2
                y2 = center_y + estimated_height // 2
                
                # Clamp to image bounds
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(img_width, x2)
                y2 = min(img_height, y2)
                
                bbox = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                
                detections.append({
                    'text': text,
                    'confidence': det.get('confidence', 0.9),
                    'center': (center_x, center_y),
                    'bbox': bbox,  # Synthetic bbox for compatibility
                    'width': estimated_width,
                    'height': estimated_height,
                    'area': estimated_width * estimated_height,
                })
            
            elapsed = (time.time() - start_time) * 1000
            
            if self.verbose:
                print(f"✓ VLM detected {len(detections)} text elements in {elapsed:.0f}ms")
            
            return detections
            
        except Exception as e:
            if self.verbose:
                print(f"❌ VLM OCR failed: {e}")
            return []
    
    def find_text(self, 
                  image: np.ndarray, 
                  target_text: str, 
                  fuzzy: bool = True,
                  min_similarity: float = 0.8) -> Optional[Dict]:
        """
        Find specific text in image
        
        Args:
            image: numpy array
            target_text: Text to search for
            fuzzy: Allow fuzzy matching
            min_similarity: Minimum similarity for fuzzy match (0-1)
        
        Returns:
            Best matching detection or None
        """
        detections = self.detect_text_with_boxes(image)
        
        if not fuzzy:
            # Exact match (case-insensitive)
            for det in detections:
                if det['text'].lower().strip() == target_text.lower().strip():
                    return det
            return None
        else:
            # Fuzzy match
            from fuzzywuzzy import fuzz
            
            best_match = None
            best_score = 0
            
            for det in detections:
                score = fuzz.ratio(det['text'].lower(), target_text.lower()) / 100.0
                if score > best_score and score >= min_similarity:
                    best_score = score
                    best_match = det
            
            if best_match:
                best_match['match_similarity'] = best_score
            
            return best_match


def test_vlm_ocr():
    """Test the VLM OCR engine"""
    import pyautogui
    
    print("=" * 70)
    print("VLM OCR Engine Test (Groq Llama 4 Scout)")
    print("=" * 70)
    print()
    
    # Initialize
    print("Initializing VLM OCR engine...")
    ocr = VLMOCREngine(verbose=True)
    
    # Take screenshot
    print("\nCapturing screenshot...")
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    
    # Detect text
    print("\nDetecting text with VLM...")
    detections = ocr.detect_text_with_boxes(screenshot_np)
    
    print(f"\n✅ Found {len(detections)} text elements!")
    print("\nTop 20 detected elements:")
    print("-" * 70)
    
    for i, det in enumerate(detections[:20], 1):
        text_preview = det['text'][:50]
        print(f"{i:2d}. '{text_preview}' at {det['center']} (conf: {det['confidence']:.2f})")
    
    # Test text search
    print("\n" + "=" * 70)
    print("Testing text search...")
    print("=" * 70)
    
    if detections:
        # Search for first detected text
        target = detections[0]['text']
        print(f"\nSearching for: '{target}'")
        
        result = ocr.find_text(screenshot_np, target, fuzzy=False)
        if result:
            print(f"✓ Found exact match at {result['center']}")
        
        # Test fuzzy search
        if len(target) > 5:
            partial = target[:len(target)//2]
            print(f"\nFuzzy search for: '{partial}'")
            
            result = ocr.find_text(screenshot_np, partial, fuzzy=True, min_similarity=0.6)
            if result:
                print(f"✓ Found fuzzy match: '{result['text']}' (similarity: {result.get('match_similarity', 0):.0%})")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_vlm_ocr()

