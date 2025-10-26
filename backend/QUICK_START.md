# AgentFlow Pro - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### 1. Setup (One-Time)

```bash
# Navigate to backend
cd backend/

# Activate virtual environment
source venv/bin/activate

# Set your Gemini API key
export GOOGLE_API_KEY='your_key_here'
# Get one at: https://aistudio.google.com/apikey
```

### 2. Record a Workflow

```bash
# Start the recorder UI
./START_RECORDER.sh
```

In the UI:
1. Click **"⏺ Record"**
2. Enter workflow name (e.g., "Open GitHub")
3. Click **"Start Recording"**
4. **Perform your workflow** on screen (e.g., open Chrome, go to GitHub)
5. Click **"⏹ Stop"** when done
6. Click **"🧠 Analyze"** - Gemini will watch your video and learn!

### 3. Execute the Workflow

```python
# In a Python shell:
from intelligent_workflow_system import IntelligentWorkflowSystem

system = IntelligentWorkflowSystem()

# Execute your learned workflow
system.execute_from_prompt("Open GitHub")

# Or use variations:
system.execute_from_prompt("Go to GitHub repo")
```

The system will:
- Find your recorded "Open GitHub" workflow
- Adapt it to the current screen
- Execute using the same style you demonstrated

## 📝 Example Workflows

### Simple: Open an Application
1. **Record**: "Open Chrome"
   - Click Record
   - Use Spotlight/Raycast to open Chrome
   - Click Stop → Analyze

2. **Execute**:
   ```python
   system.execute_from_prompt("Open Chrome")
   ```

### Moderate: Navigate to Website
1. **Record**: "Go to GitHub"
   - Open Chrome
   - Type "github.com" in address bar
   - Press Enter
   - Stop → Analyze

2. **Execute**:
   ```python
   system.execute_from_prompt("Go to GitHub")
   ```

### Advanced: Parameterized Workflow
1. **Record**: "Open Canvas class"
   - Go to canvas.asu.edu
   - Click on "Machine Learning" course
   - Stop → Analyze

2. **Execute** (Gemini auto-detects course_name parameter):
   ```python
   system.execute_from_prompt("Open DataVis class on Canvas")
   # Gemini understands to substitute "DataVis" for "Machine Learning"
   ```

## 🎯 Best Practices

### During Recording:
- ✅ **Go slow** - Give Gemini time to see each action
- ✅ **Be deliberate** - Make clear clicks, don't rush
- ✅ **Keep it simple** - 5-10 steps max for first workflows
- ✅ **One workflow = one goal** - Don't mix multiple tasks

### Naming Workflows:
- ✅ Descriptive: "Download Canvas assignment"
- ✅ Specific: "Open GitHub repo"
- ❌ Too generic: "Do stuff"
- ❌ Too long: "Navigate to website and then click on the thing..."

### For Parameterization:
- Use **specific values** during recording
- Examples:
  - Course name: "Machine Learning" → Gemini learns this is a parameter
  - Ticket ID: "ABC-123" → Gemini recognizes pattern
  - Search term: "React tutorials" → Can vary later

## 🔧 Troubleshooting

### "Module not found" errors
```bash
source venv/bin/activate
pip install -r requirements_fast.txt
```

### Recording doesn't start
- Check macOS Accessibility permissions
- System Preferences → Security & Privacy → Accessibility
- Add Terminal (or your terminal app)

### Analysis fails
- Check GOOGLE_API_KEY is set: `echo $GOOGLE_API_KEY`
- Check internet connection
- Try shorter video (< 1 minute for testing)

### UI doesn't appear
```bash
python -m tkinter
# Should show test window. If error:
brew install python-tk@3.12  # or your Python version
```

## 📊 What Gets Stored

After recording + analyzing a workflow named "Open GitHub":

```
workflows/
  └── <workflow_id>/
      ├── metadata.json           # Name, description, tags
      ├── recording.mp4          # Your original screen recording
      └── steps/
          └── step_001.json      # Gemini's semantic understanding
```

## 💡 Pro Tips

1. **Start Simple**: Record opening an app first, then build up

2. **Use Tags**: Tag workflows (e.g., "canvas", "github", "jira")
   ```python
   # Later filter by tag:
   system.memory.list_workflows(tags=['canvas'])
   ```

3. **Check Workflows**: View learned workflows anytime
   ```python
   system.list_workflows()
   ```

4. **Parameter Detection**: Gemini automatically finds parameters!
   - Record: "Search for React tutorials"
   - Execute: "Search for Python guides"
   - Gemini understands "Python guides" replaces "React tutorials"

5. **Interactive Mode**: Try the full demo
   ```bash
   python intelligent_workflow_system.py --demo
   ```

## 🎬 What's Happening Behind the Scenes

When you click **"Analyze"**:

1. **Upload**: Video sent to Gemini File API
2. **Gemini Watches**:
   - "User opened Chrome using dock"
   - "User typed 'github.com' in address bar"
   - "User pressed Enter"
3. **Extract Semantics**:
   - Action: open_application(Chrome)
   - Action: type_text("github.com", target="address bar")
   - Action: key_press(Enter)
4. **Store**: Workflow saved with semantic actions

When you execute:

1. **Match**: Find similar workflow ("Open GitHub")
2. **Extract Params**: Parse request for values
3. **Execute**: Use GeminiWorkflowExecutor to:
   - Find Chrome on THIS screen (vision-guided)
   - Find address bar on THIS browser
   - Type and press Enter

**Result**: Same workflow, adapted to YOUR screen!

## 🚀 Next Steps

Now that you have the basics:

1. Record 3-5 simple workflows
2. Try executing them with variations
3. Experiment with parameters
4. Build complex workflows (10-15 steps)
5. Chain workflows together

## 📚 Full Documentation

- `VIDEO_RECORDER_README.md` - Detailed technical docs
- `CLAUDE.md` - Project overview
- `intelligent_workflow_system.py` - Main API

## 🎉 You're Ready!

Run `./START_RECORDER.sh` and start teaching your AI intern!
