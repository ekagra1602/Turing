# AgentFlow: Learn-by-Observation Architecture

## Vision

Build an AI agent that **learns by watching** - like an intern that shadows you, learns your workflows, and then executes them autonomously with different parameters.

## Core Concept

```
User demonstrates:
  1. Open canvas.asu.edu
  2. Click "Machine Learning" class
  3. Navigate to "Assignments"
  4. Clone notebook to Jupyter

System learns pattern:
  - Navigate to Canvas
  - Find class with name [PARAMETER]
  - Navigate to section [PARAMETER]
  - Perform action [PARAMETER]

Later, user says: "Do this for DataVis class"
→ System recognizes pattern, substitutes "DataVis" for "Machine Learning", executes workflow
```

## Architecture Components

### 1. **Recording System**
**Purpose**: Capture user actions and visual context during demonstration

**Components**:
- **Screen Recorder**: Continuous screenshot capture (1-2 FPS during demo)
- **Action Tracker**: Monitor mouse clicks, keyboard input, scrolling
- **Event Logger**: Timestamp and sequence all actions
- **Visual State Tracker**: Detect UI changes (page loads, popups, etc.)

**Data Captured**:
```python
{
  "workflow_id": "uuid",
  "name": "Open Canvas Class",
  "timestamp": "2025-10-25T10:30:00",
  "steps": [
    {
      "step_id": 1,
      "timestamp": 0.5,
      "action": {
        "type": "click",
        "x": 500,
        "y": 300,
        "normalized_x": 340,  # 0-1000 scale
        "normalized_y": 314
      },
      "screenshot_before": "base64_image_data",
      "screenshot_after": "base64_image_data",
      "visual_context": {
        "clicked_text": "Machine Learning",
        "clicked_element_type": "link",
        "surrounding_text": ["CSE 475", "Found of Machine Learning", "2025 Fall C"],
        "visual_signature": "base64_cropped_element",
        "ocr_results": {...},
        "url": "https://canvas.asu.edu/courses"
      }
    },
    ...
  ]
}
```

### 2. **Visual Analysis Engine**
**Purpose**: Extract meaning from screenshots and identify clickable elements

**Technologies**:
- **OCR**: Extract text from screenshots (pytesseract, EasyOCR)
- **Vision LLM**: Understand UI layout, identify elements (Gemini Vision, GPT-4V)
- **Object Detection**: Detect buttons, links, input fields
- **Visual Embeddings**: Create searchable representations of UI elements

**Capabilities**:
- Identify what text was clicked
- Detect button/link boundaries
- Understand UI hierarchy
- Create visual "signatures" of elements for matching

### 3. **Pattern Extraction Engine**
**Purpose**: Analyze recorded workflows and identify generalizable patterns

**Process**:
```
Raw Recording → Pattern Extraction → Parameterized Workflow

Example:
Raw: [Click "Machine Learning" at (500, 300)]
↓
Pattern: [Click link matching "Machine Learning" in course list]
↓
Parameterized: [Click link matching {class_name} in course list]
```

**Pattern Types**:
- **Sequential**: Step A → Step B → Step C
- **Conditional**: If see X, then do Y
- **Loops**: Repeat until condition
- **Parameters**: Variable values (class names, search terms, etc.)

**Parameter Detection**:
- Identify varying text (e.g., "Machine Learning" vs "DataVis")
- Detect input values
- Recognize navigation targets

### 4. **Visual Memory Storage**
**Purpose**: Store workflows in a format that enables fast matching and retrieval

**Storage Structure**:
```python
# SQLite + JSON files
workflows/
  ├── {workflow_id}/
  │   ├── metadata.json          # Name, description, tags
  │   ├── pattern.json           # Parameterized workflow
  │   ├── steps/
  │   │   ├── step_001.json      # Action + visual context
  │   │   ├── step_001_before.png
  │   │   ├── step_001_after.png
  │   │   └── step_001_element.png  # Cropped element clicked
  │   └── embeddings.json        # Vector embeddings for matching
```

**Indexing**:
- Text-based: Keywords, descriptions
- Visual-based: Element embeddings
- Action-based: Click sequences, navigation patterns

### 5. **Workflow Matching Engine**
**Purpose**: When user requests task, find most similar recorded workflow

**Matching Strategy**:
```python
User prompt: "Open DataVis class on Canvas"

1. Text Similarity:
   - Extract keywords: ["open", "DataVis", "class", "Canvas"]
   - Match against workflow descriptions
   
2. Semantic Similarity:
   - Use LLM to understand intent
   - Match against workflow purposes
   
3. Pattern Similarity:
   - Identify action pattern (navigate → find → click)
   - Match against recorded patterns

4. Confidence Score:
   - 90%+ : Execute automatically
   - 70-90%: Ask for confirmation
   - <70%: Ask for demonstration
```

### 6. **Execution Engine with Visual Guidance**
**Purpose**: Execute learned workflows with new parameters

**Approach**: **Hybrid Vision + Pattern Matching**

```python
# For each step in workflow:
1. Take current screenshot
2. Use vision LLM to locate target element:
   - "Find a link that says '{class_name}'"
   - Use stored visual signature as reference
   - Use OCR to locate text
3. Calculate coordinates
4. Execute action
5. Verify state change (compare screenshot)
6. Proceed to next step
```

**Robustness**:
- **Visual Matching**: Match element appearance
- **Text Matching**: OCR to find exact text
- **Position Heuristics**: Elements usually in similar regions
- **Retry Logic**: If element not found, scroll or wait
- **Failure Recovery**: Ask user for help if stuck

### 7. **Learning & Adaptation**
**Purpose**: Improve over time

**Strategies**:
- Track success/failure rates
- A/B test different matching strategies
- Learn from corrections
- Cluster similar workflows
- Suggest workflow optimizations

---

## Implementation Phases

### Phase 1: Enhanced Memory System (Current Focus)
- Extend AgentMemory to store visual data
- Add screenshot capture during execution
- Store action sequences with visual context

### Phase 2: Recording Mode
- Add "record" command to UI
- Implement continuous screenshot capture
- Track user actions (read-only, observation)
- Store recordings as structured workflows

### Phase 3: Visual Analysis
- Integrate OCR for text extraction
- Add vision LLM analysis of UI elements
- Create visual signatures for clicked elements
- Build element detection pipeline

### Phase 4: Pattern Extraction
- Analyze recordings to find patterns
- Identify parameters automatically
- Build parameterized workflow templates
- Create workflow metadata for matching

### Phase 5: Workflow Matching
- Implement text-based matching
- Add semantic similarity matching
- Build confidence scoring system
- Create user confirmation flows

### Phase 6: Visual-Guided Execution
- Enhance execution engine with visual search
- Add element location using OCR + vision
- Implement retry and recovery logic
- Add state verification

---

## Technologies & Libraries

### Computer Vision
- **pytesseract / EasyOCR**: Text extraction (OCR)
- **opencv-python**: Image processing, element detection
- **Pillow (PIL)**: Screenshot manipulation
- **numpy**: Image array operations

### Machine Learning
- **Google Gemini Vision**: UI understanding, element identification
- **sentence-transformers**: Text/image embeddings for matching
- **scikit-learn**: Clustering, similarity matching

### Screen Control
- **pyautogui**: Mouse/keyboard control (current)
- **pynput**: Action monitoring during recording
- **Quartz (macOS)**: Low-level screen access

### Storage
- **SQLite**: Workflow metadata and indexes
- **JSON**: Structured workflow data
- **File system**: Screenshots and visual data

### Analysis
- **networkx**: Workflow graph representation
- **difflib**: Pattern similarity
- **fuzzywuzzy**: Fuzzy text matching

---

## Key Challenges & Solutions

### Challenge 1: UI Element Recognition
**Problem**: Same button can look different (hover states, themes, etc.)
**Solution**: 
- Multiple matching strategies (text + position + visual)
- Confidence-based fallback chain
- Store multiple visual signatures per element

### Challenge 2: Parameter Identification
**Problem**: How to know "Machine Learning" is a parameter, not literal text?
**Solution**:
- Compare multiple demonstrations of similar workflow
- Use LLM to analyze what varies vs what's constant
- Let user annotate parameters during recording

### Challenge 3: Workflow Generalization
**Problem**: User demonstrated Canvas workflow, can it work for other LMS?
**Solution**:
- Store abstract patterns ("find course by name") not literal actions
- Use vision LLM to adapt to different UIs
- Build domain-specific pattern libraries

### Challenge 4: Execution Reliability
**Problem**: Pages load at different speeds, elements move
**Solution**:
- Implement retry logic with exponential backoff
- Use visual verification after each step
- Add explicit wait steps in patterns
- Detect loading indicators

---

## Success Metrics

1. **Recording Quality**: Can capture 100% of user actions with visual context
2. **Pattern Accuracy**: 90%+ correct parameter identification
3. **Matching Precision**: 85%+ correct workflow match from natural language
4. **Execution Success**: 90%+ successful workflow execution
5. **Generalization**: Can adapt workflow to similar but different UIs

---

## Example Workflow: "Open Canvas Class"

### Recorded Demonstration
```
User demonstrates:
1. Opens canvas.asu.edu
2. Clicks link "CSE 475: Found of Machine Learning"
3. Clicks "Assignments" tab
4. Clicks "Download" on notebook
```

### Extracted Pattern
```json
{
  "name": "Open Canvas Class and Download Notebook",
  "parameters": {
    "class_name": {
      "type": "string",
      "example": "Machine Learning",
      "location": "step_2"
    },
    "section": {
      "type": "string",
      "example": "Assignments",
      "location": "step_3"
    }
  },
  "pattern": [
    {
      "action": "navigate",
      "url": "https://canvas.asu.edu"
    },
    {
      "action": "click_link",
      "text_contains": "{class_name}",
      "visual_signature": "...",
      "region": "main_content"
    },
    {
      "action": "click_link",
      "text_exact": "{section}",
      "element_type": "tab"
    },
    {
      "action": "click_button",
      "text_contains": "Download",
      "element_type": "button"
    }
  ]
}
```

### Execution with New Parameters
```
User: "Do this for my DataVis class"

System:
1. Matches workflow pattern (95% confidence)
2. Extracts parameter: class_name = "DataVis"
3. Executes:
   - Navigate to Canvas ✓
   - Use vision to find link containing "DataVis" ✓
   - Click found link ✓
   - Find "Assignments" tab (same as recorded) ✓
   - Find "Download" button ✓
```

---

## Next Steps

1. ✅ Fix Gemini API bug (add URL to responses)
2. 🔄 Research visual workflow learning systems
3. 📝 Design enhanced memory storage schema
4. 🛠️ Implement recording mode
5. 🧠 Build visual analysis pipeline
6. 🎯 Create pattern extraction engine
7. 🚀 Build workflow execution with visual guidance

