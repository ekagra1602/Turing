# AgentFlow - Quick Start Guide

Get up and running with AgentFlow in 5 minutes!

## Prerequisites

- macOS (currently required)
- Python 3.8+
- Google Gemini API key
- Terminal access

## Installation

### 1. Install Dependencies

```bash
cd agentflow/backend

# Activate virtual environment (if not already activated)
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

**Note:** This will install ~500MB of packages including computer vision libraries. The first run may take several minutes.

### 2. Set API Key

Get a Gemini API key from: https://makersuite.google.com/app/apikey

```bash
export GOOGLE_API_KEY='your_api_key_here'
```

**Tip:** Add this to your `~/.zshrc` or `~/.bashrc` to persist across sessions.

### 3. Grant Permissions

AgentFlow needs accessibility permissions to control your screen:

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the lock icon and authenticate
3. Click **+** and add **Terminal** (or your terminal app)
4. Enable the checkbox

## First Run

### Test Basic Execution

```bash
python agent_interface.py
```

Try: `"open canvas.asu.edu and open my machine learning class"`

This uses the basic AI-powered execution (no learning yet).

### Test Enhanced Version with Recording

```bash
python agent_enhanced.py
```

You'll see:
```
✅ Enhanced AgentFlow initialized
   - Visual memory enabled
   - Workflow recording enabled
   - Visual analysis enabled
   - Visual execution enabled

💬 
```

## Your First Workflow

Let's teach AgentFlow to open a Canvas class!

### Step 1: Start Recording

```
💬 record
```

Enter details:
```
Workflow name: Open Canvas Class
Description: Navigate to Canvas and open a specific class
Tags: canvas, education
```

You'll see:
```
🔴 RECORDING: Open Canvas Class
======================================================================
Perform your workflow naturally.
I'll watch and learn!

When done, call: recorder.stop_recording()
======================================================================
```

### Step 2: Perform Your Workflow

**Important:** Do these actions slowly and deliberately:

1. Click on your browser (if not already open)
2. Navigate to canvas.asu.edu (if not there)
3. Click on a class (e.g., "Machine Learning")
4. Wait a moment after each action

The system will capture:
- Every click
- Every scroll
- Screenshots before/after each action
- What text you clicked on (using OCR)

### Step 3: Stop Recording

Back in the terminal:
```
💬 stop
```

The system will analyze your recording:
```
⏹  STOPPED RECORDING: Open Canvas Class
======================================================================

Recorded 2 steps

💡 Analyzing workflow for parameters...

📊 Identified Parameters:
  - class_name: Name of the class to open
    Example: Machine Learning

✅ Parameters saved to workflow
```

### Step 4: Use Your Learned Workflow

Now tell AgentFlow to do the same thing for a different class:

```
💬 Open my DataVis class on Canvas
```

The system will:
```
✨ Found matching workflow: Open Canvas Class
   Confidence: 90%
   
   Execute this workflow? [Y/n]: y

🎬 Executing learned workflow: Open Canvas Class
======================================================================

Parameters:
  class_name = DataVis

⚠️  Starting execution in 3 seconds...
DON'T TOUCH YOUR MOUSE OR KEYBOARD!
   3...
   2...
   1...

🤖 Executing workflow...

🔸 Step 1: click
   Looking for: 'Machine Learning'
   Substituted to: 'DataVis'
   Searching with OCR...
   Found: 'DataVis' (similarity: 95%)
   Clicking at (521, 342)

======================================================================
✅ Workflow execution completed
======================================================================
```

**It just did it!** 🎉

## Common Commands

| Command | Description |
|---------|-------------|
| `record` | Start recording a new workflow |
| `stop` | Stop current recording |
| `list` | Show all learned workflows |
| `memory` | Show agent's memory |
| `quit` or `exit` | Exit the program |

## Tips for Better Workflows

### Do's ✅
- **Click deliberately** - Pause between actions
- **Use clear targets** - Click on text labels, not icons
- **Keep it simple** - Record straightforward workflows first
- **Name it well** - Use descriptive workflow names
- **Add good descriptions** - Help matching later

### Don'ts ❌
- **Don't rush** - System needs time to capture screenshots
- **Don't use complex UI** - Avoid custom controls for now
- **Don't record errors** - If you mess up, start over
- **Don't touch mouse during replay** - Let the AI control

## Troubleshooting

### "OCR not working"

If you see warnings about Tesseract or EasyOCR:

```bash
# macOS
brew install tesseract

# Then reinstall Python packages
pip install --force-reinstall pytesseract easyocr
```

### "Accessibility permissions denied"

Make sure you've granted Terminal accessibility permissions (see step 3 above).

### "Element not found during execution"

The system tries multiple strategies:
1. OCR text matching
2. Vision LLM location
3. Fallback to original coordinates

If it fails:
- UI might have changed significantly
- Text might not be visible
- Try recording a new workflow with current UI

### "Workflow execution seems slow"

- OCR takes 1-2 seconds per step
- Vision LLM queries take 2-3 seconds
- This is normal for accuracy

## Examples

### Example 1: Email Workflow

```
💬 record
Workflow name: Send Email to Professor
Description: Compose and send email to course professor
Tags: email, communication

[Perform actions:]
1. Click Gmail
2. Click Compose
3. Type recipient email
4. Type subject
5. Type message
6. Click Send

💬 stop
```

Later:
```
💬 Send email to Dr. Smith about assignment extension
```

### Example 2: File Download

```
💬 record
Workflow name: Download Course Materials
Description: Download files from Canvas course page
Tags: canvas, download

[Perform actions:]
1. Navigate to course
2. Click Files
3. Click on file
4. Click Download

💬 stop
```

Later:
```
💬 Download materials from my DataVis class
```

### Example 3: Research Paper

```
💬 record
Workflow name: Save Paper from arXiv
Description: Download paper and save to Papers folder
Tags: research, papers

[Perform actions:]
1. Go to arXiv URL
2. Click PDF link
3. Save to ~/Papers/

💬 stop
```

Later:
```
💬 Save paper from arxiv.org/abs/2304.12345
```

## Next Steps

- Read [`README.md`](README.md) for full documentation
- Check [`ARCHITECTURE.md`](ARCHITECTURE.md) to understand how it works
- Read [`RESEARCH.md`](RESEARCH.md) for technology deep-dive
- Review [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) for current state

## Get Help

- **Issues?** Check troubleshooting section above
- **Questions?** Read the full docs
- **Bugs?** File an issue on GitHub
- **Ideas?** We'd love to hear them!

## Limitations

Current version (Beta):
- ✅ Records workflows perfectly
- ✅ Identifies parameters automatically
- ✅ Matches user intent to workflows
- ✅ Executes with OCR + Vision guidance
- ⚠️ May struggle with:
  - Very complex UI
  - Custom widgets
  - Fast-changing content
  - Multiple monitors

## What's Next?

After you're comfortable:
1. Record more workflows
2. Try complex multi-step tasks
3. Experiment with different applications
4. Share workflows with team (export/import)
5. Contribute improvements!

---

**Happy Automating! 🚀**

Made with ❤️ for CalHacks 2025

