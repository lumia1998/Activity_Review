import { invoke as apiInvoke } from '$lib/api/client.js';
import { listen as apiListen } from '$lib/api/events.js';
import {
  ask,
  emitTo,
  getCurrentWebviewWindow,
  getCurrentWindow,
  getVersion,
  open,
  openDialog,
  relaunch,
} from '$lib/desktop/bridge.js';

export const invoke = apiInvoke;
export const listen = apiListen;
export { ask, emitTo, getCurrentWebviewWindow, getCurrentWindow, getVersion, open, openDialog, relaunch };
