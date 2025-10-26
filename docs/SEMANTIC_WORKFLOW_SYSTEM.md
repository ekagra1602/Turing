# Semantic Workflow System

## 🎯 Overview

The **Semantic Workflow System** is an intelligent automation framework that learns from demonstrations and executes tasks adaptively. It's like having an intern that shadows you, understands what you do, and can repeat it in new contexts.

## 🧠 Key Innovation: Semantic Understanding

### ❌ OLD: Dumb Replay
```
Step 1: key_press('c')
Step 2: key_press('h')
Step 3: key_press('r')
Step 4: key_press('o')
Step 5: key_press('m')
Step 6: key_press('e')
Step 7: key_press(enter)
Step 8: click(450, 320)
```

**Problems:**
- Breaks if screen resolution changes
- Can't adapt to UI changes
- No understanding of intent
- Not generalizable

### ✅ NEW: Semantic Understanding
```
Action 1: open_application("Chrome")
Action 2: click_element("Machine Learning", type="course_link")
```

**Benefits:**
- ✅ Resolution-independent
- ✅ Adapts to UI changes (Gemini finds elements)
- ✅ Understands intent
- ✅ Parameterizable (course name can change)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│ 1. RECORD                                           │
│    - User performs actions                          │
│    - System captures: clicks, keystrokes, scrolls   │
│    - Screenshots saved before/after each action     │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 2. ANALYZE (Semantic Action Analyzer)               │
│    - Groups raw actions into logical units          │
│    - Uses Gemini Vision to understand intent        │
│    - Identifies clicked elements                    │
│    - Detects typed text and context                 │
│    - Generates semantic action sequence             │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 3. STORE (Visual Workflow Memory)                   │
│    - Saves both raw + semantic actions              │
│    - Identifies parameters (course names, etc.)     │
│    - Creates searchable embeddings                  │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 4. MATCH (Semantic Workflow Matcher)                │
│    - User provides natural language prompt          │
│    - Finds similar workflows via embeddings         │
│    - Returns ranked matches                         │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 5. EXECUTE (Gemini Workflow Executor)               │
│    - Uses SEMANTIC actions (not raw replay!)        │
│    - Gemini Computer Use finds elements             │
│    - Adapts to current screen state                 │
│    - Applies parameter substitutions                │
└─────────────────────────────────────────────────────┘
```

## 📚 Components

### 1. **SemanticActionAnalyzer** (`semantic_action_analyzer.py`)
Transforms raw recorded actions into semantic understanding.

**Example Transformations:**
```python
# Raw: cmd+space, type "chrome", enter
# Semantic: open_application("Chrome")

# Raw: click(450, 320)
# Semantic: click_element("Machine Learning", element_type="course_link")

# Raw: type('c'), type('s'), type('e')
# Semantic: type_text("cse", target="search_box")
```

**Key Methods:**
- `analyze_workflow()` - Main entry point
- `_group_actions()` - Groups consecutive key presses
- `_identify_clicked_element_with_gemini()` - Uses vision to identify elements
- `_identify_parameters()` - Detects parameterizable values

### 2. **GeminiWorkflowExecutor** (`gemini_workflow_executor.py`)
Executes workflows using semantic actions + Gemini vision.

**Semantic Action Types:**
- `open_application` - Launch apps via Spotlight
- `click_element` - Find and click using Gemini vision
- `type_text` - Type into fields
- `scroll` - Scroll page

**Parameter Substitution:**
```python
# Learned: click_element("Machine Learning")
# Execute: click_element("Data Visualization")  # Parameter substituted!
```

### 3. **VisualWorkflowMemory** (`visual_memory.py`)
Stores workflows with both raw and semantic actions.

**Storage Structure:**
```
workflows/
  └── {workflow_id}/
      ├── metadata.json           # Name, desc, tags, parameters
      ├── semantic_actions.json   # High-level actions
      └── steps/
          ├── step_001.json       # Raw action
          ├── step_001_before.png
          ├── step_001_after.png
          └── ...
```

### 4. **SemanticWorkflowMatcher** (`semantic_workflow_matcher.py`)
Finds similar workflows using embeddings.

**Example:**
```python
User: "Download assignment for Data Mining class"
Matches:
  1. "canvas cse475 download" (85% similarity)
  2. "canvas download hw" (72% similarity)
```

### 5. **IntelligentWorkflowSystem** (`intelligent_workflow_system.py`)
Main orchestrator that ties everything together.

## 🎮 Usage

### Recording a Workflow

```python
from intelligent_workflow_system import IntelligentWorkflowSystem

system = IntelligentWorkflowSystem()

# Start recording
workflow_id = system.record_workflow(
    "Download Canvas Assignment",
    description="Open Canvas, navigate to ML class, download notebook"
)

# Perform your workflow...
# System watches and learns!

# Stop recording
system.stop_recording()
# → Automatically analyzes and generates semantic actions
```

### Executing with Prompts

```python
# Execute similar task with different parameters
system.execute_from_prompt("Download Canvas assignment for Data Mining class")

# System will:
# 1. Find similar workflow ("Download Canvas Assignment")
# 2. Extract parameter: course_name = "Data Mining"
# 3. Execute adapted workflow using Gemini vision
```

### Interactive Mode

```bash
python workflow_cli.py
# or
./start_fast_computer_use.sh  # Choose option 1
```

## 🎯 Real-World Examples

### Example 1: Close Jira Tickets

**Record Once:**
```
1. Open Chrome
2. Navigate to Jira
3. Click ticket "BUG-123"
4. Click "Close" button
5. Select "Fixed" resolution
6. Click "Confirm"
```

**Execute Many:**
```
"Close ticket BUG-456"  → Adapts to BUG-456
"Close ticket BUG-789"  → Adapts to BUG-789
```

### Example 2: Canvas Assignments

**Record Once:**
```
1. Open Chrome
2. Go to Canvas
3. Click "Machine Learning" course
4. Click "Assignments"
5. Download "Homework 3"
```

**Execute Many:**
```
"Download Canvas assignment for Data Visualization"
"Download Canvas assignment for Data Mining"
```

### Example 3: Job Applications

**Record Once:**
```
1. Open browser
2. Go to job site
3. Click "Software Engineer at Google"
4. Fill application fields
5. Upload resume
6. Submit
```

**Execute Many:**
```
"Apply to Software Engineer at Meta"
"Apply to ML Engineer at OpenAI"
```

## 🔬 Technical Details

### Semantic Action Format

```json
{
  "semantic_type": "click_element",
  "target": "Machine Learning",
  "element_type": "course_link",
  "description": "Click Machine Learning course link",
  "coordinates": {"x": 450, "y": 320},
  "parameterizable": ["course_name"],
  "raw_steps": [15, 16, 17]
}
```

### Parameter Detection

Parameters are automatically identified when:
- Element text varies between executions
- User provides different values in prompt
- Element is marked as `parameterizable`

### Gemini Integration

**Element Identification:**
```python
# Gemini analyzes screenshot + click coordinates
# Returns: element name, type, description
"Clicked on 'Machine Learning' course link"
```

**Element Location:**
```python
# Gemini finds element by description
gemini.click("Machine Learning course")
# → Adapts to current UI layout
```

## 🚀 Performance

- **Recording:** Real-time, no performance impact
- **Analysis:** ~5-10 seconds per workflow (one-time)
- **Matching:** <100ms (using embeddings)
- **Execution:** Depends on Gemini API (~1-2s per action)

## 🔮 Future Enhancements

1. **Multi-step reasoning** - Chain multiple workflows
2. **Conditional logic** - "If X, then Y"
3. **Error recovery** - Retry with different strategies
4. **Cross-application** - Workflows spanning multiple apps
5. **Voice control** - "Do the Canvas thing for my Data Viz class"
6. **Workflow composition** - Combine learned workflows

## 📖 References

- Gemini 2.5 Flash Computer Use: Native screen understanding
- Sentence Transformers: Semantic similarity matching
- Visual Workflow Memory: Context-aware storage
- Parameter Extraction: LLM-based identification

## 🤝 Contributing

This is a research prototype. Key areas for improvement:
- Better parameter detection
- More robust error handling
- Support for more action types
- Cross-platform support (Windows, Linux)

---

**Built with ❤️ for CalHacks 2025**

