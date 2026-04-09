import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('应用壳层应监听录制状态变更事件并同步侧边栏状态', async () => {
  const source = await readFile(new URL('./App.svelte', import.meta.url), 'utf8');

  assert.match(source, /listen\('recording-state-changed'/);
  assert.match(source, /isRecording\s*=\s*event\.payload\.isRecording/);
  assert.match(source, /isPaused\s*=\s*event\.payload\.isPaused/);
});

test('应用壳层在录制状态能力未实现时应回退到默认显示状态', async () => {
  const source = await readFile(new URL('./App.svelte', import.meta.url), 'utf8');

  assert.match(source, /const \[recording, paused\] = await invoke\('get_recording_state'\);/);
  assert.match(source, /catch \(e\) \{[\s\S]*isRecording = true;[\s\S]*isPaused = false;[\s\S]*\}/);
});

test('托盘和设置的配置变更应回推到前端缓存与设置页', async () => {
  const [appSource, settingsSource, clientSource] = await Promise.all([
    readFile(new URL('./App.svelte', import.meta.url), 'utf8'),
    readFile(new URL('./routes/settings/Settings.svelte', import.meta.url), 'utf8'),
    readFile(new URL('./lib/api/client.js', import.meta.url), 'utf8'),
  ]);

  assert.match(appSource, /listen\('config-changed'/);
  assert.match(appSource, /cache\.setConfig\(event\.payload\)/);
  assert.match(settingsSource, /cache\.subscribe\(\(state\)\s*=>/);
  assert.match(settingsSource, /config\s*=\s*state\.config/);
  assert.match(clientSource, /case 'save_config':[\s\S]*request\('\/api\/config'/);
});

test('轻量模式关闭主界面时应触发窗口关闭而非仅隐藏', async () => {
  const source = await readFile(new URL('./App.svelte', import.meta.url), 'utf8');

  assert.match(source, /runtimeConfig\?\.lightweight_mode/);
  assert.match(source, /await appWindow\.close\(\)/);
  assert.match(source, /await appWindow\.hide\(\)/);
});

test('自动更新检查已收口到关于页手动入口，不应再在应用壳层启动时自动触发', async () => {
  const source = await readFile(new URL('./App.svelte', import.meta.url), 'utf8');

  assert.doesNotMatch(source, /await runUpdateFlow\(/);
  assert.doesNotMatch(source, /invoke\('should_check_updates'\)/);
  assert.doesNotMatch(source, /const autoUpdateTimer = setTimeout/);
  assert.doesNotMatch(source, /clearTimeout\(autoUpdateTimer\)/);
});

test('应用壳层应根据运行时平台决定是否展示自定义窗控，而不是依赖固定 windows 返回', async () => {
  const [appSource, clientSource] = await Promise.all([
    readFile(new URL('./App.svelte', import.meta.url), 'utf8'),
    readFile(new URL('./lib/api/client.js', import.meta.url), 'utf8'),
  ]);

  assert.match(appSource, /platform = await invoke\('get_platform'\);/);
  assert.match(appSource, /platform && platform !== 'macos'/);
  assert.match(clientSource, /case 'get_platform':[\s\S]*return getBrowserPlatform\(\);/);
  assert.doesNotMatch(clientSource, /case 'get_platform':[\s\S]*return 'windows';/);
});

test('更新能力已收口到手动入口，应用壳层不应再通过 should_check_updates 静默自动检查', async () => {
  const [appSource, clientSource] = await Promise.all([
    readFile(new URL('./App.svelte', import.meta.url), 'utf8'),
    readFile(new URL('./lib/api/client.js', import.meta.url), 'utf8'),
  ]);

  assert.doesNotMatch(appSource, /invoke\('should_check_updates'\)/);
  assert.doesNotMatch(appSource, /const autoUpdateTimer = setTimeout/);
  assert.doesNotMatch(appSource, /clearTimeout\(autoUpdateTimer\)/);
  assert.match(clientSource, /case 'should_check_updates':[\s\S]*request\('\/api\/runtime\/should-check-updates'\)/);
});
