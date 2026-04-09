import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('Cargo 旧测试应明确标记为历史兼容快照，而不是当前桌面宿主主链', () => {
  const source = readFileSync(new URL('./cargoToml.test.js', import.meta.url), 'utf8');

  assert.match(source, /历史兼容快照/);
  assert.match(source, /src-tauri\/Cargo\.toml/);
});
