const { Tray, Menu, nativeImage } = require('electron');
const http = require('http');

let tray = null;
let trayConfig = null;

// ── HTTP helpers for backend API ────────────────────────────────────────────

function apiPost(path, body = {}) {
  return apiRequest(path, 'POST', body);
}

function apiPut(path, body = {}) {
  return apiRequest(path, 'PUT', body);
}

function apiRequest(path, method, body = {}) {
  return new Promise((resolve) => {
    const data = JSON.stringify(body);
    const req = http.request(
      `http://127.0.0.1:8000/api${path}`,
      { method, headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }, timeout: 5000 },
      (res) => {
        let body = '';
        res.on('data', (chunk) => { body += chunk; });
        res.on('end', () => {
          try { resolve(JSON.parse(body)); } catch (_) { resolve(null); }
        });
      }
    );
    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
    req.write(data);
    req.end();
  });
}

function apiGet(path) {
  return new Promise((resolve) => {
    const req = http.get(
      `http://127.0.0.1:8000/api${path}`,
      { timeout: 5000 },
      (res) => {
        let body = '';
        res.on('data', (chunk) => { body += chunk; });
        res.on('end', () => {
          try { resolve(JSON.parse(body)); } catch (_) { resolve(null); }
        });
      }
    );
    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
  });
}

// ── State fetching ──────────────────────────────────────────────────────────

async function fetchState() {
  const recordingData = await apiGet('/runtime/recording-state');
  const configData = await apiGet('/config');

  let is_recording = true;
  let is_paused = false;
  if (Array.isArray(recordingData) && recordingData.length >= 2) {
    is_recording = recordingData[0] !== false;
    is_paused = !!recordingData[1];
  }

  return {
    is_recording,
    is_paused,
    lightweight_mode: !!(configData && configData.lightweight_mode),
  };
}

// ── Menu building ───────────────────────────────────────────────────────────

async function buildContextMenu() {
  const state = await fetchState();
  const win = trayConfig.getWindow();

  const recordingLabel = state.is_paused ? '\u7ee7\u7eed\u5f55\u5236' : '\u6682\u505c\u5f55\u5236';
  const lightweightLabel = state.lightweight_mode ? '\u5173\u95ed\u8f7b\u91cf\u6a21\u5f0f' : '\u5f00\u542f\u8f7b\u91cf\u6a21\u5f0f';

  return Menu.buildFromTemplate([
    {
      label: '\u663e\u793a\u4e3b\u754c\u9762',
      click: () => {
        if (win && !win.isDestroyed()) {
          win.show();
          win.restore();
        }
      },
    },
    {
      label: '\u9690\u85cf\u4e3b\u754c\u9762',
      click: () => {
        if (win && !win.isDestroyed()) {
          win.hide();
        }
      },
    },
    { type: 'separator' },
    {
      label: recordingLabel,
      type: 'checkbox',
      checked: !state.is_paused,
      click: async () => {
        if (state.is_paused) {
          await apiPost('/runtime/resume-recording');
        } else {
          await apiPost('/runtime/pause-recording');
        }
        refreshTrayMenu();
      },
    },
    {
      label: lightweightLabel,
      type: 'checkbox',
      checked: state.lightweight_mode,
      click: async () => {
        const config = await apiGet('/config');
        if (config) {
          config.lightweight_mode = !state.lightweight_mode;
          await apiPut('/config', config);
        }
        if (!state.lightweight_mode) {
          if (win && !win.isDestroyed()) win.hide();
        } else {
          if (win && !win.isDestroyed()) { win.show(); win.restore(); }
        }
        refreshTrayMenu();
      },
    },
    { type: 'separator' },
    {
      label: '\u9000\u51fa',
      click: () => {
        const { app } = require('electron');
        app.isQuitting = true;
        app.quit();
      },
    },
  ]);
}

async function refreshTrayMenu() {
  if (!tray || tray.isDestroyed()) return;
  const menu = await buildContextMenu();
  tray.setContextMenu(menu);
}

// ── Public API ──────────────────────────────────────────────────────────────

function createTray(config) {
  trayConfig = config;

  const icon = nativeImage.createFromPath(config.iconPath).resize({ width: 16, height: 16 });
  tray = new Tray(icon);
  tray.setToolTip('Activity Review');

  // Build initial menu
  refreshTrayMenu();

  // Double-click → show window
  tray.on('double-click', () => {
    const win = trayConfig.getWindow();
    if (win && !win.isDestroyed()) {
      win.show();
      win.restore();
      win.focus();
    }
  });
}

function destroyTray() {
  if (tray && !tray.isDestroyed()) {
    tray.destroy();
  }
  tray = null;
}

module.exports = { createTray, destroyTray };
