const { contextBridge } = require('electron');

// Expose a minimal, safe flag to the renderer to reliably detect Electron
contextBridge.exposeInMainWorld('electron', {
  isElectron: true,
});

// Mark the document so CSS can adapt even if app logic mis-detects
window.addEventListener('DOMContentLoaded', () => {
  try {
    if (document && document.documentElement) {
      document.documentElement.classList.add('electron');
      if (document.body) {
        document.body.style.background = 'transparent';
        document.body.style.margin = '0';
        document.body.style.padding = '0';
        document.body.style.width = '100%';
        document.body.style.height = '100%';
      }
      const nextRoot = document.getElementById('__next');
      if (nextRoot) {
        nextRoot.style.width = '100%';
        nextRoot.style.height = '100%';
      }
    }
  } catch {}
});


