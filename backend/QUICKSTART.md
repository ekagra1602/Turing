# AgentFlow Quick Start Guide

Get up and running with AI-powered workflow automation in 5 minutes.

---

## 1️⃣ Setup (2 minutes)

```bash
cd backend/

# Install ffmpeg for screen recording
brew install ffmpeg

# Activate virtual environment (should already exist)
source venv/bin/activate

# Make sure .env has your API key
echo "GOOGLE_API_KEY='your_key_here'" > .env
```

---

## 2️⃣ Record a Workflow (2 minutes)

```bash
# Launch the recorder UI
./START_RECORDER.sh
```

A floating window appears in the top-right:

1. Click **"⏺ Record"**
2. Enter:
   - **Name**: `my_first_workflow`
   - **Description**: `Test workflow`
3. Click **"Start Recording"**
4. Do something simple:
   - Open Spotlight (Cmd+Space)
   - Type "Calculator"
   - Press Enter
5. Click **"⏹ Stop"**
6. Click **"🧠 Analyze"**

Wait ~30 seconds for Gemini to analyze the video.

**Result**: Workflow learned! ✅

---

## 3️⃣ Execute the Workflow (1 minute)

```bash
# Interactive execution
python execute_workflow.py
```

Follow the prompts:
1. Select your workflow (type `1`)
2. Confirm execution (type `y`)

Watch it execute! 🚀

---

## 📚 What You Just Built

You created a system that:
- Records what you do on screen
- Uses AI to understand your actions
- Can repeat those actions automatically

---

## 🎯 Try a Real Example

### Record: Check Canvas Syllabus

1. Launch recorder: `./START_RECORDER.sh`
2. Click Record
3. Name it: `canvas_syllabus`
4. Perform the task:
   - Open browser
   - Go to canvas.asu.edu (or your school's Canvas)
   - Click on any course
   - Click "Syllabus" in sidebar
   - Scroll down a bit
5. Stop and Analyze

### Execute for Different Courses

```bash
# Check syllabus for different courses
python check_canvas.py "Machine Learning"
python check_canvas.py "Data Visualization"
python check_canvas.py "Software Engineering"
```

Each time, it finds the course and opens its syllabus automatically! 🎓

---

## 🔧 Troubleshooting

### "ffmpeg not found"
```bash
brew install ffmpeg
```

### "GOOGLE_API_KEY not set"
```bash
echo "GOOGLE_API_KEY='your_actual_key'" > .env
```

### "No workflows found"
Make sure you clicked "Analyze" after recording!

### "Permission denied"
System Preferences → Security & Privacy → Privacy → Accessibility
→ Add Terminal and check the box

---

## 📖 Full Documentation

See **END_TO_END_TUTORIAL.md** for complete documentation including:
- Advanced features
- Best practices
- Troubleshooting
- API usage
- System architecture

---

## 🚀 What's Next?

**View all learned workflows:**
```bash
python execute_workflow.py
```

**See workflows in system prompt:**
```bash
python test_workflows_system_prompt.py
```

**Record more workflows:**
```bash
./START_RECORDER.sh
```

**Build custom automation:**
```python
from gemini_workflow_executor import GeminiWorkflowExecutor

executor = GeminiWorkflowExecutor(verbose=True)
# All workflows loaded automatically!
# Gemini can match natural language to workflows
```

---

## 💡 Key Concepts

- **Recording**: Capture your screen actions as video
- **Analysis**: Gemini watches video and learns semantic actions
- **Execution**: AI adapts and executes on current screen
- **Parameters**: Values that can change (course names, etc.)
- **System Prompt**: All workflows loaded into AI context

---

## 📝 File Structure

```
backend/
├── START_RECORDER.sh           # Launch recorder UI
├── execute_workflow.py         # Execute any workflow
├── check_canvas.py             # Example: Canvas automation
├── video_recorder.py           # Screen recording
├── video_analyzer.py           # Gemini video analysis
├── recorder_ui.py              # Recording UI
├── gemini_workflow_executor.py # Execution engine
├── workflows/                  # Stored workflows
│   └── {id}/
│       ├── metadata.json
│       ├── semantic_actions.json
│       └── recording.mp4
└── recordings/                 # Raw recordings
```

---

## ✨ That's It!

You now have a working AI automation system.

**Record. Analyze. Execute. Repeat.** 🔄

For questions and detailed docs, see **END_TO_END_TUTORIAL.md**
