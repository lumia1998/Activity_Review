import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('Cargo.toml 历史兼容快照应继续保留 cargo-clippy feature 断言', () => {
  const source = readFileSync(new URL('./src-tauri/Cargo.toml', import.meta.url), 'utf8');

  assert.match(
    source,
    /\[features\][\s\S]*\bcargo-clippy\s*=\s*\[\s*\]/,
    '需要显式声明 cargo-clippy feature，兼容旧 objc 宏里的 cfg(feature = "cargo-clippy")'
  );
});
