import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('宿主相关文案应描述当前支持边界，而不是继续标记为未实现占位', async () => {
  const [i18nSource, sidebarSource, desktopInitSource] = await Promise.all([
    readFile(new URL('./lib/i18n/index.js', import.meta.url), 'utf8'),
    readFile(new URL('./lib/components/Sidebar.svelte', import.meta.url), 'utf8'),
    readFile(new URL('../desktop/__init__.py', import.meta.url), 'utf8'),
  ]);

  assert.match(i18nSource, /autoStartUnsupported: '当前宿主暂不支持系统自启动控制'/);
  assert.match(i18nSource, /hideDockIconUnsupported: '当前宿主暂不支持 Dock \/ 托盘显隐控制'/);
  assert.match(i18nSource, /autoStartUnsupported: 'The current desktop host does not support system autostart control'/);
  assert.match(i18nSource, /hideDockIconUnsupported: 'The current desktop host does not support Dock \/ tray visibility control'/);
  assert.match(sidebarSource, /录制控制失败/);
  assert.doesNotMatch(sidebarSource, /录制控制暂未实现/);
  assert.equal(desktopInitSource.trim(), '# Desktop shell package.');
});
