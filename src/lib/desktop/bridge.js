function getDesktopApi() {
  return window.__ACTICITY_DESKTOP__ || null;
}

function dispatchWindowEvent(eventName, payload) {
  window.dispatchEvent(new CustomEvent(eventName, { detail: payload }));
}

export async function open(url) {
  if (!url) return;
  const desktop = getDesktopApi();
  if (typeof desktop?.openExternal === 'function') {
    await desktop.openExternal(url);
    return;
  }
  window.open(url, '_blank', 'noopener,noreferrer');
}

export async function relaunch() {
  const desktop = getDesktopApi();
  if (typeof desktop?.relaunch === 'function') {
    await desktop.relaunch();
    return;
  }
  window.location.reload();
}

export async function getVersion() {
  const desktop = getDesktopApi();
  if (typeof desktop?.getVersion === 'function') {
    return desktop.getVersion();
  }
  if (typeof desktop?.version === 'string' && desktop.version.trim()) {
    return desktop.version;
  }
  if (typeof window.__ACTICITY_VERSION__ === 'string' && window.__ACTICITY_VERSION__.trim()) {
    return window.__ACTICITY_VERSION__;
  }
  return 'web-dev';
}

export async function emitTo(label, eventName, payload) {
  const desktop = getDesktopApi();
  if (typeof desktop?.emitTo === 'function') {
    await desktop.emitTo(label, eventName, payload);
    return;
  }
  dispatchWindowEvent(eventName, payload);
}

export function getCurrentWebviewWindow() {
  const desktop = getDesktopApi();
  let maximized = false;
  let visible = true;

  return {
    label: desktop?.currentWindowLabel || 'main',
    async startDragging() {
      await desktop?.startDragging?.();
    },
    async close() {
      if (typeof desktop?.closeWindow === 'function') {
        await desktop.closeWindow();
        return;
      }
      window.close();
    },
    async hide() {
      visible = false;
      await desktop?.hideWindow?.();
    },
    async minimize() {
      await desktop?.minimizeWindow?.();
    },
    async maximize() {
      maximized = true;
      await desktop?.maximizeWindow?.();
    },
    async unmaximize() {
      maximized = false;
      await desktop?.unmaximizeWindow?.();
    },
    async isMaximized() {
      if (typeof desktop?.isMaximized === 'function') {
        return desktop.isMaximized();
      }
      return maximized;
    },
    async isVisible() {
      if (typeof desktop?.isVisible === 'function') {
        return desktop.isVisible();
      }
      return visible;
    },
    async listen(eventName, callback) {
      if (typeof desktop?.listenWindowEvent === 'function') {
        return desktop.listenWindowEvent(eventName, callback);
      }
      const handler = (event) => callback({ payload: event.detail });
      window.addEventListener(eventName, handler);
      return async () => {
        window.removeEventListener(eventName, handler);
      };
    },
  };
}

export function getCurrentWindow() {
  const desktop = getDesktopApi();

  return {
    async startDragging() {
      await desktop?.startDragging?.();
    },
    async onMoved(callback) {
      if (typeof desktop?.onWindowMoved === 'function') {
        return desktop.onWindowMoved(callback);
      }
      const handler = (event) => callback({ payload: event.detail });
      window.addEventListener('window-moved', handler);
      return async () => {
        window.removeEventListener('window-moved', handler);
      };
    },
  };
}

export async function openDialog(options = {}) {
  const desktop = getDesktopApi();
  if (typeof desktop?.pickDirectory === 'function' && options.directory) {
    return desktop.pickDirectory(options);
  }
  return null;
}

export async function ask(message, options = {}) {
  const desktop = getDesktopApi();
  if (typeof desktop?.confirm === 'function') {
    return desktop.confirm({
      message,
      ...options,
    });
  }
  return window.confirm(message);
}
