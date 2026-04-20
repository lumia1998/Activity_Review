const { contextBridge, ipcRenderer } = require('electron');

// Track event listeners for cleanup
const eventListeners = new Map();

contextBridge.exposeInMainWorld('__ACTICITY_DESKTOP__', {
  // Static properties
  version: '',  // will be populated via getVersion()
  currentWindowLabel: 'main',

  // ── Navigation / lifecycle ──────────────────────────────────────────────

  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  relaunch: () => ipcRenderer.invoke('relaunch'),

  getVersion: () => ipcRenderer.invoke('get-version'),

  // ── Cross-window events ─────────────────────────────────────────────────

  emitTo: (label, eventName, payload) =>
    ipcRenderer.invoke('emit-to', label, eventName, payload),

  // ── Window dragging (handled by CSS -webkit-app-region: drag) ───────────

  startDragging: () => Promise.resolve(),

  // ── Window event listeners ──────────────────────────────────────────────

  listenWindowEvent: (eventName, callback) => {
    const handler = (_event, payload) => {
      callback({ payload });
    };
    ipcRenderer.on(eventName, handler);

    // Return an unlisten function
    const unlisten = async () => {
      ipcRenderer.removeListener(eventName, handler);
    };
    return Promise.resolve(unlisten);
  },

  onWindowMoved: (callback) => {
    const handler = (_event, payload) => {
      callback({ payload });
    };
    ipcRenderer.on('window-moved', handler);

    const unlisten = async () => {
      ipcRenderer.removeListener('window-moved', handler);
    };
    return Promise.resolve(unlisten);
  },

  // ── Window controls ─────────────────────────────────────────────────────

  closeWindow: () => ipcRenderer.invoke('close-window'),

  hideWindow: () => ipcRenderer.invoke('hide-window'),

  showWindow: () => ipcRenderer.invoke('show-window'),

  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),

  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),

  unmaximizeWindow: () => ipcRenderer.invoke('unmaximize-window'),

  isMaximized: () => ipcRenderer.invoke('is-maximized'),

  isVisible: () => ipcRenderer.invoke('is-visible'),

  // ── Dialogs ─────────────────────────────────────────────────────────────

  pickDirectory: (options) => ipcRenderer.invoke('pick-directory', options || {}),

  confirm: (options) => ipcRenderer.invoke('confirm-dialog', options || {}),
});
