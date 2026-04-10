import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('Cargo 旧测试现应明确断言 src-tauri 已移除', () => {
  const source = readFileSync(new URL('./cargoToml.test.js', import.meta.url), 'utf8');

  assert.match(source, /src-tauri/);
  assert.match(source, /已从 Python 主线中移除/);
});
