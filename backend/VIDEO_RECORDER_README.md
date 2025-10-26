# AgentFlow Pro - Video-Based Workflow Recorder

## Overview

**Revolutionary AI-powered workflow automation using pure VLM (Vision Language Model) learning.**

Instead of complex screenshot analysis and OCR, AgentFlow Pro simply **records your screen as video** and uses **Gemini 2.5's video understanding** to learn exactly what you did - like teaching an intern by demonstration.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  VIDEO RECORDER                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Professional Tkinter UI                           │   │
│  │  - Always-on-top overlay                          │   │
│  │  - Real-time recording timer                      │   │
│  │  - One-click record/stop/analyze                  │   │
│  └────────────────────────────────────────────────────┘   │
│                           ↓                               │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Screen Video Capture (opencv + mss)              │   │
│  │  - 10 FPS (perfect for UI recording)              │   │
│  │  - MP4 format                                      │   │
│  │  - Efficient, low resource usage                  │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│              GEMINI VIDEO ANALYSIS                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Upload video to Gemini File API                  │   │
│  └─────────────────────┬──────────────────────────────┘   │
│                        ↓                                   │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Gemini 2.5 Flash watches video and extracts:     │   │
│  │  ✓ Semantic actions (what user did)               │   │
│  │  ✓ Intent (what they wanted to accomplish)        │   │
│  │  ✓ Parameters (values that can vary)              │   │
│  │  ✓ Style notes (how they did it)                  │   │
│  └─────────────────────┬──────────────────────────────┘   │
│                        ↓                                   │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Store workflow with semantic understanding       │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                WORKFLOW EXECUTION                         │
│  Existing GeminiWorkflowExecutor mimics user's style     │
│  using learned semantic actions                          │
└──────────────────────────────────────────────────────────┘
```

## Key Features

### 1. **Pure VLM Learning** 🎥
- No OCR, no complex image processing
- Just record video and let Gemini watch
- Gemini understands context, intent, and style

### 2. **Professional UI** 🎨
- Clean, minimal floating overlay
- Always-on-top, semi-transparent
- Real-time recording timer
- One-click workflow

### 3. **Intelligent Analysis** 🧠
- Gemini identifies semantic actions
- Detects parameterizable values
- Understands user's workflow style
- Generates natural language descriptions

### 4. **Seamless Integration** 🔗
- Works with existing executor
- Compatible with visual memory storage
- Supports Snowflake cloud storage

## Installation

```bash
# 1. Navigate to backend
cd backend/

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements_fast.txt

# 4. Set API key
export GOOGLE_API_KEY='your_gemini_api_key'
# Get key at: https://aistudio.google.com/apikey
```

## Usage

### Quick Start

```bash
# Start the recorder UI
./START_RECORDER.sh

# Or manually:
source venv/bin/activate
python recorder_ui.py
```

### Recording a Workflow

1. **Click "Record"**
   - Enter workflow name
   - Add description (optional)
   - Add tags (optional)

2. **Perform Workflow**
   - Do your task on screen as you normally would
   - The recorder captures everything at 10 FPS
   - No need to think about clicks/coordinates

3. **Click "Stop"**
   - Recording saved as MP4

4. **Click "Analyze"**
   - Video uploaded to Gemini
   - Gemini watches and understands
   - Semantic actions extracted
   - Workflow saved and ready!

### Using Learned Workflows

```python
from intelligent_workflow_system import IntelligentWorkflowSystem

# Initialize system
system = IntelligentWorkflowSystem()

# Execute learned workflow with natural language
system.execute_from_prompt("Open my DataVis class on Canvas")

# System finds matching workflow and adapts it!
```

## File Structure

```
backend/
├── video_recorder.py          # Core screen recording (opencv + mss)
├── video_analyzer.py          # Gemini video analysis
├── recorder_ui.py             # Professional Tkinter UI
├── visual_memory.py           # Workflow storage (unchanged)
├── gemini_workflow_executor.py # Executor (unchanged)
├── intelligent_workflow_system.py # Main interface
├── START_RECORDER.sh          # Quick start script
└── workflows/                 # Stored workflows
    └── {workflow_id}/
        ├── metadata.json      # Workflow info
        ├── recording.mp4      # Original video
        └── steps/             # Extracted semantic actions
```

## Components

### VideoRecorder (`video_recorder.py`)
- Screen capture using `mss` (fast, thread-safe)
- Video encoding with `opencv-python`
- 10 FPS (perfect balance: smooth playback, small files)
- MP4 format with H.264 encoding
- Background recording thread

### VideoWorkflowAnalyzer (`video_analyzer.py`)
- Uploads video to Gemini File API
- Prompts Gemini to analyze workflow
- Extracts semantic actions, parameters, style
- Returns structured JSON

### RecorderUI (`recorder_ui.py`)
- Professional Tkinter overlay
- Dark theme, minimal design
- Real-time status updates
- Workflow management

## Gemini Video Processing

**Capabilities:**
- Up to 1 hour video (Gemini 2.0 Flash)
- 1 FPS processing by default
- ~300 tokens per second of video
- **Cost: ~$0.005 per minute** (basically free!)

**What Gemini Extracts:**
```json
{
  "overall_intention": "Navigate to Canvas and open Machine Learning course",
  "semantic_actions": [
    {
      "step_number": 1,
      "semantic_type": "open_application",
      "description": "User opened Chrome using dock",
      "target": "Chrome",
      "is_parameterizable": false,
      "confidence": 0.95
    },
    {
      "step_number": 2,
      "semantic_type": "navigate",
      "description": "User navigated to canvas.asu.edu",
      "target": "canvas.asu.edu",
      "is_parameterizable": false
    },
    {
      "step_number": 3,
      "semantic_type": "click_element",
      "description": "User clicked on Machine Learning course",
      "target": "Machine Learning",
      "is_parameterizable": true,
      "parameter_name": "course_name",
      "confidence": 0.92
    }
  ],
  "identified_parameters": [
    {
      "name": "course_name",
      "example_value": "Machine Learning",
      "type": "string"
    }
  ],
  "style_notes": "User prefers Chrome browser, uses dock to open apps"
}
```

## Performance

**Recording:**
- 10 FPS at 1080p: ~5-10 MB per minute
- Low CPU usage (background thread)
- No impact on UI responsiveness

**Analysis:**
- Upload time: ~5-10s per minute of video
- Gemini processing: ~10-20s
- Total: ~30s for typical 1-minute workflow

**Execution:**
- Same as before (uses GeminiWorkflowExecutor)
- Vision-guided, adapts to screen

## Testing

### Test Components Individually

```bash
# Test video recorder
python video_recorder.py

# Test video analyzer (requires recorded video)
python video_analyzer.py

# Test full UI
python recorder_ui.py
```

### Test End-to-End

1. Record a simple workflow (e.g., open browser)
2. Analyze with Gemini
3. Check `workflows/` directory for saved workflow
4. Use `intelligent_workflow_system.py` to execute

## Troubleshooting

### "Import cv2 could not be resolved"
```bash
pip install opencv-python
```

### "Import mss could not be resolved"
```bash
pip install mss
```

### "GOOGLE_API_KEY not set"
```bash
export GOOGLE_API_KEY='your_key_here'
# Or add to .env file
```

### Video upload fails
- Check file size (< 100MB recommended)
- Check internet connection
- Verify API key has quota

### UI doesn't appear
- Check if Tkinter is installed: `python -m tkinter`
- On macOS, may need: `brew install python-tk`

## Advantages Over Previous Approach

### Old Way (Screenshot-based):
- ❌ Complex event tracking
- ❌ OCR needed for text
- ❌ Element detection difficult
- ❌ Screenshots pile up quickly
- ❌ Hard to maintain timing info

### New Way (Video-based):
- ✅ Simple screen recording
- ✅ Gemini does ALL analysis
- ✅ Natural timing preserved
- ✅ One video file per workflow
- ✅ Gemini understands context

## Future Enhancements

- [ ] Variable FPS based on activity
- [ ] Region-based recording (specific windows)
- [ ] Real-time action hints during recording
- [ ] Workflow comparison and merging
- [ ] Auto-parameter detection improvements
- [ ] Multi-monitor support

## Credits

Built with:
- **Gemini 2.5 Flash** - Video understanding
- **opencv-python** - Video encoding
- **mss** - Fast screen capture
- **Tkinter** - UI
- **Existing AgentFlow** - Execution engine

## License

Part of the AgentFlow project.
