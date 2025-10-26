const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 380,
    height: 480,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: false,
    hasShadow: false,
    backgroundColor: '#00000000',
    useContentSize: true,
    show: false, // we'll position first, then show
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      backgroundThrottling: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // Position window in top-right corner (flush with edges, below menu bar)
  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { x: workX, y: workY, width: workW, height: workH } = primaryDisplay.workArea; // safer with notch/menu bar

  // Flush to the right edge, with a small adjustable margin from top
  const TOP_OFFSET = parseInt(process.env.ELECTRON_Y_OFFSET || '8', 10); // minimal default
  const CONTENT_W = 380;
  const CONTENT_H = 480;
  const applyPosition = () => {
    const x = Math.round(workX + workW - CONTENT_W);
    const y = Math.round(workY + TOP_OFFSET);
    console.log('[Electron] setContentBounds', { x, y, width: CONTENT_W, height: CONTENT_H, workArea: { workX, workY, workW, workH } });
    mainWindow.setContentBounds({ x, y, width: CONTENT_W, height: CONTENT_H });
  };
  // Ensure content size is exact before showing
  mainWindow.setContentSize(CONTENT_W, CONTENT_H);
  applyPosition();

  // Load Next.js dev server or production build
  const isDev = process.env.NODE_ENV !== 'production';

  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    // Open DevTools in development
    // mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../out/index.html'));
  }

  // Make window draggable
  mainWindow.setIgnoreMouseEvents(false);

  // Ensure background stays transparent once content loads
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.setBackgroundColor('#00000000');
  });

  // After content is ready to show, re-apply position then show to avoid flicker
  mainWindow.once('ready-to-show', () => {
    applyPosition();
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// macOS: Keep app running when all windows are closed
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Wait for app to be ready
app.whenReady().then(() => {
  createWindow();
});

// Enable click-through for transparent areas (optional)
// Uncomment if you want clicks to pass through transparent parts
// app.commandLine.appendSwitch('enable-transparent-visuals');
