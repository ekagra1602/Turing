# AgentFlow Backend

**AI-Powered Workflow Automation System**

Record your screen actions once, execute them anywhere with AI adaptation.

---

## What is AgentFlow?

AgentFlow learns workflows by watching you work. Record a screen video of any task, and Gemini AI understands what you did semantically - not just pixel coordinates. Later, execute that workflow with different parameters, and the AI adapts to your current screen.

### Key Features

✅ **Video-Based Learning**: Records screen at 30 FPS, Gemini analyzes your actions
✅ **Semantic Understanding**: Learns "click Submit button" not "click (542, 301)"
✅ **Visual Adaptation**: Finds elements on screen even if layout changes
✅ **Parameterizable**: Execute workflows with different values (course names, etc.)
✅ **System Prompt Integration**: All workflows loaded into AI context automatically
✅ **Professional UI**: Clean Tkinter interface for recording

---

## Quick Start

### 1. Install Dependencies

```bash
# Install ffmpeg
brew install ffmpeg

# Activate venv
source venv/bin/activate

# Set API key
echo "GOOGLE_API_KEY='your_key'" > .env
```

### 2. Record a Workflow

```bash
./START_RECORDER.sh
```

Click Record → Perform your task → Stop → Analyze

### 3. Execute the Workflow

```bash
python execute_workflow.py
```

Select workflow → Enter parameters → Execute!

**📖 See [QUICKSTART.md](QUICKSTART.md) for detailed 5-minute tutorial**

---

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[END_TO_END_TUTORIAL.md](END_TO_END_TUTORIAL.md)** - Complete guide with examples
- **[WORKFLOWS_SYSTEM_PROMPT.md](WORKFLOWS_SYSTEM_PROMPT.md)** - How workflows are loaded into AI
- **[EXECUTOR_WORKFLOWS_DICT.md](EXECUTOR_WORKFLOWS_DICT.md)** - Technical details on workflow dictionary

---

## Architecture

### Recording Pipeline

```
User Action → ffmpeg Screen Capture (30 FPS)
    ↓
Video File (.mp4)
    ↓
Gemini 2.0 Flash (Video Analysis)
    ↓
Semantic Actions + Parameters
    ↓
Visual Memory Storage (workflows/{id}/)
```

### Execution Pipeline

```
User Request → Load All Workflows into System Prompt
    ↓
Gemini Matches Request to Workflow
    ↓
Extract Parameters from Request
    ↓
Execute Semantic Actions:
  - Gemini Computer Use (vision-based)
  - Find elements on current screen
  - Adapt to layout changes
  - Perform actions
```

---

## File Structure

### Core Components

- **video_recorder.py** - Screen recording using ffmpeg native capture
- **video_analyzer.py** - Gemini video analysis for semantic understanding
- **recorder_ui.py** - Professional Tkinter UI for recording
- **gemini_computer_use.py** - Gemini executor with workflows in system prompt
- **gemini_workflow_executor.py** - Workflow execution engine
- **visual_memory.py** - Workflow storage and retrieval
- **intelligent_workflow_system.py** - Main system interface

### Executables

- **START_RECORDER.sh** - Launch recording UI
- **execute_workflow.py** - Interactive workflow execution
- **check_canvas.py** - Example: Canvas automation script

### Tests

- **test_video_recorder.py** - Test screen recording
- **test_workflows_system_prompt.py** - Verify system prompt loading
- **test_executor_workflows.py** - Test workflow dictionary

---

## Example: Canvas Syllabus Automation

### Record Once

```bash
./START_RECORDER.sh
```

1. Record going to Canvas
2. Click on "Data Visualization" course
3. Click "Syllabus"
4. Scroll through syllabus

### Execute Many Times

```bash
python check_canvas.py "Machine Learning"
python check_canvas.py "Software Engineering"
python check_canvas.py "Database Systems"
```

Each execution adapts to find the correct course, no matter where it appears!

---

## How It Works

### 1. Semantic Actions

Instead of recording pixel coordinates, AgentFlow learns semantic actions:

**Bad (old way)**:
```json
{"action": "click", "x": 542, "y": 301}
```
❌ Breaks if window moves or resizes

**Good (AgentFlow way)**:
```json
{
  "semantic_type": "click_element",
  "description": "Click on 'Data Visualization' course link",
  "target": "Data Visualization",
  "is_parameterizable": true,
  "parameter_name": "course_name"
}
```
✅ Works anywhere on screen, with any course name!

### 2. System Prompt Integration

All workflows are loaded into Gemini's system prompt:

```python
executor = GeminiWorkflowExecutor(verbose=True)
# ✅ Loaded 3 workflows into system context:
#    • The user is checking the syllabus for a specific course on Canvas.
#    • The user is submitting an assignment on Canvas.
#    • The user is downloading course materials.
```

The AI can now match natural language requests to workflows automatically!

### 3. Visual Execution

Gemini uses computer vision to find elements:

```python
# Gemini looks at current screen
gemini.click("Submit button")

# Finds button wherever it is
# Adapts to:
# - Different screen resolutions
# - Window positions
# - UI layout changes
```

---

## API Usage

### Basic Usage

```python
from dotenv import load_dotenv
load_dotenv()

from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory

# Initialize (workflows auto-loaded)
executor = GeminiWorkflowExecutor(verbose=True)
memory = VisualWorkflowMemory()

# List workflows
workflows = memory.list_workflows(status='ready')

# Execute workflow
workflow = workflows[0]
parameters = {'course_name': 'Machine Learning'}
success, results = executor.execute_workflow(workflow, parameters)
```

### Advanced: Custom Automation

```python
class CanvasBot:
    def __init__(self):
        self.executor = GeminiWorkflowExecutor(verbose=True)
        self.memory = VisualWorkflowMemory()

    def check_all_syllabi(self, courses):
        """Check syllabus for multiple courses"""
        # Find syllabus workflow
        workflows = self.memory.search_workflows("syllabus")
        syllabus_wf = workflows[0]

        # Execute for each course
        for course in courses:
            print(f"Checking {course}...")
            self.executor.execute_workflow(
                syllabus_wf,
                {'course_name': course}
            )

# Use it
bot = CanvasBot()
bot.check_all_syllabi([
    "Machine Learning",
    "Data Visualization",
    "Software Engineering"
])
```

---

## Key Technologies

- **Python 3.9+** - Core language
- **ffmpeg** - High-quality screen recording (30 FPS, H.264)
- **Gemini 2.0 Flash** - Video analysis and computer vision
- **Tkinter** - Professional recording UI
- **pyautogui** - Low-level keyboard/mouse control
- **mss** - Fast screen capture (unused in final version)

---

## Troubleshooting

### Video Recording Issues

**Empty or small video files**:
```bash
# Verify ffmpeg
ffmpeg -version

# Test screen capture
python video_recorder.py

# Check macOS permissions
# System Prefs → Security → Screen Recording → Terminal
```

### Gemini Analysis Fails

**Upload errors or timeouts**:
```bash
# Verify API key
cat .env

# Check video file size
ls -lh recordings/

# Test analyzer
python video_analyzer.py
```

### Execution Fails

**Workflows don't execute correctly**:
```bash
# Check workflows loaded
python test_workflows_system_prompt.py

# Enable verbose mode
executor = GeminiWorkflowExecutor(verbose=True)

# Verify macOS Accessibility permissions
# System Prefs → Security → Accessibility → Terminal
```

---

## Contributing

This is a demo system optimized for Cal Hacks 2025. Focus areas:

1. **Recording Quality** - Improve video capture on different displays
2. **Semantic Understanding** - Better parameter identification
3. **Visual Execution** - More robust element finding
4. **Error Handling** - Better recovery from failures
5. **UI/UX** - More intuitive recording interface

---

## System Requirements

- **macOS** (tested on macOS 14+)
- **Python 3.9+**
- **ffmpeg** (for screen recording)
- **Google API Key** (Gemini access)
- **Screen Recording Permission** (macOS)
- **Accessibility Permission** (macOS)

---

## Credits

Built for Cal Hacks 2025

**Core Team**:
- Video-based learning pipeline
- Gemini integration
- Semantic action extraction
- Visual execution engine

**Technologies**:
- Google Gemini 2.0 Flash
- ffmpeg screen capture
- Python Tkinter UI

---

## License

MIT License - See LICENSE file

---

## Get Started Now!

```bash
# 1. Record a workflow
./START_RECORDER.sh

# 2. Execute it
python execute_workflow.py

# 3. Build amazing automations!
```

**📖 Read [QUICKSTART.md](QUICKSTART.md) for step-by-step guide**

**📚 Read [END_TO_END_TUTORIAL.md](END_TO_END_TUTORIAL.md) for complete documentation**

---

🚀 **Happy Automating!**
