import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('后端检查更新应优先验证当前平台存在可安装更新包', async () => {
  const source = await readFile(new URL('../src-tauri/src/commands.rs', import.meta.url), 'utf8');

  assert.match(source, /check_installable_update/);
  assert.match(source, /\.updater_builder\(\)/);
  assert.match(source, /match updater\.check\(\)\.await/);
  assert.match(source, /auto_update_ready: true/);
});
