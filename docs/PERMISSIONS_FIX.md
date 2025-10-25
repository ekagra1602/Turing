# Fixing Permissions for AgentFlow

## The Error You're Seeing

```
This process is not trusted! Input event monitoring will not be possible until it is added to accessibility clients.
```

This means macOS is **blocking** AgentFlow from detecting your clicks. This is a security feature.

## How to Fix It

### Step 1: Open System Preferences

1. Click the Apple menu () in top-left corner
2. Click **System Preferences** (or **System Settings** on newer macOS)
3. Click **Security & Privacy**
4. Click the **Privacy** tab

### Step 2: Grant Accessibility Access

1. In the left sidebar, scroll down and click **Accessibility**
2. Click the **lock icon** at bottom-left (you'll need your password)
3. Click the **+** button to add an application
4. Navigate to **Applications** → **Utilities** → **Terminal** (or iTerm if you use that)
5. Select **Terminal** and click **Open**
6. Make sure the checkbox next to **Terminal** is **checked** ✅

### Step 3: Also Add Python (Optional but Recommended)

While you're in Accessibility settings:

1. Click the **+** button again
2. Press **Cmd+Shift+G** to open "Go to folder"
3. Paste this path: `/usr/bin/`
4. Find and select **python3**
5. Click **Open**
6. Check the box next to it ✅

### Step 4: Restart AgentFlow

Close the overlay and restart it:

```bash
./start_overlay.sh
```

## Visual Guide

```
System Preferences
  └─ Security & Privacy
       └─ Privacy tab
            └─ Accessibility (left sidebar)
                 └─ [+] Add Terminal
                 └─ [+] Add python3 (optional)
                 └─ [✓] Make sure both are checked
```

## Alternative: Quick Terminal Command

You can also try this command to check current permissions:

```bash
# Check if we have accessibility permissions
sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" \
  "SELECT * FROM access WHERE service='kTCCServiceAccessibility';"
```

## Testing After Granting Permissions

After granting permissions:

1. Run `./start_overlay.sh`
2. Click **⏺ Record**
3. Click somewhere on your screen
4. Check the terminal output - it should say:
   ```
   Recorded click at (123, 456) with X.XXs wait
   ```
   (Without the "not trusted" error)

## Still Not Working?

### Try These Steps:

1. **Remove and Re-add Terminal**
   - In Accessibility settings, select Terminal
   - Click the **-** button to remove it
   - Click **+** to add it back
   - Restart your Terminal app

2. **Restart Your Computer**
   - Sometimes macOS needs a full restart for permissions to take effect

3. **Check macOS Version**
   - On macOS Ventura (13.0+), the settings might be in different locations
   - Look for **Privacy & Security** instead of **Security & Privacy**

4. **Use System Python Directly**
   ```bash
   /usr/bin/python3 minimal_overlay.py
   ```
   This bypasses virtual environment issues

## Why This Happens

macOS introduced strict privacy controls to prevent malware from:
- Monitoring keyboard input
- Tracking mouse movements
- Recording clicks

AgentFlow needs these permissions to function, but you have to explicitly grant them.

## Security Note

These permissions allow AgentFlow to:
- ✅ See when you click
- ✅ Record click positions
- ✅ Simulate clicks during playback

AgentFlow does **NOT**:
- ❌ Record keystrokes
- ❌ Capture screenshots
- ❌ Access files without your permission
- ❌ Send data anywhere (everything is local)

All recordings are saved locally as JSON files that you can inspect.

## Verification

Once permissions are granted correctly, you should see:

```
Starting recording...
Captured 0 window positions
Recorded click at (500, 300) with 2.50s wait  ← No error!
Recorded click at (600, 400) with 1.20s wait
Stopping recording...
Recorded 2 actions
```

No "not trusted" message = permissions are working! ✅

---

**After granting permissions, AgentFlow will work perfectly!**
