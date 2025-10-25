# Deep Research: Learn-by-Observation Technologies

## 1. Visual Workflow Learning Systems

### Academic Research

#### Programming by Demonstration (PbD)
- **Concept**: Users demonstrate tasks, system learns and generalizes
- **Key Papers**:
  - "Programming by Demonstration" (Cypher & Halbert, 1993)
  - "Imitation Learning: A Survey" (Hussein et al., 2017)
  - "Visual Programming by Demonstration" (Lieberman, 2001)

#### RPA (Robotic Process Automation)
- **Commercial Systems**: UiPath, Automation Anywhere, Blue Prism
- **How They Work**:
  1. Record user actions in applications
  2. Use UI element detection (accessibility APIs, OCR, image matching)
  3. Create workflows with conditionals and loops
  4. Execute with element selectors

**Key Insight**: Combine multiple detection methods for robustness
- DOM/accessibility tree (for web/apps with APIs)
- OCR for text-based matching
- Image template matching for visual elements
- ML-based element detection

### Existing Open-Source Projects

#### **Selenium IDE** (Web Automation)
- Records browser actions
- Creates test scripts
- Uses CSS/XPath selectors
- **Limitation**: Only works in browsers

#### **PyAutoGUI** (Current in our stack)
- Screen control via coordinates
- **Limitation**: Brittle to UI changes
- **Solution**: Combine with visual recognition

#### **SikuliX** (Visual Automation)
- Uses computer vision to find UI elements
- Template matching with OpenCV
- Can click on images
- **Strength**: Works with any application
- **Limitation**: Requires exact visual matches

#### **TagUI** (RPA Framework)
- Natural language automation
- Multi-modal element detection
- **Strength**: Combines OCR, vision, accessibility APIs

---

## 2. Screen Recording & Action Tracking

### Action Monitoring Libraries

#### **pynput** (Python)
```python
from pynput import mouse, keyboard

def on_click(x, y, button, pressed):
    if pressed:
        # Capture click event
        screenshot = capture_screen()
        save_action({
            'type': 'click',
            'x': x,
            'y': y,
            'timestamp': time.time(),
            'screenshot': screenshot
        })

listener = mouse.Listener(on_click=on_click)
listener.start()
```

**Capabilities**:
- Monitor mouse clicks, movements
- Capture keyboard input
- Non-blocking, runs in background

#### **pyautogui** (Current)
- Can capture screenshots
- Can get mouse position
- Controls input (not just monitoring)

#### **macOS-specific: Quartz**
```python
from Quartz import CGEventTapCreate, kCGEventTapOptionDefault, kCGSessionEventTap

# Lower-level event monitoring
# Can intercept ALL system events
# Requires accessibility permissions
```

### Screen Capture Strategies

#### **Continuous Recording** (Full Demo)
- Capture at 1-2 FPS during demo
- Store all frames
- **Pros**: Complete visual history
- **Cons**: Storage intensive

#### **Event-Triggered** (On Action)
- Only capture screenshot before/after each action
- **Pros**: Efficient storage
- **Cons**: Miss transitions

#### **Hybrid** (Recommended)
- Capture on each action
- Plus periodic captures (every 2 seconds)
- Plus capture on detected UI changes

### UI Change Detection
```python
import imagehash
from PIL import Image

def detect_ui_change(img1, img2, threshold=5):
    """
    Detect if UI changed significantly between screenshots
    """
    hash1 = imagehash.average_hash(img1)
    hash2 = imagehash.average_hash(img2)
    diff = hash1 - hash2
    return diff > threshold
```

---

## 3. OCR & Text Extraction

### OCR Libraries Comparison

#### **Tesseract (pytesseract)**
```python
import pytesseract
from PIL import Image

image = Image.open('screenshot.png')
text = pytesseract.image_to_string(image)
boxes = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
```

**Pros**:
- Free, widely used
- Supports 100+ languages
- Good for printed text

**Cons**:
- Slower than modern alternatives
- Struggles with small text, unusual fonts

#### **EasyOCR**
```python
import easyocr

reader = easyocr.Reader(['en'])
results = reader.readtext('screenshot.png')
# Returns: [([[x1,y1], [x2,y2], ...], 'text', confidence), ...]
```

**Pros**:
- Better accuracy than Tesseract
- Returns bounding boxes
- Deep learning based

**Cons**:
- Requires GPU for speed (CPU slow)
- Larger model size

#### **Apple Vision Framework** (macOS)
```python
import Vision
import Quartz

# Native macOS OCR - extremely fast and accurate
```

**Pros**:
- Native to macOS
- Extremely fast
- Excellent accuracy
- Built into OS

**Cons**:
- macOS only

#### **Recommendation**: Use Apple Vision (primary) + EasyOCR (fallback)

### Advanced Text Detection

#### **Finding Clickable Text**
```python
def find_clickable_text(screenshot, target_text):
    """
    Find location of clickable text in screenshot
    """
    # 1. OCR to get all text with bounding boxes
    results = reader.readtext(screenshot)
    
    # 2. Find matches
    matches = []
    for (bbox, text, conf) in results:
        if target_text.lower() in text.lower() and conf > 0.7:
            # Calculate center of bounding box
            x_center = sum([p[0] for p in bbox]) / 4
            y_center = sum([p[1] for p in bbox]) / 4
            matches.append({
                'text': text,
                'x': x_center,
                'y': y_center,
                'bbox': bbox,
                'confidence': conf
            })
    
    return matches
```

---

## 4. Object Detection & UI Element Recognition

### Approaches

#### **Traditional Computer Vision** (OpenCV)
```python
import cv2

def detect_buttons(screenshot):
    """
    Detect rectangular buttons using edge detection
    """
    gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    buttons = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h
        # Buttons typically have certain aspect ratios
        if 1.5 < aspect_ratio < 4 and w > 50 and h > 20:
            buttons.append((x, y, w, h))
    
    return buttons
```

**Pros**: Fast, no ML needed
**Cons**: Brittle to different UI styles

#### **Template Matching**
```python
def find_template(screenshot, template):
    """
    Find template image in screenshot
    """
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val > 0.8:  # High confidence match
        return max_loc
    return None
```

**Use Case**: Finding previously seen UI elements
**Limitation**: Exact pixel matching required

#### **Vision LLM for UI Understanding** (Gemini Vision, GPT-4V)
```python
def locate_element_with_vision_llm(screenshot, description):
    """
    Use vision LLM to understand UI and locate element
    """
    prompt = f"""
    Analyze this screenshot. I want to click on: {description}
    
    Provide:
    1. The exact text of the element
    2. The approximate coordinates (0-1000 scale) where I should click
    3. The type of element (button, link, input, etc.)
    4. Confidence (0-100%)
    
    Format:
    TEXT: [exact text]
    X: [0-1000]
    Y: [0-1000]
    TYPE: [element type]
    CONFIDENCE: [0-100]
    """
    
    response = vision_llm.analyze(screenshot, prompt)
    return parse_response(response)
```

**Pros**: 
- Understands context
- Works with varied UIs
- Can reason about element purpose

**Cons**:
- API costs
- Slower than traditional CV
- Need to validate coordinates

#### **Hybrid Approach** (Recommended)
```python
def smart_element_locator(screenshot, target_description, visual_signature=None):
    """
    Multi-strategy element location
    """
    candidates = []
    
    # Strategy 1: Template matching (if we have signature)
    if visual_signature:
        match = find_template(screenshot, visual_signature)
        if match:
            candidates.append(('template', match, confidence=0.95))
    
    # Strategy 2: OCR text matching
    text_matches = find_clickable_text(screenshot, target_description)
    for match in text_matches:
        candidates.append(('ocr', match, confidence=match['confidence']))
    
    # Strategy 3: Vision LLM
    llm_result = locate_element_with_vision_llm(screenshot, target_description)
    if llm_result['confidence'] > 70:
        candidates.append(('llm', llm_result, confidence=llm_result['confidence']/100))
    
    # Pick best candidate
    if not candidates:
        return None
    
    best = max(candidates, key=lambda x: x[2])
    return best[1]
```

---

## 5. Pattern Extraction & Workflow Generalization

### Pattern Recognition Techniques

#### **Sequence Mining**
```python
from collections import defaultdict

def extract_common_patterns(workflows):
    """
    Find common action sequences across multiple workflows
    """
    sequences = []
    for workflow in workflows:
        seq = [step['action_type'] for step in workflow['steps']]
        sequences.append(seq)
    
    # Find common subsequences
    pattern_counts = defaultdict(int)
    for seq in sequences:
        for length in range(2, len(seq)):
            for i in range(len(seq) - length + 1):
                pattern = tuple(seq[i:i+length])
                pattern_counts[pattern] += 1
    
    # Return patterns that appear in multiple workflows
    common_patterns = {
        pattern: count 
        for pattern, count in pattern_counts.items() 
        if count > 1
    }
    
    return common_patterns
```

#### **Parameter Identification with LLM**
```python
def identify_parameters(workflow, llm):
    """
    Use LLM to analyze workflow and identify variable parameters
    """
    workflow_description = format_workflow_for_analysis(workflow)
    
    prompt = f"""
    Analyze this recorded workflow and identify which values are likely parameters 
    (i.e., could change between executions):
    
    {workflow_description}
    
    For each parameter, provide:
    1. Parameter name
    2. Example value from this recording
    3. Type (text, number, url, etc.)
    4. Location in workflow (which step)
    5. Description of what it represents
    
    Format as JSON.
    """
    
    response = llm.generate(prompt)
    parameters = json.loads(response)
    
    return parameters
```

#### **Visual Abstraction**
```python
def create_visual_abstraction(clicked_element_image):
    """
    Create abstract representation of UI element that can match variations
    """
    # 1. Extract color histogram
    hist = cv2.calcHist([clicked_element_image], [0,1,2], None, [8,8,8], [0,256,0,256,0,256])
    hist = cv2.normalize(hist, hist).flatten()
    
    # 2. Extract edge features (shape)
    edges = cv2.Canny(clicked_element_image, 100, 200)
    edge_density = edges.sum() / edges.size
    
    # 3. Extract text (if any)
    text = pytesseract.image_to_string(clicked_element_image)
    
    # 4. Compute visual embedding (using pretrained model)
    embedding = visual_encoder.encode(clicked_element_image)
    
    return {
        'color_hist': hist,
        'edge_density': edge_density,
        'text': text,
        'embedding': embedding,
        'size': clicked_element_image.shape
    }
```

### Workflow Generalization

#### **Abstract Syntax Tree for Workflows**
```python
class WorkflowAST:
    """
    Abstract representation of workflow that can be instantiated with parameters
    """
    def __init__(self):
        self.nodes = []
    
    def add_action(self, action_type, **kwargs):
        node = {
            'type': action_type,
            'params': kwargs
        }
        self.nodes.append(node)
    
    def instantiate(self, parameters):
        """
        Create concrete workflow from abstract one with parameters filled in
        """
        instantiated = []
        for node in self.nodes:
            concrete_node = node.copy()
            # Replace parameter placeholders with actual values
            for key, value in concrete_node['params'].items():
                if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                    param_name = value[1:-1]
                    if param_name in parameters:
                        concrete_node['params'][key] = parameters[param_name]
            instantiated.append(concrete_node)
        return instantiated

# Example usage:
workflow = WorkflowAST()
workflow.add_action('navigate', url='https://canvas.asu.edu')
workflow.add_action('click_link', text_contains='{class_name}')
workflow.add_action('click_tab', text='{section_name}')

# Later, instantiate with specific parameters:
concrete = workflow.instantiate({
    'class_name': 'DataVis',
    'section_name': 'Assignments'
})
```

---

## 6. Visual Memory & Embeddings

### Creating Searchable Visual Memory

#### **Image Embeddings with CLIP**
```python
import torch
from transformers import CLIPProcessor, CLIPModel

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def create_visual_embedding(image, text_description):
    """
    Create multimodal embedding of UI element
    """
    inputs = processor(
        text=[text_description],
        images=image,
        return_tensors="pt",
        padding=True
    )
    
    outputs = model(**inputs)
    
    return {
        'image_embedding': outputs.image_embeds[0].detach().numpy(),
        'text_embedding': outputs.text_embeds[0].detach().numpy(),
        'combined': (outputs.image_embeds[0] + outputs.text_embeds[0]).detach().numpy()
    }

def find_similar_elements(query_embedding, stored_embeddings, threshold=0.8):
    """
    Find visually similar elements using cosine similarity
    """
    from sklearn.metrics.pairwise import cosine_similarity
    
    similarities = cosine_similarity([query_embedding], stored_embeddings)[0]
    matches = [(i, sim) for i, sim in enumerate(similarities) if sim > threshold]
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches
```

#### **Vector Database for Fast Retrieval**
```python
# Using FAISS for fast similarity search
import faiss
import numpy as np

class VisualMemoryIndex:
    def __init__(self, dimension=512):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
    
    def add(self, embedding, metadata):
        """Add visual embedding to index"""
        embedding_np = np.array([embedding]).astype('float32')
        self.index.add(embedding_np)
        self.metadata.append(metadata)
    
    def search(self, query_embedding, k=5):
        """Find k most similar elements"""
        query_np = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_np, k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                results.append({
                    'metadata': self.metadata[idx],
                    'distance': dist,
                    'similarity': 1 / (1 + dist)
                })
        
        return results
```

---

## 7. Workflow Matching & Retrieval

### Natural Language to Workflow Matching

#### **Semantic Similarity**
```python
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

def match_user_intent_to_workflow(user_prompt, workflows):
    """
    Match user's natural language request to stored workflows
    """
    # Create embedding for user prompt
    prompt_embedding = model.encode(user_prompt, convert_to_tensor=True)
    
    # Create embeddings for workflow descriptions
    workflow_descriptions = [
        f"{w['name']}: {w['description']}" 
        for w in workflows
    ]
    workflow_embeddings = model.encode(workflow_descriptions, convert_to_tensor=True)
    
    # Compute similarities
    similarities = util.cos_sim(prompt_embedding, workflow_embeddings)[0]
    
    # Get best matches
    matches = []
    for i, similarity in enumerate(similarities):
        if similarity > 0.5:  # Threshold
            matches.append({
                'workflow': workflows[i],
                'similarity': float(similarity),
                'confidence': float(similarity) * 100
            })
    
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    return matches
```

#### **Parameter Extraction from Prompt**
```python
def extract_parameters_from_prompt(prompt, workflow, llm):
    """
    Extract parameter values from user's natural language prompt
    """
    required_params = workflow['parameters']
    
    extraction_prompt = f"""
    The user said: "{prompt}"
    
    Extract the following parameters:
    {json.dumps(required_params, indent=2)}
    
    Return a JSON object with parameter values. If a parameter can't be found, use null.
    """
    
    response = llm.generate(extraction_prompt)
    extracted = json.loads(response)
    
    return extracted
```

---

## 8. Implementation Strategy

### Phase 1: Enhanced Visual Memory (Week 1)
```python
# Add to current system:
1. Screenshot capture before/after each action
2. Store with action metadata
3. Basic OCR for text extraction
4. Simple parameter identification
```

### Phase 2: Recording Mode (Week 2)
```python
# New recording module:
1. Monitor user actions with pynput
2. Capture screenshots on each action
3. Store sequence with timestamps
4. Basic workflow saving
```

### Phase 3: Visual Analysis (Week 3)
```python
# Enhanced vision capabilities:
1. Integrate Apple Vision / EasyOCR
2. Element detection and cropping
3. Visual signature creation
4. Embedding generation
```

### Phase 4: Pattern Extraction (Week 4)
```python
# Intelligence layer:
1. Analyze recorded workflows
2. Identify parameters with LLM
3. Create abstract workflow templates
4. Build pattern database
```

### Phase 5: Smart Execution (Week 5)
```python
# Visual-guided execution:
1. Match user prompt to workflow
2. Extract parameters
3. Execute with visual element location
4. Retry and recovery logic
```

---

## 9. Technology Stack Summary

### Core Libraries
```
# Computer Vision
opencv-python==4.8.1.78        # Image processing
pytesseract==0.3.10            # OCR (fallback)
easyocr==1.7.0                 # Modern OCR
pillow==10.1.0                 # Image manipulation
imagehash==4.3.1               # Perceptual hashing

# Machine Learning
sentence-transformers==2.2.2   # Text embeddings
transformers==4.35.0           # CLIP, other models
torch==2.1.0                   # PyTorch backend
faiss-cpu==1.7.4              # Fast similarity search
scikit-learn==1.3.2           # Clustering, metrics

# Screen Control & Monitoring
pyautogui==0.9.54             # Current screen control
pynput==1.7.6                 # Action monitoring
pyobjc-framework-Quartz       # macOS screen access
pyobjc-framework-Vision       # Apple Vision API

# Storage & Analysis
networkx==3.2                 # Workflow graphs
fuzzywuzzy==0.18.0           # Fuzzy matching
python-Levenshtein==0.23.0   # String distance
```

### APIs
```
- Google Gemini Vision API (UI understanding)
- Google Gemini 2.5 Computer Use (current execution)
- Optional: OpenAI GPT-4V (alternative vision)
```

### Storage
```
- SQLite: Workflow metadata, indexes
- JSON: Workflow definitions
- PNG: Screenshots
- NPY: Numpy arrays (embeddings)
```

---

## 10. Key Research Insights

### What Makes This Hard
1. **UI Variability**: Same button can look different (themes, sizes, states)
2. **Dynamic Content**: Element positions change
3. **Timing**: Pages load at different speeds
4. **Generalization**: Learning from one example vs. many
5. **Error Recovery**: What to do when element not found

### What Makes This Possible (2025)
1. **Vision LLMs**: Can understand UI semantically
2. **Fast OCR**: Apple Vision, EasyOCR are production-ready
3. **Multimodal Embeddings**: CLIP enables visual-semantic matching
4. **Robust Screen Control**: PyAutoGUI + visual guidance
5. **Powerful Hardware**: M-series Macs can run vision models locally

### Success Factors
1. **Multiple Fallbacks**: Never rely on single detection method
2. **Confidence Scoring**: Know when to ask for help
3. **Visual + Semantic**: Combine appearance and meaning
4. **User Feedback Loop**: Learn from corrections
5. **Domain Patterns**: Build libraries for common workflows (web, desktop, etc.)

---

## Next: Implementation Plan

With this research complete, we can now build:
1. Enhanced memory system with visual storage
2. Recording mode with action monitoring
3. Visual analysis pipeline
4. Pattern extraction engine
5. Smart execution with visual guidance

Each component builds on solid, proven technologies while pushing the boundaries of what's possible with learn-by-observation systems.

