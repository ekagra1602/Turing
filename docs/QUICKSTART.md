# AgentFlow - Quick Start Guide

## Installation Complete!

All dependencies are installed and the application is ready to use.

## Running AgentFlow

### Run the Floating Overlay:

```bash
./start_overlay.sh
```

**This is the main way to use AgentFlow!**

A small floating window will appear in the top-right corner of your screen. It stays on top of everything so you can control recording while using your computer normally.

### The Overlay Controls:

- **⏺ Record** - Start recording clicks
- **⏹ Stop** - Stop recording
- **💾 Save** - Save recording to file
- **📁 Load** - Load a previous recording
- **▶ Play** - Play back the recording
- **—** - Minimize to dock

## Quick Demo

Here's a quick workflow to test it out:

### 1. Start the Overlay
```bash
./start_overlay.sh
```

A small window appears in the top-right corner. It shows "● Ready" and "Clicks: 0".

### 2. Record Some Actions
- Click the **⏺ Record** button in the overlay
- The button turns red and shows **⏹ Stop**
- Now click around your screen a few times (try different apps, buttons, etc.)
- The overlay shows your click count increasing
- Click **⏹ Stop** when done

### 3. Save Your Recording
- Click **💾 Save** in the overlay
- Choose a filename like `test.json`
- Click Save

### 4. Play It Back
- Click **▶ Play** in the overlay
- Confirm "Yes" in the dialog
- Watch as your clicks are replayed automatically with the same timing!

### 5. Load Previous Recordings
- Click **📁 Load** to load any saved recording
- Select the file
- Click **▶ Play** to replay it

## Important Permissions

On first run, macOS will ask for permissions:

1. **Accessibility Access** - Required to record clicks
   - System Preferences > Security & Privacy > Privacy > Accessibility
   - Add Terminal (or iTerm, or your Python interpreter)

2. **Screen Recording** - May be required for some features
   - System Preferences > Security & Privacy > Privacy > Screen Recording
   - Add Terminal (or iTerm, or your Python interpreter)

## Features

### What It Records
- **Click positions** (x, y coordinates)
- **Click timing** (how long between each click)
- **Button type** (left, right, middle click)
- **Window states** (positions and sizes of all windows at start)

### What It Can Do
- **Save** recordings as JSON files
- **Load** previously saved recordings
- **Play back** recordings with accurate timing
- **Preview** recordings before playing

### Safety Features
- **Failsafe**: Move mouse to corner of screen to abort playback
- **Confirmation**: Must type 'yes' before playback starts
- **Countdown**: 3-second countdown before playback begins

## Example Workflow

### Automate a Repetitive Task

1. **Record once**: Start recording, perform the task once, stop
2. **Save it**: Save the recording for future use
3. **Replay anytime**: Load and replay whenever you need to repeat the task

### Use Cases
- Testing UI interactions
- Automating repetitive clicking tasks
- Demonstrating workflows
- Creating interaction macros
- Testing different window layouts

## File Structure

Your recordings are saved as JSON files:

```json
{
  "metadata": {
    "recorded_at": "2025-01-15T10:30:00",
    "duration": 45.5,
    "action_count": 10
  },
  "windows": [ /* window states */ ],
  "actions": [
    {
      "type": "click",
      "x": 500,
      "y": 300,
      "button": "Button.left",
      "wait_before": 2.5,
      "timestamp": "2025-01-15T10:30:05"
    }
    /* ... more actions ... */
  ]
}
```

## Troubleshooting

### "Permission denied" when clicking
→ Grant Accessibility permissions (see above)

### Playback not working
→ Ensure screen resolution hasn't changed since recording

### "Module not found" errors
→ Make sure you're using the venv: `./venv/bin/python`

### Clicks going to wrong locations
→ Window positions may have changed - recordings include absolute coordinates

## Tips & Tricks

1. **Test with simple tasks first** - Record just 2-3 clicks to get comfortable

2. **Watch the timing** - The recorder captures real wait times between clicks

3. **Position windows consistently** - For best results, windows should be in same positions during playback

4. **Use preview before playing** - Always preview to see what will happen

5. **Keep recordings short** - Shorter recordings are easier to debug and more reliable

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Try recording a simple task and playing it back
- Experiment with saving and loading recordings
- Consider adding keyboard support (see future enhancements in README)

## Getting Help

If you encounter issues:
1. Check that permissions are granted
2. Try the test script: `./venv/bin/python test_basic.py`
3. Check the terminal output for error messages
4. Make sure you're in the agentflow directory

---

**Happy Automating!**
