# AgentFlow: End-to-End Tutorial

## Complete Guide to Recording and Executing Workflows

This tutorial walks you through the entire AgentFlow system - from recording a workflow to executing it with AI.

---

## Part 1: Setup

### Prerequisites

1. **Python 3.9+** installed
2. **ffmpeg** installed (for video recording):
   ```bash
   brew install ffmpeg
   ```
3. **Google API key** with Gemini access

### Installation

```bash
cd backend/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up API key
echo "GOOGLE_API_KEY='your_api_key_here'" > .env
```

### Verify Setup

```bash
# Test video recorder
python video_recorder.py

# Should see:
# ✅ Video Recorder initialized (ffmpeg native capture)
# Recording for 5 seconds...
```

---

## Part 2: Recording Your First Workflow

### Step 1: Launch the Recorder UI

```bash
./START_RECORDER.sh
```

You'll see a floating UI window in the top-right corner:

```
==================================================
🚀 AgentFlow Pro - Video Recorder
==================================================

✅ Video Recorder initialized (ffmpeg native capture)
   Screen device: 3
   FPS: 30
✅ Video Workflow Analyzer initialized
   Model: gemini-2.0-flash-exp
======================================================================
🚀 AgentFlow Recorder Starting
======================================================================
```

### Step 2: Record a Workflow

**Example: Record "Check Canvas Syllabus" workflow**

1. Click **"⏺ Record"** button
2. Enter workflow details:
   - **Name**: `canvas_syllabus`
   - **Description**: `Check syllabus for a course`
   - **Tags**: `canvas, education`
3. Click **"Start Recording"**
4. Perform your workflow:
   - Open browser (Cmd+Space → "Brave")
   - Navigate to `canvas.asu.edu`
   - Click on a course (e.g., "CSE 578: Data Visualization")
   - Click "Syllabus" in sidebar
   - Scroll through syllabus
5. Click **"⏹ Stop"** when done
6. Click **"🧠 Analyze"** to process with Gemini

### Step 3: Wait for Analysis

Gemini will analyze your screen recording:

```
🧠 ANALYZING WORKFLOW VIDEO
======================================================================

📤 Uploading video to Gemini...
   ✓ Uploaded: files/xxx
   ✓ State: FileState.ACTIVE

🎬 Analyzing video with Gemini...

======================================================================
✅ ANALYSIS COMPLETE
======================================================================

Goal: The user is checking the syllabus for a specific course on Canvas.
Actions: 9
Parameters: 1

📋 Semantic Actions:
----------------------------------------------------------------------
1. User opened Brave Browser using Spotlight search
2. User typed 'canvas.asu.edu' into the address bar
3. User navigated to the URL entered in the address bar
4. User clicked on the course 'CSE 578: Data Visualization (2025 Fall C)'
   → Parameter: course_name
5. User clicked on the 'Syllabus' link in the left navigation bar
6. User scrolled down the page to view the syllabus content
...

🎯 Parameters:
----------------------------------------------------------------------
• course_name: CSE 578: Data Visualization (2025 Fall C)
```

**Success!** Your workflow is now learned and ready to execute.

---

## Part 3: Viewing Learned Workflows

### Using the UI

Click **"📚 View Workflows"** in the recorder UI to see all learned workflows:

```
📚 Learned Workflows (2)

1. canvas_syllabus
   The user is checking the syllabus for a specific course on Canvas.
   Steps: 9 | Used: 0 times
   Tags: canvas, education

2. navigate_canvas
   The user is navigating the Canvas website to view the syllabus for a specific course.
   Steps: 4 | Used: 0 times
   Tags: canvas, navigation
```

### Using Python

```python
from visual_memory import VisualWorkflowMemory

memory = VisualWorkflowMemory()
workflows = memory.list_workflows(status='ready')

for wf in workflows:
    print(f"{wf['name']}: {wf['description']}")
    print(f"  Steps: {wf['steps_count']}")
```

---

## Part 4: Executing Workflows

### Method 1: Using the Executor Directly

Create `execute_workflow.py`:

```python
#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory

# Initialize
memory = VisualWorkflowMemory()
executor = GeminiWorkflowExecutor(memory=memory, verbose=True)

# List available workflows
workflows = memory.list_workflows(status='ready')
print("\nAvailable workflows:")
for i, wf in enumerate(workflows, 1):
    print(f"{i}. {wf['name']}: {wf['description']}")

# Choose workflow
choice = int(input("\nSelect workflow (number): ")) - 1
workflow = workflows[choice]

# Get parameters if needed
parameters = {}
if workflow.get('parameters'):
    print("\nThis workflow has parameters:")
    for param in workflow['parameters']:
        print(f"  - {param['name']}: {param['description']}")
        value = input(f"    Enter value for {param['name']}: ")
        parameters[param['name']] = value

# Execute!
print("\n🚀 Executing workflow...\n")
success, results = executor.execute_workflow(workflow, parameters)

if success:
    print("\n✅ Workflow completed successfully!")
else:
    print("\n⚠️ Workflow completed with errors")
```

Run it:
```bash
python execute_workflow.py
```

### Method 2: Using Natural Language (Advanced)

The executor now has ALL workflows loaded in its system prompt!

```python
#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from gemini_workflow_executor import GeminiWorkflowExecutor

# Initialize (workflows automatically loaded)
executor = GeminiWorkflowExecutor(verbose=True)

# Gemini can now see all workflows:
# ✅ Gemini Computer Use initialized
#    Loaded 2 workflows into system context

# The LLM now knows about:
# - "The user is checking the syllabus for a specific course on Canvas."
# - "The user is navigating the Canvas website to view the syllabus for a specific course."

# You can now execute by natural language matching!
user_request = "check the syllabus for Machine Learning course"

# The system prompt contains all workflows
# Gemini will match the request to the appropriate workflow
```

---

## Part 5: Complete Example Workflow

### Scenario: Automate Canvas Syllabus Checking

**Step 1: Record the workflow once**

```bash
./START_RECORDER.sh
```

1. Click Record
2. Name: `canvas_syllabus_checker`
3. Perform the task:
   - Open browser
   - Go to Canvas
   - Click on "CSE 578: Data Visualization"
   - Click "Syllabus"
   - Scroll through
4. Stop and Analyze

**Step 2: Execute for different courses**

Create `check_canvas.py`:

```python
#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory

def check_syllabus(course_name):
    """Check syllabus for any course"""

    # Initialize
    memory = VisualWorkflowMemory()
    executor = GeminiWorkflowExecutor(memory=memory, verbose=True)

    # Find the canvas syllabus workflow
    workflows = memory.list_workflows(status='ready')
    canvas_wf = None

    for wf in workflows:
        if 'syllabus' in wf['description'].lower() and 'canvas' in wf['description'].lower():
            canvas_wf = wf
            break

    if not canvas_wf:
        print("❌ No Canvas syllabus workflow found!")
        print("   Please record one first using START_RECORDER.sh")
        return

    # Execute with new course name
    print(f"\n🎯 Checking syllabus for: {course_name}\n")

    parameters = {'course_name': course_name}
    success, results = executor.execute_workflow(canvas_wf, parameters)

    if success:
        print(f"\n✅ Successfully checked syllabus for {course_name}!")
    else:
        print(f"\n❌ Failed to check syllabus")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python check_canvas.py 'Course Name'")
        print("Example: python check_canvas.py 'Machine Learning'")
        sys.exit(1)

    course = sys.argv[1]
    check_syllabus(course)
```

**Step 3: Run for different courses**

```bash
# Check different courses without repeating manual steps!
python check_canvas.py "Machine Learning"
python check_canvas.py "Data Visualization"
python check_canvas.py "Software Engineering"
```

---

## Part 6: Understanding What Happens Behind the Scenes

### Recording Phase

1. **Video Capture**: ffmpeg records your screen at 30 FPS
2. **Upload to Gemini**: Video sent to Gemini 2.0 Flash
3. **AI Analysis**: Gemini watches the video and extracts:
   - Semantic actions (what you did, not pixel coordinates)
   - Parameters (values that can change)
   - Overall intention (what you were trying to do)
4. **Storage**: Workflow saved to `workflows/{workflow_id}/`
   - `metadata.json` - workflow info
   - `semantic_actions.json` - learned actions
   - `recording.mp4` - original video

### Execution Phase

1. **System Prompt**: All workflows loaded into Gemini's context
2. **Matching**: LLM matches user request to workflow intention
3. **Parameter Substitution**: Replace parameters (e.g., new course name)
4. **Execution**: Gemini uses computer vision to:
   - Find elements on current screen
   - Adapt to layout changes
   - Execute semantic actions

### The Magic: Semantic Understanding

**Old approach** (doesn't work):
- Record: "Click at (542, 301)"
- Execute: Click at (542, 301) → FAILS if window moved!

**New approach** (works):
- Record: "Click on 'CSE 578: Data Visualization' course link"
- Execute: Gemini finds the course link wherever it is → WORKS!

---

## Part 7: Troubleshooting

### Video Recording Issues

**Problem**: Empty or corrupted video files

**Solution**:
```bash
# Verify ffmpeg installation
ffmpeg -version

# Test screen capture
python video_recorder.py

# Check macOS permissions:
# System Preferences → Security & Privacy → Screen Recording
# Make sure Terminal.app has permission
```

### Gemini Analysis Fails

**Problem**: "Error uploading video" or timeout

**Solution**:
```bash
# Check API key
echo $GOOGLE_API_KEY

# Verify file size (should be < 100MB)
ls -lh recordings/*.mp4

# Test Gemini connection
python video_analyzer.py
```

### Workflow Execution Fails

**Problem**: Workflow doesn't execute correctly

**Debug**:
1. Check if workflows are loaded:
   ```python
   executor = GeminiWorkflowExecutor(verbose=True)
   print(executor.workflows_by_intention)
   ```
2. Verify parameters are correct
3. Check macOS Accessibility permissions for terminal
4. Run with `verbose=True` to see detailed logs

---

## Part 8: Advanced Usage

### Recording Multiple Workflows

Record different tasks and the system learns them all:

```bash
# Record workflow 1
./START_RECORDER.sh
# → Record "Submit Canvas assignment"

# Record workflow 2
./START_RECORDER.sh
# → Record "Check course announcements"

# Record workflow 3
./START_RECORDER.sh
# → Record "Download course materials"
```

All workflows are available to the executor:

```python
executor = GeminiWorkflowExecutor(verbose=True)
# ✅ Loaded 3 workflows into system context:
#    • Submit assignment on Canvas
#    • Check announcements for a course
#    • Download materials for a course
```

### Chaining Workflows

Execute multiple workflows in sequence:

```python
executor = GeminiWorkflowExecutor(verbose=True)
workflows = memory.list_workflows(status='ready')

# Execute multiple workflows with same parameter
course = "Machine Learning"

for wf in workflows:
    if 'canvas' in wf.get('tags', []):
        print(f"Executing: {wf['name']}")
        executor.execute_workflow(wf, {'course_name': course})
```

---

## Part 9: Best Practices

### Recording Tips

1. **Go Slow**: Perform actions deliberately, pause between steps
2. **Be Consistent**: Use the same app/workflow path each time
3. **Clear Parameters**: Make it obvious what values could change
4. **Good Names**: Use descriptive workflow names and tags
5. **Test First**: Record a simple workflow first to test the system

### Execution Tips

1. **Same Starting State**: Start from same screen state as recording
2. **Correct Parameters**: Ensure parameter values match expected format
3. **Wait for Loading**: Some web apps need time to load
4. **Error Handling**: Always check return value and results
5. **Verbose Mode**: Use `verbose=True` during development

### System Design Tips

1. **One Task Per Workflow**: Keep workflows focused on single tasks
2. **Reusable Components**: Record common sub-tasks separately
3. **Clear Intentions**: Write clear descriptions that Gemini can understand
4. **Tag Everything**: Use tags for organization and filtering
5. **Version Control**: Keep workflow backups in git

---

## Part 10: Next Steps

### Explore More

- **Intelligent Workflow System**: See `intelligent_workflow_system.py`
- **Workflow Matcher**: See how LLM matches requests to workflows
- **Computer Vision**: Explore Gemini's vision capabilities in `gemini_computer_use.py`

### Build Custom Tools

```python
from gemini_workflow_executor import GeminiWorkflowExecutor
from visual_memory import VisualWorkflowMemory

class MyCustomAutomation:
    def __init__(self):
        self.executor = GeminiWorkflowExecutor(verbose=True)
        self.memory = VisualWorkflowMemory()

    def automate_task(self, task_name, **params):
        """Execute any learned workflow by name"""
        workflows = self.memory.search_workflows(task_name)
        if workflows:
            return self.executor.execute_workflow(workflows[0], params)
        return False

# Use it
bot = MyCustomAutomation()
bot.automate_task("canvas syllabus", course_name="Data Mining")
```

---

## Quick Reference

### File Structure
```
backend/
├── video_recorder.py          # Screen recording
├── video_analyzer.py          # Gemini video analysis
├── recorder_ui.py             # Recording UI
├── gemini_computer_use.py     # Gemini executor (with workflows in prompt)
├── gemini_workflow_executor.py # Workflow execution engine
├── visual_memory.py           # Workflow storage
├── START_RECORDER.sh          # Launch recorder
├── workflows/                 # Stored workflows
│   └── {workflow_id}/
│       ├── metadata.json
│       ├── semantic_actions.json
│       └── recording.mp4
└── recordings/                # Raw recordings
```

### Common Commands

```bash
# Record workflow
./START_RECORDER.sh

# List workflows
python -c "from visual_memory import VisualWorkflowMemory; m = VisualWorkflowMemory(); print(m.list_workflows())"

# Execute workflow
python execute_workflow.py

# Test system
python test_workflows_system_prompt.py
```

### Key Concepts

- **Semantic Actions**: High-level descriptions of what user did (not pixel coords)
- **Parameters**: Values that can vary between executions
- **Intention**: Overall goal of the workflow
- **System Prompt**: All workflows loaded into Gemini's context
- **Visual Execution**: Gemini finds elements visually on current screen

---

## That's It!

You now have a complete AI-powered workflow automation system that:

✅ Records workflows by watching you work
✅ Understands actions semantically (not just coordinates)
✅ Adapts to screen changes automatically
✅ Executes workflows with different parameters
✅ Scales to hundreds of learned workflows

**Go build something amazing!** 🚀
