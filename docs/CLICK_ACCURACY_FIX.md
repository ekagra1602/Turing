# Fixing Click Accuracy Issues

## The Problem

✅ Clicks are **recorded** correctly
❌ Clicks **play back** in the wrong location

## The Solution: Calibration

I've added a calibration system that will fix the coordinate mismatch between recording (pynput) and playback (pyautogui).

## How to Fix It

### Step 1: Run Calibration

```bash
./venv_gui/bin/python calibrate.py
```

**What this does:**
1. Moves your mouse to 4 corners of the screen
2. You click at each position
3. It calculates the offset between where it thinks you clicked vs where you actually clicked
4. Saves the correction to `calibration.json`

**Takes about 30 seconds!**

### Step 2: Test Calibration

```bash
./venv_gui/bin/python calibrate.py test
```

**What this does:**
1. You click somewhere
2. It applies the calibration correction
3. Moves the mouse back to show if it worked
4. You verify visually

### Step 3: Use AgentFlow Normally

```bash
./start_overlay.sh
```

AgentFlow will **automatically use** the calibration data!

- When playing back, clicks will be corrected
- You'll see "[calibrated]" in the terminal output
- Clicks should now go to the correct location

## Visual Feedback

When playing back recordings, you'll see:
- **Green circles** appear where clicks will happen (200ms before)
- This helps you verify the clicks are going to the right place
- If they're still off, run calibration again

## Troubleshooting

### Calibration shows inconsistent offsets

**Symptom**: Different corners have very different offsets

**Cause**: Display scaling or multiple monitor issue

**Solution**: This is more complex - might need additional fixes

### Clicks still slightly off after calibration

**Symptom**: Better but not perfect

**Solution**: Run calibration again - click more precisely

### Calibration test works but playback doesn't

**Symptom**: Test passes, but recordings still play wrong

**Solution**: Make sure you see "[calibrated]" in terminal output

## How It Works

**Recording** (pynput):
- Captures clicks at coordinates like (26, 657)

**Playback** (pyautogui):
- Without calibration: Clicks at (26, 657) - might be wrong!
- With calibration: Applies offset, clicks at (36, 652) - correct!

**The calibration.json file contains:**
```json
{
  "average_offset": [10, -5],
  "screen_size": [1512, 982],
  "calibration_type": "simple_offset"
}
```

## Alternative: Manual Test

If you want to understand the issue first:

```bash
# See the coordinate mismatch
./quick_test.sh

# More detailed test
./venv_gui/bin/python test_click_accuracy.py
```

These will show you exactly how far off the coordinates are.

## Quick Summary

```bash
# 1. Calibrate (one time)
./venv_gui/bin/python calibrate.py

# 2. Test it worked
./venv_gui/bin/python calibrate.py test

# 3. Use AgentFlow normally
./start_overlay.sh

# Calibration is automatically applied! ✅
```

## Expected Results

**Before calibration:**
- Record click at button
- Playback clicks somewhere else
- ❌ Doesn't work

**After calibration:**
- Record click at button
- Playback clicks THE SAME button
- ✅ Works perfectly!

---

**This should completely fix the click accuracy issue!**
