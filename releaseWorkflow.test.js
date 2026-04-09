import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('Release workflow 应在构建前执行前端测试，并避免继续强依赖 Rust/Tauri 构建步骤', () => {
  const source = readFileSync(new URL('./.github/workflows/release.yml', import.meta.url), 'utf8');

  assert.match(source, /run:\s*npm ci/);
  assert.match(source, /name:\s*Run frontend tests/);
  assert.match(source, /activity-review-/);
  assert.match(source, /name:\s*"Activity_Review \$\{\{ github\.ref_name \}\}"/);
  assert.doesNotMatch(source, /name:\s*Build frontend assets for Rust tests/);
  assert.doesNotMatch(source, /name:\s*Run Rust tests/);
  assert.doesNotMatch(source, /cargo test --manifest-path src-tauri\/Cargo\.toml/);

  const frontendIndex = source.indexOf('name: Run frontend tests');
  const buildIndex = source.indexOf('name: Build application');

  assert.notEqual(frontendIndex, -1);
  assert.notEqual(buildIndex, -1);
  assert.ok(frontendIndex < buildIndex, '前端测试必须先于构建执行');
});
