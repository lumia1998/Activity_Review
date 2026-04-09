import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('前端 invoke 分发不应再保留 unsupportedFeature 占位分支', async () => {
  const source = await readFile(new URL('./lib/api/client.js', import.meta.url), 'utf8');

  assert.doesNotMatch(source, /function unsupportedFeature\(/);
  assert.doesNotMatch(source, /return unsupportedFeature\(command\);/);
  assert.match(source, /case 'set_dock_visibility':/);
  assert.match(source, /request\('\/api\/runtime\/set-dock-visibility'/);
  assert.match(source, /case 'enable_autostart':/);
  assert.match(source, /request\('\/api\/runtime\/enable-autostart'/);
  assert.match(source, /case 'disable_autostart':/);
  assert.match(source, /request\('\/api\/runtime\/disable-autostart'/);
  assert.match(source, /case 'check_github_update':/);
  assert.match(source, /request\('\/api\/runtime\/check-github-update'/);
  assert.match(source, /throw new Error\(`invoke not implemented: \$\{command\}`\);/);
});
