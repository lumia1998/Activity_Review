const { app, BrowserWindow, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const { createTray, destroyTray } = require('./tray');

// ── Single instance lock ────────────────────────────────────────────────────

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
  return;
}

// ── State ───────────────────────────────────────────────────────────────────

let mainWindow = null;
let backendProcess = null;
app.isQuitting = false;

const BACKEND_URL = 'http://127.0.0.1:8000';

// ── Backend process management ──────────────────────────────────────────────

function startBackend() {
  if (app.isPackaged) {
    const exePath = path.join(process.resourcesPath, 'backend', 'ActivityReviewBackend.exe');
    backendProcess = spawn(exePath, [], {
      stdio: 'ignore',
      windowsHide: true,
    });
  } else {
    backendProcess = spawn('python', [
      '-m', 'uvicorn',
      'backend.app.main:app',
      '--host', '127.0.0.1',
      '--port', '8000',
    ], {
      cwd: path.join(__dirname, '..'),
      stdio: 'ignore',
      windowsHide: true,
    });
  }

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend:', err.message);
  });

  backendProcess.on('exit', (code) => {
    console.log('Backend exited with code:', code);
    backendProcess = null;
  });
}

function stopBackend() {
  if (!backendProcess) return;
  try {
    backendProcess.kill();
  } catch (_) {
    // already dead
  }
  backendProcess = null;
}

function waitForBackend(timeoutMs = 30000) {
  const interval = 500;
  const maxAttempts = Math.ceil(timeoutMs / interval);
  let attempts = 0;

  return new Promise((resolve) => {
    const check = () => {
      attempts++;
      const req = http.get(`${BACKEND_URL}/health`, (res) => {
        let body = '';
        res.on('data', (chunk) => { body += chunk; });
        res.on('end', () => {
          try {
            const data = JSON.parse(body);
            if (data.status === 'ok') {
              resolve(true);
              return;
            }
          } catch (_) { /* not ready */ }
          retry();
        });
      });
      req.on('error', () => retry());
      req.setTimeout(2000, () => { req.destroy(); retry(); });
    };

    const retry = () => {
      if (attempts >= maxAttempts) {
        resolve(false);
        return;
      }
      setTimeout(check, interval);
    };

    check();
  });
}

// ── Window creation ─────────────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    minWidth: 800,
    minHeight: 600,
    frame: false,
    icon: path.join(__dirname, '..', 'public', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL(BACKEND_URL);

  // ── Window events → renderer ────────────────────────────────────────

  mainWindow.on('move', () => {
    if (mainWindow.isDestroyed()) return;
    const [x, y] = mainWindow.getPosition();
    mainWindow.webContents.send('window-moved', { x, y });
  });

  mainWindow.on('minimize', () => {
    if (mainWindow.isDestroyed()) return;
    mainWindow.webContents.send('window-minimized', { minimized: true });
  });

  mainWindow.on('restore', () => {
    if (mainWindow.isDestroyed()) return;
    mainWindow.webContents.send('window-minimized', { minimized: false });
  });

  mainWindow.on('maximize', () => {
    if (mainWindow.isDestroyed()) return;
    mainWindow.webContents.send('window-maximized', { maximized: true });
  });

  mainWindow.on('unmaximize', () => {
    if (mainWindow.isDestroyed()) return;
    mainWindow.webContents.send('window-maximized', { maximized: false });
  });

  // ── Close → hide to tray (unless quitting) ─────────────────────────

  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

// ── IPC handlers ────────────────────────────────────────────────────────────

function registerIpcHandlers() {
  ipcMain.handle('open-external', async (_event, url) => {
    if (url) await shell.openExternal(url);
  });

  ipcMain.handle('close-window', () => {
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.hide();
  });

  ipcMain.handle('hide-window', () => {
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.hide();
  });

  ipcMain.handle('show-window', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
      mainWindow.restore();
    }
  });

  ipcMain.handle('minimize-window', () => {
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.minimize();
  });

  ipcMain.handle('maximize-window', () => {
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.maximize();
  });

  ipcMain.handle('unmaximize-window', () => {
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.unmaximize();
  });

  ipcMain.handle('is-maximized', () => {
    if (mainWindow && !mainWindow.isDestroyed()) return mainWindow.isMaximized();
    return false;
  });

  ipcMain.handle('is-visible', () => {
    if (mainWindow && !mainWindow.isDestroyed()) return mainWindow.isVisible();
    return false;
  });

  ipcMain.handle('pick-directory', async (_event, options = {}) => {
    if (!mainWindow || mainWindow.isDestroyed()) return null;
    const dialogOptions = { properties: ['openDirectory'] };
    if (options.defaultPath) {
      dialogOptions.defaultPath = options.defaultPath;
    }
    const result = await dialog.showOpenDialog(mainWindow, dialogOptions);
    if (result.canceled || !result.filePaths.length) return null;
    return result.filePaths[0];
  });

  ipcMain.handle('confirm-dialog', async (_event, options = {}) => {
    if (!mainWindow || mainWindow.isDestroyed()) return false;
    const result = await dialog.showMessageBox(mainWindow, {
      type: 'question',
      title: options.title || 'Activity Review',
      message: options.message || '',
      buttons: ['OK', 'Cancel'],
      defaultId: 0,
      cancelId: 1,
    });
    return result.response === 0;
  });

  ipcMain.handle('relaunch', () => {
    app.relaunch();
    app.exit(0);
  });

  ipcMain.handle('get-version', () => {
    return app.getVersion();
  });

  ipcMain.handle('emit-to', (_event, _label, eventName, payload) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send(eventName, payload);
    }
  });
}

// ── App lifecycle ───────────────────────────────────────────────────────────

app.on('second-instance', () => {
  if (mainWindow) {
    if (!mainWindow.isVisible()) mainWindow.show();
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  }
});

app.on('before-quit', () => {
  app.isQuitting = true;
  stopBackend();
  destroyTray();
});

app.on('window-all-closed', () => {
  // On Windows, quit when all windows are closed (unless hidden to tray)
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.whenReady().then(async () => {
  registerIpcHandlers();

  // Start backend
  startBackend();
  const ready = await waitForBackend(30000);
  if (!ready) {
    console.error('Backend did not become ready within 30s');
    dialog.showErrorBox('Startup Error', 'Backend server failed to start. The application will now exit.');
    app.quit();
    return;
  }

  createWindow();

  // Create tray
  createTray({
    getWindow: () => mainWindow,
    iconPath: path.join(__dirname, '..', 'public', 'icon.png'),
  });
});
