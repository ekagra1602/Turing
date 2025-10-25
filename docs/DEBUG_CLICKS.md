# Debugging Click Position Issues

## The Problem

Clicks are being **recorded correctly** but **playing back in the wrong location**.

## Possible Causes

1. **Coordinate system mismatch** - pynput and pyautogui use different coordinate systems
2. **Display scaling** - Retina displays might report coordinates differently
3. **Multiple monitors** - Different coordinate spaces per monitor
4. **Window manager interference** - macOS window manager affecting coordinates

## Quick Tests

### Test 1: Basic Coordinate Test

```bash
./quick_test.sh
```

This will:
- Show your screen size
- Record one click
- Move mouse to that position
- Click at that position
- You verify if it's correct

### Test 2: Visual Position Test

```bash
./venv_gui/bin/python test_click_accuracy.py
```

More detailed test that shows exact coordinates at each step.

### Test 3: Coordinate System Fix Test

```bash
./venv_gui/bin/python coordinate_fix.py
```

Tests if display scaling is the issue.

## Common Issues & Fixes

### Issue 1: Clicks are off by a consistent amount

**Symptom**: Every click is off by roughly the same distance/direction

**Cause**: Coordinate system offset

**Fix**: We need to add an offset correction

### Issue 2: Clicks are off by a scaling factor

**Symptom**: Clicks near top-left are close, but clicks near bottom-right are way off

**Cause**: Display scaling (Retina display)

**Fix**: Apply scaling factor to coordinates

### Issue 3: Clicks are slightly off (1-5 pixels)

**Symptom**: Close but not quite right

**Cause**: Rounding or timing

**Status**: Already fixed with `round()` instead of `int()`

## Manual Test Procedure

1. **Open a text editor** (like TextEdit)
2. **Place cursor at a specific location** (like start of a word)
3. **Start AgentFlow** and record
4. **Click on that exact location**
5. **Stop and play back**
6. **Observe**: Does it click the same spot?

## Collecting Debug Info

Please run these and share the output:

```bash
# Screen info
./venv_gui/bin/python -c "import pyautogui; print(pyautogui.size())"

# Display info
system_profiler SPDisplaysDataType | grep -A 5 "Resolution"

# Test coordinates
./venv_gui/bin/python test_click_accuracy.py
```

## Temporary Workaround

Until we fix the coordinate issue, you can:

1. Record clicks in the **same window/position** every time
2. Don't move windows between record and playback
3. Test with clicks in the **center** of the screen (usually more accurate)
4. Avoid clicks near edges of screen

## Next Steps

Based on your test results, we can:

1. **Add coordinate offset correction**
2. **Implement display scaling detection**
3. **Add coordinate system conversion layer**
4. **Create calibration tool** (click known points to build correction map)

## Quick Fix Attempt

If you want to try a potential fix now:

1. Record a click at position (100, 100)
2. Note where playback actually clicks
3. Calculate the difference
4. We can add that offset to all coordinates

Example:
- Recorded: (100, 100)
- Actually clicks: (110, 95)
- Offset needed: (+10, -5)
- Apply to all future clicks
