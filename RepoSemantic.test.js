import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('README 与 About 语义应保持 Python 宿主表述，不再依赖 src-tauri 图标路径', () => {
  const readmeSource = readFileSync(new URL('./README.md', import.meta.url), 'utf8');
  const readmeEnSource = readFileSync(new URL('./README.en.md', import.meta.url), 'utf8');
  const readmeTwSource = readFileSync(new URL('./README.tw.md', import.meta.url), 'utf8');
  const aboutSource = readFileSync(new URL('./src/routes/about/About.svelte', import.meta.url), 'utf8');

  assert.doesNotMatch(readmeSource, /src-tauri\/icons\/icon\.png/);
  assert.doesNotMatch(readmeEnSource, /src-tauri\/icons\/icon\.png/);
  assert.doesNotMatch(readmeTwSource, /src-tauri\/icons\/icon\.png/);
  assert.match(readmeSource, /Activity Review/);
  assert.match(readmeEnSource, /Activity Review/);
  assert.match(readmeTwSource, /Activity Review/);
  assert.match(aboutSource, /Activity Review/);
  assert.match(readmeSource, /Python%20%2B%20PyWebView%20%2B%20Svelte/);
  assert.match(readmeEnSource, /Python%20%2B%20PyWebView%20%2B%20Svelte/);
  assert.match(readmeTwSource, /Python%20%2B%20PyWebView%20%2B%20Svelte/);
  assert.match(aboutSource, /Python Backend/);
  assert.match(aboutSource, /Desktop Bridge/);
  assert.doesNotMatch(aboutSource, />Tauri 2</);
  assert.doesNotMatch(aboutSource, />Rust</);
});
