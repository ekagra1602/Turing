# AgentFlow Overlay Guide

## What is the Overlay?

The AgentFlow overlay is a **small floating window** that stays on top of all your other applications. Think of it like a tiny control panel that's always accessible.

## Visual Layout

```
┌─────────────────────┐
│    AgentFlow        │ ← Title
├─────────────────────┤
│   ● Ready           │ ← Status indicator
│   Clicks: 0         │ ← Click counter
├─────────────────────┤
│  [  ⏺ Record  ]    │ ← Start recording (green)
│  [  💾 Save    ]    │ ← Save recording (blue)
│  [  📁 Load    ]    │ ← Load recording (yellow)
│  [  ▶ Play    ]    │ ← Play recording (red)
│  [     —      ]    │ ← Minimize
└─────────────────────┘
```

## Size & Position

- **Size**: 200x280 pixels (compact, unobtrusive)
- **Position**: Top-right corner of screen
- **Always on top**: Yes
- **Semi-transparent**: 95% opacity
- **Moveable**: No (fixed position to stay out of the way)
- **Can minimize**: Yes (to dock)

## Color Coding

### Status Indicators
- **🟢 Green "● Ready"** - Ready to record or play
- **🔴 Red "● Recording..."** - Currently recording clicks
- **🟠 Orange "● Stopped"** - Recording stopped, ready to save
- **🔵 Cyan "● Playing..."** - Playing back a recording
- **🔵 Blue "● Loaded"** - Recording loaded from file

### Button States
- **⏺ Record** (Green) - Click to start recording
- **⏹ Stop** (Red) - Click to stop recording (only when recording)
- **💾 Save** (Blue) - Save current recording (disabled until you record)
- **📁 Load** (Yellow) - Load a saved recording file
- **▶ Play** (Red) - Play back recording (disabled until you have one)
- **—** (Gray) - Minimize to dock

## Typical Workflow

### Recording Session

1. **Idle State**
   ```
   Status: ● Ready (green)
   Clicks: 0
   Record button: Green, enabled
   ```

2. **While Recording**
   ```
   Status: ● Recording... (red)
   Clicks: 5 (updates live)
   Record button: Red "⏹ Stop"
   Other buttons: Disabled
   ```

3. **After Stopping**
   ```
   Status: ● Stopped (orange)
   Clicks: 5 (final count)
   Save button: Enabled
   Play button: Enabled
   ```

### Playback Session

1. **Loading a File**
   - Click 📁 Load
   - File picker opens
   - Select .json file
   - Status: ● Loaded (blue)

2. **Playing Back**
   - Click ▶ Play
   - Confirmation dialog appears
   - Status: ● Playing... (cyan)
   - Clicks are replayed with timing

## Features

### Always Available
The overlay is **always visible** while you work, so you can:
- Start recording at any moment
- Check if you're currently recording
- See your click count in real-time
- Access playback controls instantly

### Doesn't Block Your Work
- **Small footprint**: Only 200px wide
- **Corner placement**: Top-right, out of the way
- **Can minimize**: Hide it when not needed
- **Transparent**: Slightly see-through

### Smart Button States
Buttons automatically enable/disable based on context:
- Can't save if nothing recorded
- Can't play if no recording loaded
- Can't load/play while recording
- Can't record while playing

## Keyboard Shortcuts

Currently none - all control via mouse clicks on the overlay buttons.

**Future enhancement**: Add keyboard shortcuts like:
- `Cmd+Shift+R` to start/stop recording
- `Cmd+Shift+P` to play
- `Cmd+Shift+S` to save

## Tips

1. **Position**: The overlay appears in top-right corner automatically
2. **Recording**: The overlay itself won't capture clicks on its own buttons
3. **Visibility**: If you lose it, check your dock - it may be minimized
4. **Multi-monitor**: Works on primary display
5. **Relaunch**: Just run `./start_overlay.sh` again if it closes

## Technical Details

- Built with Python's `tkinter` (standard library)
- Uses system Python (not Homebrew) for tkinter support
- Runs in its own virtual environment (`venv_gui`)
- Single-threaded with background tasks for playback
- Auto-saves window state in recordings

## Troubleshooting

**Overlay doesn't appear**
→ Check terminal for errors
→ Grant Accessibility permissions
→ Try running: `./venv_gui/bin/python minimal_overlay.py`

**Buttons are grayed out**
→ Normal! They enable based on state (e.g., need recording to save)

**Overlay disappeared**
→ Check if it's minimized in dock
→ Rerun `./start_overlay.sh`

**Can't click other windows**
→ The overlay stays on top but doesn't block input
→ Click normally on windows behind it

---

**The overlay makes AgentFlow actually usable!** No need to switch to terminal - just glance at the corner to see status and click buttons to control recording.
