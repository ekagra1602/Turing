# AgentFlow Pro - Enhanced Recording Mode 🚀

## What's New?

AgentFlow Pro captures the **complete interaction story**, not just clicks!

### Full Interaction Recording:

✅ **Mouse Movements** - Full cursor path, not just endpoints
✅ **Clicks** - Mouse down/up events (enables drag detection)
✅ **Keyboard Input** - Every keystroke captured
✅ **Scrolling** - Scroll wheel events with position
✅ **Hovers** - Time spent at each position
✅ **Drags** - Automatically detected from click+move patterns

## Why This Matters

**Old Way (Click-Only):**
```
1. Click at (100, 100)
2. Click at (500, 200)
```
❌ Misses: How you got there, what you hovered over, what you typed

**New Way (Full Recording):**
```
1. Move to (100, 80)    ← Hover approach
2. Move to (100, 100)   ← Precise positioning
3. Click down at (100, 100)
4. Move to (120, 110)   ← Drag motion
5. Move to (140, 115)
6. Click up at (150, 120)  ← Drag complete
7. Key: 'h'
8. Key: 'e'
9. Key: 'l'
10. Key: 'l'
11. Key: 'o'
12. Scroll at (300, 400): dy=3
```
✅ Captures: Complete interaction context!

## The Overlay

```
┌────────────────────────┐
│   AgentFlow Pro        │
├────────────────────────┤
│   ● Ready              │
│   Actions: 0           │
├────────────────────────┤
│   ┌─ Record ─────┐    │
│   │ ☑ 🖱️  Movements│    │
│   │ ☑ ⌨️  Keyboard │    │
│   └───────────────┘    │
├────────────────────────┤
│  [    ⏺ Record    ]   │
│  [    💾 Save      ]   │
│  [    📁 Load      ]   │
│  [    ▶ Play      ]   │
├────────────────────────┤
│   ┌─ Playback ────┐   │
│   │ ☑ 🐌 Smooth    │   │
│   └───────────────┘    │
│  [       —        ]    │
└────────────────────────┘
```

## Recording Options

### 🖱️ Movements (Checkbox)
- **ON**: Records full cursor path (smooth replay)
- **OFF**: Only records clicks (jump between points)
- **File size**: ~10x larger with movements
- **Use when**: Recording precise workflows, tutorials

### ⌨️ Keyboard (Checkbox)
- **ON**: Records every keystroke
- **OFF**: Only mouse interactions
- **Security**: ⚠️ Captures passwords if you type them!
- **Use when**: Need to replay text input, form filling

## Playback Options

### 🐌 Smooth (Checkbox)
- **ON**: Mouse moves smoothly along recorded path
- **OFF**: Mouse teleports between positions
- **Speed**: Smooth is slower but more visual
- **Use when**: Want to watch/verify actions

## How to Use

### Start the Enhanced Version:

```bash
./start_pro.sh
```

### Recording Example:

1. **Enable options** - Check "Movements" and "Keyboard"
2. **Click ⏺ Record**
3. **Perform your workflow**:
   - Move mouse around
   - Click buttons
   - Type text
   - Scroll pages
   - Drag items
4. **Click ⏹ Stop**
5. **Click 💾 Save**

### Playback Example:

1. **Click 📁 Load** (or use what you just recorded)
2. **Choose playback mode**:
   - Check "Smooth" for visual replay
   - Uncheck for fast execution
3. **Click ▶ Play**
4. **Watch** the complete interaction replay!

## What Gets Recorded

### Action Types:

| Type | Description | When |
|------|-------------|------|
| `move` | Mouse movement | Every 50ms if moved >5px |
| `click_down` | Button press | Start of click |
| `click_up` | Button release | End of click |
| `scroll` | Scroll wheel | Any scroll event |
| `key` | Keystroke | Any key press |

### Metadata Saved:

```json
{
  "metadata": {
    "recording_mode": "enhanced",
    "action_count": 1247,
    "duration": 45.5,
    "options": {
      "movements": true,
      "keyboard": true,
      "sample_rate": 0.05
    }
  },
  "actions": [
    {
      "type": "move",
      "x": 100,
      "y": 100,
      "wait_before": 0.05,
      "timestamp": "..."
    },
    {
      "type": "click_down",
      "x": 100,
      "y": 100,
      "button": "Button.left",
      "wait_before": 0.1,
      "timestamp": "..."
    },
    {
      "type": "key",
      "key": "h",
      "wait_before": 0.2,
      "timestamp": "..."
    }
  ]
}
```

## Performance Notes

### File Sizes:

- **Click-only**: ~1-5 KB (small!)
- **With movements**: ~50-200 KB (larger)
- **With keyboard**: Adds ~1 KB per 100 keys

### Recording Duration:

- **Short task** (10 seconds): ~200-500 actions
- **Medium task** (60 seconds): ~1000-3000 actions
- **Long task** (5 minutes): ~5000-15000 actions

### Playback Speed:

- **Movements OFF**: Super fast, instant jumps
- **Movements ON**: Natural speed (can adjust with speed multiplier)

## Use Cases

### Perfect For:

✅ **UI Testing** - Replay exact user interactions
✅ **Tutorials** - Record then replay demonstrations
✅ **Form Filling** - Automate repetitive data entry
✅ **Workflow Automation** - Complex multi-step tasks
✅ **Bug Reproduction** - Exact steps that caused issue

### Not Ideal For:

❌ **Long recordings** - File gets huge, hard to edit
❌ **Variable data** - Replays exact same keystrokes
❌ **Password entry** - Security risk (gets recorded!)

## Tips & Tricks

### 1. Disable Movements for Speed
If you don't need the path, turn off "Movements" for 10x smaller files and faster playback.

### 2. Edit JSON Files
Recordings are human-readable JSON! You can:
- Remove unwanted actions
- Change coordinates
- Adjust timing
- Add/remove keystrokes

### 3. Combine Recordings
Load a recording, add to it, save as new file.

### 4. Speed Control
In code, adjust `player.playback_speed = 2.0` for 2x speed.

### 5. Selective Recording
- Record movements but not keyboard
- Record keyboard but not movements
- Mix and match!

## Security Warning ⚠️

**Keyboard recording captures everything you type!**

- Passwords
- Credit card numbers
- Personal information

**Best Practices:**
- ❌ Don't record sensitive input
- ✅ Disable keyboard when not needed
- ✅ Don't share recordings with sensitive data
- ✅ Review recording before saving

## Comparison

| Feature | Basic Mode | Pro Mode |
|---------|------------|----------|
| Clicks | ✅ | ✅ |
| Movements | ❌ | ✅ |
| Keyboard | ❌ | ✅ |
| Scrolling | ❌ | ✅ |
| Drags | ❌ | ✅ |
| Hovers | ❌ | ✅ |
| File Size | Small | Larger |
| Playback | Fast | Realistic |

## Which Version to Use?

### Use **Basic Mode** (`./start_overlay.sh`):
- Simple click automation
- Fast playback needed
- Small file sizes
- No keyboard needed

### Use **Pro Mode** (`./start_pro.sh`):
- Need complete interaction story
- Recording tutorials/demos
- Form filling with text
- Complex workflows
- Drag and drop operations

---

**AgentFlow Pro captures the full story of your interactions!** 🎬
