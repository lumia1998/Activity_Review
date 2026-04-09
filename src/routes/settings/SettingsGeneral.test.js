import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('工作时间跨零点时应显示跨天后的总时长而不是横线', async () => {
  const source = await readFile(
    new URL('./components/SettingsGeneral.svelte', import.meta.url),
    'utf8'
  );

  assert.match(source, /endTotal === startTotal/);
  assert.match(source, /endTotal < startTotal/);
  assert.match(source, /24 \* 60/);
  assert.doesNotMatch(source, /const diffSeconds = \(endTotal - startTotal\) \* 60;/);
});

test('开始时间等于结束时间时应显示零时长而不是横线', async () => {
  const source = await readFile(
    new URL('./components/SettingsGeneral.svelte', import.meta.url),
    'utf8'
  );

  assert.match(source, /endTotal === startTotal/);
  assert.match(source, /formatDurationLocalized\(0\)/);
});

test('关闭开机自启动失败时不应吞掉所有异常并伪称已经移除成功', async () => {
  const source = await readFile(
    new URL('./components/SettingsGeneral.svelte', import.meta.url),
    'utf8'
  );

  assert.doesNotMatch(source, /未知原因报错os error -2147024891/);
  assert.doesNotMatch(source, /确实已经正常移除了开机自启动/);
});


test('设置页应接入真实自启动开关，并将 Dock 开关接到 runtime API', async () => {
  const [generalSource, i18nSource, clientSource, serviceSource, runtimeApiSource, runtimeServiceSource] = await Promise.all([
    readFile(new URL('./components/SettingsGeneral.svelte', import.meta.url), 'utf8'),
    readFile(new URL('../../lib/i18n/index.js', import.meta.url), 'utf8'),
    readFile(new URL('../../lib/api/client.js', import.meta.url), 'utf8'),
    readFile(new URL('../../../backend/app/services/autostart_service.py', import.meta.url), 'utf8'),
    readFile(new URL('../../../backend/app/api/runtime.py', import.meta.url), 'utf8'),
    readFile(new URL('../../../backend/app/services/runtime_service.py', import.meta.url), 'utf8'),
  ]);

  assert.match(generalSource, /const autoStartSupported = true;/);
  assert.match(generalSource, /const dockVisibilitySupported = true;/);
  assert.match(generalSource, /onMount\(async \(\) => \{/);
  assert.match(generalSource, /autoStartEnabled = await invoke\('is_autostart_enabled'\);/);
  assert.match(generalSource, /await invoke\(autoStartEnabled \? 'disable_autostart' : 'enable_autostart'\);/);
  assert.match(generalSource, /await invoke\('set_dock_visibility', \{ visible: !nextValue \}\);/);
  assert.match(generalSource, /disabled=\{!dockVisibilitySupported\}/);
  assert.match(clientSource, /case 'is_autostart_enabled':[\s\S]*request\('\/api\/runtime\/is-autostart-enabled'/);
  assert.match(clientSource, /case 'enable_autostart':[\s\S]*request\('\/api\/runtime\/enable-autostart'/);
  assert.match(clientSource, /case 'disable_autostart':[\s\S]*request\('\/api\/runtime\/disable-autostart'/);
  assert.match(clientSource, /case 'set_dock_visibility':[\s\S]*request\('\/api\/runtime\/set-dock-visibility'/);
  assert.match(runtimeApiSource, /class DockVisibilityPayload\(BaseModel\):/);
  assert.match(runtimeApiSource, /@router.post\('\/set-dock-visibility'\)/);
  assert.match(serviceSource, /AUTOSTART_FILE_NAME = 'Activity Review\.cmd'/);
  assert.match(runtimeServiceSource, /'dock_visible': True,/);
  assert.match(runtimeServiceSource, /def set_dock_visibility\(visible: bool\) -> bool:/);
  assert.match(serviceSource, /AUTOSTART_FILE_NAME = 'Activity Review\.cmd'/);
  assert.match(i18nSource, /hideDockIconUnsupported:/);
});

test('设置页应在挂载阶段读取真实自启动状态，而不是继续依赖固定 false', async () => {
  const [generalSource, clientSource] = await Promise.all([
    readFile(new URL('./components/SettingsGeneral.svelte', import.meta.url), 'utf8'),
    readFile(new URL('../../lib/api/client.js', import.meta.url), 'utf8'),
  ]);

  assert.match(generalSource, /import \{ createEventDispatcher, onMount \} from 'svelte';/);
  assert.match(generalSource, /invoke\('is_autostart_enabled'\)/);
  assert.doesNotMatch(clientSource, /case 'is_autostart_enabled':[\s\S]*return unsupportedFeature\(command\);/);
});



