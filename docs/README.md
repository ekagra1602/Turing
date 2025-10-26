# AgentFlow - Learn by Observation

<img src="https://img.shields.io/badge/Status-Beta-yellow" />
<img src="https://img.shields.io/badge/Python-3.8%2B-blue" />
<img src="https://img.shields.io/badge/Platform-macOS-lightgrey" />

**AgentFlow** is an AI agent that learns by watching you work. Like an intern that shadows you, learns your workflows, and then executes them autonomously.

## 🎯 Vision

Imagine telling your computer:
> "Open my DataVis class on Canvas and clone the notebook"

And it just... does it. Because it watched you do it once for your Machine Learning class.

That's AgentFlow.

## ✨ Features

### 🔴 Record Mode
- Click "record", perform your workflow naturally
- System captures:
  - Every click, scroll, and keystroke
  - Screenshots before/after each action
  - Visual context (what you clicked on)
  - OCR of text elements

### 🧠 Visual Learning
- AI analyzes your recording to understand:
  - What steps you took
  - What the workflow accomplishes
  - Which values are parameters (e.g., class names)
  - Visual signatures of UI elements

### 🔄 Smart Replay
- Tell it what you want in natural language
- System:
  - Finds matching workflow
  - Extracts new parameters from your request
  - Executes workflow with visual guidance
  - Uses OCR to locate elements dynamically

### 📚 Workflow Library
- Store unlimited workflows
- Search by name, description, tags
- Export/import workflow packages
- Track usage statistics

## 🏗️ Architecture

<img width="6821" height="2704" alt="image" src="https://github.com/user-attachments/assets/f72f263a-7462-4162-9c60-3df32068a741" />


```
┌─────────────────────────────────────────────┐
│           User Interface                     │
│  "Open my DataVis class on Canvas"          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     Workflow Matching Engine                │
│  • Find similar learned workflows           │
│  • Extract parameters from user request     │
│  • Calculate confidence score               │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      Visual Memory                          │
│  workflows/                                 │
│    ├── {uuid}/                              │
│    │   ├── metadata.json                    │
│    │   ├── steps/                           │
│    │   │   ├── step_001.json                │
│    │   │   ├── step_001_before.png          │
│    │   │   └── step_001_after.png           │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│   Visual-Guided Execution                   │
│  1. Take screenshot                         │
│  2. Use OCR to find target element          │
│  3. Use Vision LLM to understand UI         │
│  4. Calculate click coordinates             │
│  5. Execute action                          │
│  6. Verify state change                     │
└─────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Navigate to backend directory
cd agentflow/backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Set API Key

```bash
export GOOGLE_API_KEY='your_gemini_api_key_here'
```

### Run Enhanced Agent

```bash
python agent_enhanced.py
```

## 📖 Usage Guide

### Recording a Workflow

1. Start the enhanced agent:
   ```bash
   python agent_enhanced.py
   ```

2. Enter `record` command

3. Provide workflow details:
   ```
   Workflow name: Open Canvas Class
   Description: Navigate to Canvas and open a specific class
   Tags: canvas, education
   ```

4. **Perform your workflow naturally** - the system is watching!
   - Open browser
   - Navigate to canvas.asu.edu
   - Click on your class
   - Do whatever you need to do

5. When done, enter `stop` command

6. System analyzes and identifies parameters:
   ```
   📊 Identified Parameters:
     - class_name: Name of the class to open
       Example: Machine Learning
   
   ✅ Workflow saved!
   ```

### Using a Learned Workflow

Just describe what you want:

```
💬 Open my DataVis class on Canvas

✨ Found matching workflow: Open Canvas Class
   Confidence: 90%
   
   Execute this workflow? [Y/n]: y

🎬 Executing learned workflow...
✅ Done!
```

### List All Workflows

```
💬 list

📚 Learned Workflows:
=================================================================

  Open Canvas Class
  └─ Navigate to Canvas and open a specific class
     Steps: 3 | Uses: 5
     Parameters: class_name
     Tags: canvas, education

  Download Bank Statement
  └─ Log into bank and download statement PDF
     Steps: 8 | Uses: 2
     Parameters: month, year
     Tags: finance, banking
```

## 🛠️ Components

### 1. **visual_memory.py**
Stores workflows with complete visual context.

```python
from visual_memory import VisualWorkflowMemory

memory = VisualWorkflowMemory()

# Create workflow
wf_id = memory.create_workflow(
    name="My Workflow",
    description="What it does",
    tags=["tag1", "tag2"]
)

# Add steps
memory.add_step(
    workflow_id=wf_id,
    action_type='click',
    action_data={'x': 500, 'y': 300},
    screenshot_before=screenshot,
    screenshot_after=screenshot,
    visual_context={'clicked_text': 'Submit'}
)

# Finalize
memory.finalize_workflow(wf_id, parameters=[...])
```

### 2. **recorder.py**
Monitors user actions and captures visual context.

```python
from recorder import WorkflowRecorder

recorder = WorkflowRecorder()

# Start recording
wf_id = recorder.start_recording("My Workflow")

# User performs actions...
# System automatically captures everything

# Stop recording
recorder.stop_recording()
```

### 3. **visual_analyzer.py**
Extracts meaning from screenshots using OCR and computer vision.

```python
from visual_analyzer import VisualAnalyzer

analyzer = VisualAnalyzer()

# Analyze what was clicked
context = analyzer.analyze_click_context(
    screenshot, 
    click_x=500, 
    click_y=300
)

print(context['clicked_text'])  # "Submit Button"

# Find text in screenshot
matches = analyzer.find_text_in_screenshot(
    screenshot,
    target_text="Machine Learning"
)

for match in matches:
    print(f"Found at: {match['center']}")
```

### 4. **agent_enhanced.py**
Main interface with recording and learned execution.

## 🔬 Advanced Topics

### Parameter Identification

The system uses Google's Gemini LLM to analyze workflows and identify parameters:

```
Workflow: Open Canvas Class
Steps:
1. Navigate to https://canvas.asu.edu
2. Click on "Machine Learning"
3. Click on "Assignments"

AI identifies:
- "Machine Learning" is a parameter (varies per class)
- "Assignments" is NOT a parameter (always same)
```

### Visual Element Matching

When executing with new parameters, system uses multiple strategies:

1. **OCR Text Matching**: Find text "DataVis" on screen
2. **Visual Similarity**: Compare to recorded element appearance  
3. **Position Heuristics**: Similar elements often in same region
4. **Vision LLM**: Ask AI "where is the DataVis class link?"

### Confidence Scoring

```python
if confidence > 0.9:
    # Execute automatically
elif confidence > 0.7:
    # Ask for confirmation
else:
    # Ask user to demonstrate
```

## 📊 Storage Format

Workflows are stored as structured directories:

```
workflows/
  ├── 550e8400-e29b-41d4-a716-446655440000/
  │   ├── metadata.json
  │   ├── steps/
  │   │   ├── step_001.json
  │   │   ├── step_001_before.png
  │   │   ├── step_001_after.png
  │   │   ├── step_002.json
  │   │   ├── step_002_before.png
  │   │   └── step_002_after.png
```

**metadata.json**:
```json
{
  "workflow_id": "550e8400-...",
  "name": "Open Canvas Class",
  "description": "Navigate to Canvas and open class",
  "tags": ["canvas", "education"],
  "created": "2025-10-25T10:30:00",
  "status": "ready",
  "steps_count": 3,
  "parameters": [
    {
      "name": "class_name",
      "type": "string",
      "example": "Machine Learning",
      "step": 2,
      "description": "Name of class to open"
    }
  ]
}
```

**step_001.json**:
```json
{
  "step_id": "step_001",
  "step_number": 1,
  "timestamp": 1698234567.89,
  "action_type": "click",
  "action_data": {
    "x": 500,
    "y": 300,
    "normalized_x": 340,
    "normalized_y": 314
  },
  "visual_context": {
    "clicked_text": "Machine Learning",
    "element_type": "link",
    "ocr_confidence": 0.95
  },
  "screenshot_before": "step_001_before.png",
  "screenshot_after": "step_001_after.png"
}
```

## 🎓 Use Cases

### Customer Support
```
Record: "Resolve ticket #1234 for product XYZ"
Execute: "Resolve ticket #5678 for product ABC"
→ System learns ticket resolution workflow
```

### Data Entry
```
Record: "Enter invoice from ACME Corp"
Execute: "Enter invoice from Widget Co"
→ Learns invoice entry pattern
```

### Testing
```
Record: "Test login flow with valid credentials"
Execute: "Test login flow with invalid credentials"
→ Learns UI testing patterns
```

### Research
```
Record: "Download paper from arXiv and save to Papers folder"
Execute: "Download paper [URL] and save to Papers folder"
→ Learns research paper workflow
```

## 🚧 Current Limitations

### In Beta
- **Visual-guided execution**: Core logic implemented, needs refinement
- **OCR accuracy**: Depends on text clarity and font
- **UI variations**: Works best with consistent UI layouts
- **Cross-application**: Currently optimized for web applications

### Coming Soon
- [ ] Advanced visual element matching with ML
- [ ] Support for conditional logic in workflows
- [ ] Workflow editing and debugging tools
- [ ] Multi-monitor support
- [ ] Windows/Linux support
- [ ] Browser extension for better web automation

## 🤝 Contributing

This is research-grade software under active development. Contributions welcome!

Areas of focus:
- Improving OCR accuracy
- Better parameter identification
- Visual element matching algorithms
- Cross-platform support
- UI/UX improvements

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

Built with:
- Google Gemini AI (computer use & vision)
- PyAutoGUI (screen control)
- EasyOCR (text extraction)
- pynput (action monitoring)

Inspired by:
- Robotic Process Automation (RPA) systems
- Programming by Demonstration research
- The dream of truly intelligent assistants

---

## 📚 Documentation

See additional documentation:
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - System architecture and design
- [`RESEARCH.md`](RESEARCH.md) - Deep dive into technologies used
- [`computer_use_simple.py`](computer_use_simple.py) - Core computer control
- [`agent_interface.py`](agent_interface.py) - Original agent interface

---

**Made with ❤️ for CalHacks 2025**

*Teaching computers to learn by watching, one workflow at a time.*

