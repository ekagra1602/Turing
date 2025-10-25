# AgentFlow

Record and replay complete user interactions on macOS.

## Quick Start

```bash
# Basic version (clicks only, fast)
./start_basic.sh

# Pro version (full interactions: movements, keyboard, drags)
./start_pro.sh
```

That's it! A small overlay appears in the top-right corner. Hit Record, do stuff, hit Stop, then Play it back.

## Features

### Basic Mode
- ⚡ Click recording
- 🎯 Instant playback
- 📦 Small file sizes (~2KB)
- 🚀 Fast execution

### Pro Mode
- 🖱️ Full mouse movements
- ⌨️ Keyboard input
- 📜 Scrolling
- ↔️ Drag & drop
- ⏱️ Exact timing

## Installation

```bash
# Clone or download
cd agentflow

# Install dependencies (automatic on first run)
./start_basic.sh
```

### Requirements
- macOS 10.15+
- Python 3.8+
- **Accessibility permissions** (System Preferences → Security & Privacy)

## Usage

### Recording

1. Launch overlay: `./start_basic.sh` or `./start_pro.sh`
2. Click **⏺ Record**
3. Perform your actions
4. Click **⏹ Stop**
5. Click **💾 Save**

### Playback

1. Click **📁 Load** (or use just-recorded session)
2. Click **▶ Play**
3. Watch it replay automatically

### Options

**Pro Mode Recording:**
- ☑ **Movements** - Record full cursor path
- ☑ **Keyboard** - Capture keystrokes

**Playback:**
- ☑ **Instant** (Basic) - Direct clicks, no movement
- ☑ **Smooth** (Pro) - Natural movement replay

## Use Cases

- 🧪 UI/UX testing
- 📝 Form automation
- 🎓 Tutorial creation
- 🐛 Bug reproduction
- ⚙️ Workflow automation
- 🔄 Repetitive task automation

## Permissions

AgentFlow needs **Accessibility** permissions:

1. System Preferences → Security & Privacy → Privacy
2. Click **Accessibility**
3. Click 🔒 and enter password
4. Click **+** and add **Terminal**
5. Restart AgentFlow

## Troubleshooting

### "Not trusted" error
→ Grant Accessibility permissions (see above)

### Clicks go to wrong places
→ Run calibration: `./venv_gui/bin/python tools/calibrate.py`

### Import errors
→ Run `./start_basic.sh` to auto-install dependencies

### Overlay doesn't appear
→ Check terminal for errors

## Project Structure

```
agentflow/
├── start_basic.sh         # Launch basic mode
├── start_pro.sh           # Launch pro mode
├── src/                   # Source code
│   ├── basic/            # Basic mode
│   └── pro/              # Pro mode
└── tools/                 # Utilities
```

## Advanced

### Calibration

Fix coordinate accuracy:

```bash
./venv_gui/bin/python tools/calibrate.py
```

### Diagnostics

Check your setup:

```bash
./venv_gui/bin/python tools/diagnose.py
```

## Security

⚠️ **Keyboard recording captures EVERYTHING you type!**

- Don't record passwords
- Don't share recordings with sensitive data
- Disable keyboard recording when not needed

All recordings are local - nothing sent anywhere.

## Comparison

| Feature | Basic | Pro |
|---------|-------|-----|
| Clicks | ✅ | ✅ |
| Movements | ❌ | ✅ |
| Keyboard | ❌ | ✅ |
| Scrolling | ❌ | ✅ |
| File Size | ~2KB | ~50KB |
| Speed | Instant | Natural |

## Tips

- **First time?** Use Basic mode
- **Complex workflows?** Use Pro mode
- **Form filling?** Enable keyboard in Pro
- **Fast automation?** Basic mode with instant clicks
- **Debugging?** Pro mode with smooth playback

## License

MIT - use freely

---

**Record once, replay forever!** 🎬
