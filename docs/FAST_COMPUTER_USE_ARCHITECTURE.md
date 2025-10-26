# AgentFlow FAST Computer Use - Architecture

## 🚀 October 2025: Next-Generation Computer Use System

**Problem:** Gemini 2.5 Pro is slow for real-time computer use
**Solution:** Fast LLM (Groq) + Fast Vision + Advanced OCR + Set-of-Marks Grounding

---

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    USER REQUEST                              │
│        "Click on the Submit button"                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         ORCHESTRATOR (Fast LLM - Groq)                       │
│   • Parse user intent                                        │
│   • Determine action sequence                                │
│   • Generate search strategies                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           VISUAL ANALYSIS PIPELINE                           │
│                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌─────────────┐     │
│   │ SCREENSHOT   │→ │ SET-OF-MARKS │→ │ MULTI-MODAL │     │
│   │  CAPTURE     │  │   OVERLAY    │  │  ANALYSIS   │     │
│   └──────────────┘  └──────────────┘  └─────────────┘     │
│                                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                ┌──────┴──────┐
                │             │
                ▼             ▼
┌──────────────────────┐  ┌──────────────────────┐
│  FAST OCR + BBOX     │  │  VISUAL GROUNDING    │
│  (PaddleOCR/RapidOCR)│  │  (VLM if needed)     │
│  • Text location     │  │  • Element detection │
│  • Bounding boxes    │  │  • Visual similarity │
│  • Confidence scores │  │  • Semantic matching │
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           └────────┬────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│         COORDINATE NORMALIZATION & FUSION                    │
│   • Combine OCR + Vision results                            │
│   • Calculate precise click coordinates                      │
│   • Normalize to 0-1000 scale (resolution independent)      │
│   • Multi-strategy ranking (confidence weighted)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            ROBUST ACTION EXECUTOR                            │
│   • Retry logic with exponential backoff                    │
│   • Pre-action screenshot                                    │
│   • Post-action verification                                 │
│   • Fallback strategies                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Orchestrator (Fast LLM - Groq)

**Model:** `llama-3.3-70b-versatile` via Groq API

**Why Groq:**
- Ultra-fast inference (10-100x faster than cloud APIs)
- OpenAI-compatible API
- Excellent for reasoning and task decomposition

**Responsibilities:**
- Parse natural language commands
- Decompose complex tasks into steps
- Generate search strategies for UI elements
- Handle context and conversational state

**Example:**
```python
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def parse_user_command(user_input: str, screenshot_analysis: dict) -> dict:
    """Use Groq LLM to understand user intent and generate action plan"""
    
    prompt = f"""You are a computer use assistant. Analyze this command and screenshot data.

User Command: "{user_input}"

Screenshot contains these elements:
{screenshot_analysis}

Generate an action plan in JSON:
{{
  "action_type": "click|type|drag|scroll",
  "target_element": "description of what to find",
  "search_strategies": ["strategy1", "strategy2"],
  "parameters": {{}}
}}
"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500
    )
    
    return response.choices[0].message.content
```

---

### 2. Set-of-Marks Visual Grounding

**Technique:** Overlay numbered labels on UI elements (inspired by Anthropic Claude Computer Use)

**How it works:**
1. Take screenshot
2. Run fast OCR to detect all text regions
3. Overlay numbered boxes/circles on detected elements
4. Feed annotated screenshot to vision model (or use coordinates directly)
5. Model can refer to elements by number: "Click element #42"

**Benefits:**
- **Accuracy:** Precise coordinate extraction
- **Speed:** Vision model doesn't need to describe positions
- **Reliability:** Numbers are unambiguous references

**Implementation:**
```python
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_set_of_marks(screenshot: Image.Image, ocr_results: list) -> tuple:
    """
    Overlay numbered marks on UI elements
    
    Returns:
        annotated_image: Screenshot with numbered overlays
        element_map: {mark_id: {bbox, text, center, ...}}
    """
    img = screenshot.copy()
    draw = ImageDraw.Draw(img, 'RGBA')
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    
    element_map = {}
    
    for idx, detection in enumerate(ocr_results, start=1):
        bbox = detection['bbox']  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        text = detection['text']
        confidence = detection['confidence']
        
        # Calculate center
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        center_x = int(np.mean(x_coords))
        center_y = int(np.mean(y_coords))
        
        # Draw semi-transparent box around element
        draw.polygon(bbox, outline=(255, 0, 0, 180), width=2)
        
        # Draw numbered circle
        circle_radius = 12
        circle_bbox = [
            center_x - circle_radius,
            center_y - circle_radius,
            center_x + circle_radius,
            center_y + circle_radius
        ]
        draw.ellipse(circle_bbox, fill=(255, 0, 0, 200), outline=(255, 255, 255, 255))
        
        # Draw number
        number_text = str(idx)
        draw.text((center_x - 5, center_y - 8), number_text, fill=(255, 255, 255), font=font)
        
        # Store in element map
        element_map[idx] = {
            'text': text,
            'bbox': bbox,
            'center': (center_x, center_y),
            'confidence': confidence,
            'mark_id': idx
        }
    
    return img, element_map
```

---

### 3. Fast OCR with Bounding Boxes

**Primary Choice:** **PaddleOCR** or **RapidOCR**

**Why these over Tesseract/EasyOCR:**
- **PaddleOCR:** SOTA accuracy, fast inference, excellent bounding boxes
- **RapidOCR:** Even faster, good for real-time (based on PaddleOCR)
- **DeepSeek-OCR:** Context-aware, but may be overkill for UI text

**Comparison:**

| OCR Engine | Speed | Accuracy | Bounding Boxes | Best For |
|------------|-------|----------|----------------|----------|
| PaddleOCR | Fast | Excellent | ✅ Precise | UI automation |
| RapidOCR | Fastest | Very Good | ✅ Good | Real-time |
| DeepSeek-OCR | Medium | Excellent | ✅ Excellent | Complex docs |
| Tesseract | Slow | Good | ⚠️ Basic | Legacy |
| EasyOCR | Medium | Good | ✅ Good | Multilingual |

**Implementation:**
```python
from paddleocr import PaddleOCR

class FastOCREngine:
    def __init__(self):
        # Initialize PaddleOCR (downloads models on first run)
        self.ocr = PaddleOCR(
            use_angle_cls=True,  # Detect text angle
            lang='en',           # Primary language
            use_gpu=True,        # Use GPU if available
            show_log=False
        )
    
    def detect_text_with_boxes(self, image: np.ndarray) -> list:
        """
        Run OCR and return all detected text with bounding boxes
        
        Returns:
            [
                {
                    'text': 'Submit',
                    'bbox': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
                    'confidence': 0.95,
                    'center': (x, y)
                },
                ...
            ]
        """
        result = self.ocr.ocr(image, cls=True)
        
        detections = []
        for line in result[0]:
            bbox = line[0]  # 4 corner points
            text_info = line[1]
            text = text_info[0]
            confidence = text_info[1]
            
            # Calculate center point
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))
            
            detections.append({
                'text': text,
                'bbox': bbox,
                'confidence': confidence,
                'center': (center_x, center_y),
                'width': max(x_coords) - min(x_coords),
                'height': max(y_coords) - min(y_coords)
            })
        
        return detections
```

---

### 4. Coordinate Normalization

**Problem:** Screen resolutions vary (1920x1080, 2560x1440, 3840x2160, etc.)
**Solution:** Normalize to 0-1000 coordinate system

**Benefits:**
- Resolution-independent workflows
- Easier to reason about positions ("middle of screen" = 500, 500)
- Compatible with vision models that output normalized coords

**Implementation:**
```python
class CoordinateNormalizer:
    """Handle conversion between pixel and normalized coordinates"""
    
    def __init__(self):
        self.screen_width, self.screen_height = self._get_screen_size()
    
    def _get_screen_size(self) -> tuple:
        """Get current screen resolution"""
        import pyautogui
        return pyautogui.size()
    
    def normalize(self, x: int, y: int) -> tuple:
        """Convert pixel coordinates to 0-1000 scale"""
        norm_x = int((x / self.screen_width) * 1000)
        norm_y = int((y / self.screen_height) * 1000)
        return (norm_x, norm_y)
    
    def denormalize(self, norm_x: int, norm_y: int) -> tuple:
        """Convert 0-1000 coordinates back to pixels"""
        x = int((norm_x / 1000) * self.screen_width)
        y = int((norm_y / 1000) * self.screen_height)
        return (x, y)
    
    def normalize_bbox(self, bbox: list) -> list:
        """Normalize a bounding box (4 corner points)"""
        return [self.normalize(p[0], p[1]) for p in bbox]
```

---

### 5. Multi-Strategy Element Location

**Strategy Chain** (in order of preference):

1. **Exact Text Match (OCR)**
   - Confidence > 90%
   - Fastest, most reliable

2. **Fuzzy Text Match (OCR + Fuzzy)**
   - Similarity > 80%
   - Handles typos, slight variations

3. **Visual Grounding (Set-of-Marks + LLM)**
   - Use Groq LLM to map description → mark ID
   - Example: "Submit button" → "Element #42"

4. **Position Heuristic (Fallback)**
   - Use normalized coordinates from recording
   - Works when UI is similar

5. **User Prompt (Recovery)**
   - If all fail, show annotated screenshot
   - Ask user: "Which element? (Click or enter mark #)"

**Implementation:**
```python
class MultiStrategyLocator:
    def __init__(self, ocr_engine, llm_client, normalizer):
        self.ocr = ocr_engine
        self.llm = llm_client
        self.normalizer = normalizer
    
    def locate_element(self, screenshot: Image.Image, target_desc: str, fallback_coords=None):
        """
        Try multiple strategies to find element
        
        Returns:
            (x, y, confidence, strategy_used)
        """
        # Strategy 1: Exact OCR match
        ocr_results = self.ocr.detect_text_with_boxes(np.array(screenshot))
        exact_match = self._find_exact_text(ocr_results, target_desc)
        if exact_match and exact_match['confidence'] > 0.9:
            return exact_match['center'] + (exact_match['confidence'], 'ocr_exact')
        
        # Strategy 2: Fuzzy OCR match
        fuzzy_match = self._find_fuzzy_text(ocr_results, target_desc)
        if fuzzy_match and fuzzy_match['similarity'] > 0.8:
            return fuzzy_match['center'] + (fuzzy_match['similarity'], 'ocr_fuzzy')
        
        # Strategy 3: Set-of-marks + LLM
        annotated_img, element_map = create_set_of_marks(screenshot, ocr_results)
        mark_id = self._query_llm_for_mark(annotated_img, element_map, target_desc)
        if mark_id and mark_id in element_map:
            element = element_map[mark_id]
            return element['center'] + (0.85, 'visual_grounding')
        
        # Strategy 4: Position fallback
        if fallback_coords:
            x, y = self.normalizer.denormalize(*fallback_coords)
            return (x, y, 0.5, 'position_fallback')
        
        # Strategy 5: Failed
        return (None, None, 0.0, 'not_found')
    
    def _find_exact_text(self, ocr_results, target):
        """Find exact text match (case-insensitive)"""
        for det in ocr_results:
            if det['text'].lower().strip() == target.lower().strip():
                return det
        return None
    
    def _find_fuzzy_text(self, ocr_results, target):
        """Find best fuzzy match"""
        from fuzzywuzzy import fuzz
        best_match = None
        best_score = 0
        
        for det in ocr_results:
            score = fuzz.ratio(det['text'].lower(), target.lower()) / 100.0
            if score > best_score:
                best_score = score
                best_match = det
        
        if best_match:
            best_match['similarity'] = best_score
        return best_match
    
    def _query_llm_for_mark(self, annotated_img, element_map, target_desc):
        """Ask LLM: which mark ID matches the description?"""
        # Convert element_map to text description
        elements_text = "\n".join([
            f"#{mark_id}: '{info['text']}' at {info['center']}"
            for mark_id, info in element_map.items()
        ])
        
        prompt = f"""You are analyzing a screenshot with numbered UI elements.

Elements:
{elements_text}

User wants to interact with: "{target_desc}"

Which element number matches best? Respond with ONLY the number, or "NONE" if no match.
"""
        
        # Query Groq LLM
        response = self.llm.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )
        
        try:
            mark_id = int(response.choices[0].message.content.strip())
            return mark_id
        except:
            return None
```

---

### 6. Robust Action Executor

**Features:**
- Pre-action screenshot
- Post-action verification
- Retry with exponential backoff
- Fallback strategies
- Detailed logging

**Implementation:**
```python
import time
import pyautogui
from PIL import ImageChops

class RobustActionExecutor:
    def __init__(self, locator, normalizer):
        self.locator = locator
        self.normalizer = normalizer
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def execute_click(self, target_desc: str, fallback_coords=None) -> dict:
        """
        Execute click with verification and retry
        
        Returns:
            {
                'success': bool,
                'location': (x, y),
                'strategy': str,
                'attempts': int,
                'ui_changed': bool
            }
        """
        for attempt in range(1, self.max_retries + 1):
            # Take pre-action screenshot
            screenshot_before = pyautogui.screenshot()
            
            # Locate element
            x, y, confidence, strategy = self.locator.locate_element(
                screenshot_before, target_desc, fallback_coords
            )
            
            if x is None:
                if attempt < self.max_retries:
                    print(f"❌ Attempt {attempt} failed: element not found. Retrying...")
                    time.sleep(self.retry_delay * attempt)
                    continue
                else:
                    return {
                        'success': False,
                        'error': 'Element not found after retries',
                        'attempts': attempt
                    }
            
            print(f"✓ Found element at ({x}, {y}) using {strategy} (confidence: {confidence:.0%})")
            
            # Execute click
            pyautogui.click(x, y)
            
            # Wait for UI to settle
            time.sleep(0.5)
            
            # Take post-action screenshot
            screenshot_after = pyautogui.screenshot()
            
            # Verify UI changed
            ui_changed = self._detect_change(screenshot_before, screenshot_after)
            
            return {
                'success': True,
                'location': (x, y),
                'strategy': strategy,
                'confidence': confidence,
                'attempts': attempt,
                'ui_changed': ui_changed
            }
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    def execute_drag_drop(self, start_desc: str, end_desc: str) -> dict:
        """Execute drag and drop action"""
        # Locate start element
        screenshot = pyautogui.screenshot()
        start_x, start_y, conf1, strat1 = self.locator.locate_element(screenshot, start_desc)
        
        if start_x is None:
            return {'success': False, 'error': 'Start element not found'}
        
        # Locate end element
        end_x, end_y, conf2, strat2 = self.locator.locate_element(screenshot, end_desc)
        
        if end_x is None:
            return {'success': False, 'error': 'End element not found'}
        
        # Execute drag
        pyautogui.moveTo(start_x, start_y)
        time.sleep(0.2)
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=0.5)
        time.sleep(0.5)
        
        return {
            'success': True,
            'start': (start_x, start_y),
            'end': (end_x, end_y),
            'start_strategy': strat1,
            'end_strategy': strat2
        }
    
    def _detect_change(self, img1: Image.Image, img2: Image.Image, threshold=5):
        """Detect if UI changed between screenshots"""
        import imagehash
        hash1 = imagehash.average_hash(img1)
        hash2 = imagehash.average_hash(img2)
        return (hash1 - hash2) > threshold
```

---

## Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| LLM Response Time | < 500ms | Groq ultra-fast |
| OCR Processing | < 200ms | PaddleOCR optimized |
| Total Locate Time | < 1s | Fast enough for real-time |
| Click Accuracy | > 95% | Multi-strategy approach |
| Resolution Independence | ✅ | 0-1000 normalization |

---

## Comparison: Old vs New System

| Aspect | Old (Gemini 2.5 Pro) | New (Groq + Fast OCR) |
|--------|----------------------|-----------------------|
| LLM Speed | 3-10s | < 0.5s |
| Vision Analysis | Gemini Vision (slow) | PaddleOCR (fast) + Optional VLM |
| Accuracy | Good | Excellent (multi-strategy) |
| Cost | High (vision API) | Lower (mostly OCR) |
| Offline Mode | ❌ | Partial (OCR local) |
| Drag & Drop | Basic | Precise (dual-location) |

---

## Next Steps

1. ✅ Architecture design (THIS DOCUMENT)
2. ⏳ Implement FastOCREngine with PaddleOCR
3. ⏳ Build Set-of-Marks visual grounding
4. ⏳ Integrate Groq LLM
5. ⏳ Create MultiStrategyLocator
6. ⏳ Build RobustActionExecutor
7. ⏳ Test and benchmark
8. ⏳ Update main agent_video.py to use new system

---

## Dependencies

```txt
# Fast LLM
groq>=0.4.0

# Fast OCR
paddleocr>=2.7.0
# OR
rapidocr-onnxruntime>=1.3.0

# Optional: Advanced OCR
# deepseek-ocr  # If we need context-aware OCR

# Existing
pyautogui
pillow
numpy<2
opencv-python==4.8.1.78
imagehash
fuzzywuzzy
python-Levenshtein
```

---

**Status:** Ready for implementation
**Owner:** @agentflow-team
**Date:** October 26, 2025

