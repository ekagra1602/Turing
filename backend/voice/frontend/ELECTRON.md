# AgentFlow Voice - Electron Overlay

Run AgentFlow Voice as a **desktop overlay app** that floats on top of all windows!

## Features

- 🪟 **True Desktop Overlay** - Floats above all applications
- 🎯 **Always on Top** - Stays visible while you work
- 🔲 **Transparent** - Clean integration with your desktop
- 🎨 **Same Beautiful UI** - Exact same design as the web version
- 🖱️ **Draggable** - Move it anywhere on your screen

## Quick Start

### 1. Install Dependencies

```bash
cd backend/voice/frontend
npm install
```

This installs Electron and helper packages:
- `electron` - Desktop app framework
- `concurrently` - Run Next.js and Electron together
- `wait-on` - Wait for Next.js server to start
- `electron-builder` - Build standalone apps

### 2. Run as Overlay

```bash
npm run electron:dev
```

This will:
1. Start the Next.js dev server (port 3000)
2. Wait for it to be ready
3. Launch the Electron overlay window

**That's it!** The overlay will appear in the top-right corner of your screen.

## Usage

### Moving the Window
- Click and drag the window header to reposition it anywhere

### Browser vs Electron
- **Browser** (`npm run dev`): Window appears in top-right of browser
- **Electron** (`npm run electron:dev`): Floating desktop overlay

Both use the **exact same UI** - the app auto-detects the environment!

## Building Standalone App

To create a distributable app:

```bash
npm run electron:build
```

This creates a `.dmg` file in the `dist/` folder that you can share or install.

## Configuration

### Window Settings

Edit `electron/main.js` to customize:

```javascript
const mainWindow = new BrowserWindow({
  width: 420,          // Window width
  height: 560,         // Window height
  transparent: true,   // Transparent background
  frame: false,        // No title bar
  alwaysOnTop: true,   // Stay on top
  resizable: false,    // Fixed size
});
```

### Position

The window appears in the **top-right corner** by default. Change this in `electron/main.js`:

```javascript
// Top-right (default)
mainWindow.setPosition(width - 420 - 40, 40);

// Top-left
mainWindow.setPosition(40, 40);

// Bottom-right
mainWindow.setPosition(width - 420 - 40, height - 560 - 40);
```

## Troubleshooting

### Window Not Appearing
- Check that port 3000 is not already in use
- Look for errors in the terminal
- Try running `npm run dev` first to test Next.js

### Can't Click Through Transparent Areas
- This is normal - the window is interactive
- Edit `electron/main.js` and uncomment the click-through code if needed

### Window Behind Other Apps
- Make sure `alwaysOnTop: true` in `electron/main.js`
- Some full-screen apps may override this

### Blank Window
- Wait a few seconds for Next.js to start
- Check browser console: `Cmd+Option+I` in Electron window
- Verify `http://localhost:3000` works in your browser

## Development

### File Structure

```
frontend/
├── electron/
│   └── main.js           # Electron main process
├── app/
│   └── page.tsx          # Auto-detects Electron/browser
├── package.json          # Includes Electron scripts
└── ELECTRON.md           # This file
```

### How It Works

1. **Next.js** runs normally on `localhost:3000`
2. **Electron** creates a transparent, frameless window
3. **Window** loads the Next.js app inside
4. **Detection**: `page.tsx` checks `window.navigator.userAgent` for "Electron"
5. **Adaptation**:
   - Browser: Shows at `top-8 right-8` with dark background
   - Electron: Fills entire window with transparent background

### Making Changes

All your UI changes work automatically in both modes! Just edit the React components as normal.

## Tips

- **Keyboard Shortcut**: Create an Alfred/Raycast workflow to launch the app
- **Auto-Start**: Add to Login Items in macOS System Preferences
- **Multiple Monitors**: Window appears on primary display
- **Hide/Show**: Press `Cmd+H` to hide, `Cmd+Tab` to bring back

## Resources

- [Electron Docs](https://www.electronjs.org/docs/latest/)
- [Next.js + Electron](https://github.com/vercel/next.js/tree/canary/examples/with-electron)

---

**Built for CalHacks 2025** 🚀

*The same beautiful AgentFlow Voice UI, now as a desktop overlay!*
