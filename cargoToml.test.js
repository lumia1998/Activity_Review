import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';

test('src-tauri Cargo.toml 已从 Python 主线中移除', () => {
  assert.equal(existsSync(new URL('./src-tauri/Cargo.toml', import.meta.url)), false);
});
