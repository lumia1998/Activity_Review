import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('Python 桌面宿主应通过 pywebview js_api 注入桌面桥接并监听 runtime 状态', async () => {
  const [mainSource, traySource, pyprojectSource, configSource, settingsSource] = await Promise.all([
    readFile(new URL('../../../desktop/main.py', import.meta.url), 'utf8'),
    readFile(new URL('../../../desktop/tray.py', import.meta.url), 'utf8'),
    readFile(new URL('../../../pyproject.toml', import.meta.url), 'utf8'),
    readFile(new URL('../../../backend/app/services/config_service.py', import.meta.url), 'utf8'),
    readFile(new URL('../../routes/settings/Settings.svelte', import.meta.url), 'utf8'),
  ]);

  assert.match(mainSource, /js_api=desktop_api/);
  assert.match(mainSource, /window\.__ACTICITY_DESKTOP__/);
  assert.match(mainSource, /create_confirmation_dialog/);
  assert.match(mainSource, /create_file_dialog\(/);
  assert.match(mainSource, /listenWindowEvent: \(eventName, callback\) => \{/);
  assert.match(mainSource, /api\.listenWindowEvent\(eventName\);/);
  assert.match(mainSource, /onWindowMoved: \(callback\) => \{/);
  assert.match(mainSource, /api\.onWindowMoved\(\);/);
  assert.match(mainSource, /window\.addEventListener\('window-moved', handler\)/);
  assert.match(mainSource, /window\.removeEventListener\('window-moved', handler\)/);
  assert.match(mainSource, /window\.events\.loaded \+= on_loaded/);
  assert.match(mainSource, /window\.events\.moved \+= on_moved/);
  assert.match(mainSource, /window\.events\.minimized \+= on_minimized/);
  assert.match(mainSource, /window\.events\.restored \+= on_restored/);
  assert.match(mainSource, /window\.maximize\(\)/);
  assert.match(mainSource, /window\.restore\(\)/);
  assert.match(mainSource, /window-maximized/);
  assert.match(mainSource, /window-minimized/);
  assert.match(mainSource, /window-visibility-changed/);
  assert.match(mainSource, /create_tray_controller\(/);
  assert.match(mainSource, /dock_visible/);
  assert.match(traySource, /class TrayController:/);
  assert.match(traySource, /pystray\.Icon/);
  assert.match(traySource, /MenuItem\('显示主界面'/);
  assert.match(pyprojectSource, /"pystray>=0\.19\.5"/);
  assert.match(pyprojectSource, /"Pillow>=10\.4\.0"/);
  assert.match(configSource, /"hide_dock_icon": False/);
  assert.match(settingsSource, /config\.hide_dock_icon = false;/);
});
