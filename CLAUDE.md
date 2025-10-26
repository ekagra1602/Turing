# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentFlow is a dual-purpose macOS automation tool:

1. **Basic/Pro Mode** (root `/src`): Simple GUI overlay for recording and replaying user interactions (clicks, keyboard, movements)
2. **Backend AI Agent** (`/backend`): Advanced AI-powered system that learns workflows by observation using Google Gemini for visual analysis and natural language understanding

## Core Architecture

### Two Independent Systems

**GUI Frontend** (`/src`):
- `minimal_overlay.py` - Basic mode: click-only recording with instant replay
- `enhanced_overlay.py` - Pro mode: full interaction recording (movements, keyboard, scrolling, drag-drop)
- `action_recorder.py` / `action_player.py` - Basic recording/playback engine
- `enhanced_recorder.py` / `enhanced_player.py` - Pro recording/playback with timing
- `window_manager.py` - Window state management utilities

**AI Backend** (`/backend`):
- `agent_enhanced.py` - Main conversational interface with learn-by-observation capabilities
- `visual_memory.py` - Stores workflows with screenshots and visual context in structured directories
- `recorder.py` - Monitors user actions and captures visual context during demonstrations
- `visual_analyzer.py` - OCR and computer vision for extracting UI element information
- `agent_interface.py` - Base agent with Gemini integration for computer control
- `computer_use_simple.py` - Core computer control implementation using Gemini

### Visual Workflow Storage Format

Workflows are stored as structured directories under `workflows/`:
```
workflows/{workflow_id}/
  ├── metadata.json          # Name, description, tags, parameters
  ├── steps/
  │   ├── step_001.json      # Action data + visual context
  │   ├── step_001_before.png
  │   └── step_001_after.png
```

The `metadata.json` contains workflow metadata including identified parameters (values that can vary between executions, e.g., class names). The system uses Gemini LLM to automatically identify parameters by analyzing recorded workflows.

### Parameter Identification System

The backend uses AI to analyze workflows and identify which values are parameters (variables) vs constants:
- Recorded workflow steps include visual context (clicked text, OCR results, element types)
- After recording, Gemini analyzes the workflow description to identify parameters
- Parameters are stored with name, type, example value, step number, and description
- During execution, the system extracts parameter values from natural language requests

## Development Commands

### GUI Frontend (Basic/Pro Mode)

```bash
# Launch basic mode (clicks only, fast)
./start_basic.sh

# Launch pro mode (full interactions: movements, keyboard, drags)
./start_pro.sh

# Both scripts auto-create venv_gui and install dependencies on first run
# Dependencies: pyautogui, pynput, pillow

# Test coordinate accuracy
./venv_gui/bin/python tools/test_click_accuracy.py

# Calibrate coordinate system (if clicks go to wrong places)
./venv_gui/bin/python tools/calibrate.py

# Run diagnostics
./venv_gui/bin/python tools/diagnose.py
```

### AI Backend

```bash
# Navigate to backend
cd backend/

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export GOOGLE_API_KEY='your_gemini_api_key_here'

# Run enhanced agent
python agent_enhanced.py

# Available commands in agent:
#   - 'record' - Start recording a new workflow
#   - 'stop' - Stop recording
#   - 'list' - Show learned workflows
#   - 'memory' - See agent memory
#   - Or natural language: "Open my DataVis class on Canvas"
```

## Key Technical Details

### Coordinate System

The GUI frontend uses a normalized coordinate system (0-1000 scale) to handle different screen resolutions. The `calibration.json` file stores calibration data. On Retina displays or multi-monitor setups, calibration may be needed.

### Visual Matching Strategies

The backend uses multiple strategies for finding UI elements during workflow execution:
1. **OCR Text Matching** - Find exact text on screen using EasyOCR/pytesseract
2. **Visual Similarity** - Compare to recorded element appearance using OpenCV
3. **Position Heuristics** - Similar elements often in same screen region
4. **Vision LLM** - Ask Gemini "where is the X element?" with screenshot

### Workflow Execution Flow

1. User demonstrates workflow (e.g., "Open Canvas class")
2. System captures screenshots before/after each action + visual context
3. Gemini analyzes workflow to identify parameters (e.g., class name)
4. User later requests: "Do this for DataVis class"
5. System matches request to learned workflow, extracts new parameters
6. Executes workflow using visual guidance to locate elements with OCR + Vision LLM

## macOS Permissions

Both systems require **Accessibility permissions**:
1. System Preferences → Security & Privacy → Privacy → Accessibility
2. Add Terminal (or your terminal app)
3. Restart the application

Without these permissions, mouse/keyboard control will fail with "not trusted" errors.

## Testing

### GUI Frontend
- `tools/test_basic.py` - Test basic recording
- `tools/test_click_accuracy.py` - Validate coordinate accuracy
- `tools/test_coordinates.py` - Test coordinate normalization
- `tools/quick_test.sh` - Quick validation script

### Backend
- `backend/test_screen_control.py` - Test screen control capabilities
- `backend/check_permissions.py` - Verify accessibility permissions

## Important Notes

### When modifying the GUI frontend:
- Recording logic is split: basic mode uses `action_recorder.py`, pro mode uses `enhanced_recorder.py`
- Always test coordinate accuracy after changes - use `tools/calibrate.py`
- The overlay is always-on-top and semi-transparent; position is top-right corner
- Basic mode stores only click coordinates; pro mode stores full event streams with timing

### When modifying the backend:
- All visual analysis depends on screenshot quality and OCR accuracy
- Workflow parameter identification is AI-powered and may need refinement
- Visual-guided execution is partially implemented (simulated in current version)
- The system stores base64-encoded screenshots in JSON - keep file sizes in mind
- Memory storage uses both JSON files and directory structure (not SQLite despite architecture docs mentioning it)

### Security Considerations
- Pro mode keyboard recording captures EVERYTHING typed (including passwords)
- All recordings are stored locally - nothing is sent to external servers (except Gemini API calls for backend)
- Backend sends screenshots to Gemini API for visual analysis
- Warn users not to record/share sensitive data

## Common Issues

1. **Clicks go to wrong places**: Run `./venv_gui/bin/python tools/calibrate.py`
2. **"Not trusted" error**: Grant Accessibility permissions
3. **Import errors**: Run start scripts which auto-install dependencies
4. **Backend workflow execution fails**: Visual-guided execution is not fully implemented yet (marked as TODO in agent_enhanced.py:286)
