import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('AI 设置中的 API 密钥输入应支持显示与隐藏切换', async () => {
  const source = await readFile(
    new URL('./components/SettingsAI.svelte', import.meta.url),
    'utf8'
  );

  assert.match(source, /let showApiKey = false;/);
  assert.match(source, /\{#if showApiKey\}/);
  assert.match(source, /type="text"/);
  assert.match(source, /type="password"/);
  assert.match(source, /aria-label=\{showApiKey \? '隐藏 API 密钥' : '显示 API 密钥'\}/);
});

test('日报导出目录应从 AI 设置移到存储设置', async () => {
  const aiSource = await readFile(
    new URL('./components/SettingsAI.svelte', import.meta.url),
    'utf8'
  );
  const storageSource = await readFile(
    new URL('./components/SettingsStorage.svelte', import.meta.url),
    'utf8'
  );

  assert.doesNotMatch(aiSource, /日报 Markdown 导出目录/);
  assert.match(storageSource, /日报 Markdown 导出目录/);
  assert.match(storageSource, /pickDailyReportExportDir/);
  assert.match(storageSource, /自动导出 YYYY-MM-DD\.md/);
  assert.match(storageSource, /设置日报 Markdown 默认下载位置。/);
  assert.match(storageSource, /h3 class="settings-card-title">截图与保留</);
  assert.match(storageSource, /h3 class="settings-card-title">日报导出</);
  assert.match(storageSource, /h3 class="settings-card-title">数据目录与清理</);
  assert.match(storageSource, /整桌面拼接截图/);
  assert.match(storageSource, /把所有显示器内容拼成一张完整截图/);
});

test('Ollama 提供商应支持获取模型列表并保留手动输入回退', async () => {
  const source = await readFile(
    new URL('./components/SettingsAI.svelte', import.meta.url),
    'utf8'
  );

  assert.match(source, /invoke\('get_ollama_models'/);
  assert.match(source, /refreshOllamaModels/);
  assert.match(source, /ollamaModels/);
  assert.match(source, /provider === 'ollama'/);
  assert.match(source, /<select/);
  assert.match(source, /手动输入模型名称/);
  assert.match(source, /刷新模型列表/);
});

test('Ollama 刷新模型列表后应给出反馈并在当前模型失效时自动回填可用模型', async () => {
  const source = await readFile(
    new URL('./components/SettingsAI.svelte', import.meta.url),
    'utf8'
  );

  assert.match(source, /!ollamaModels.includes\(config\.text_model\.model\)/);
  assert.match(source, /已获取 \$\{ollamaModels\.length\} 个模型/);
});

test('Ollama 模型列表为空时应保留当前模型值，避免下拉框显示空白', async () => {
  const source = await readFile(
    new URL('./components/SettingsAI.svelte', import.meta.url),
    'utf8'
  );

  assert.match(source, /let selectedOllamaModel = '';/);
  assert.match(source, /function getOllamaFallbackOptionLabel\(\)/);
  assert.match(source, /当前配置：\$\{currentModel\}/);
  assert.match(source, /\{getOllamaFallbackOptionLabel\(\)\}/);
});

test('Ollama 下拉列表应只展示实际返回的模型，并明确区分手动输入值', async () => {
  const source = await readFile(
    new URL('./components/SettingsAI.svelte', import.meta.url),
    'utf8'
  );

  assert.doesNotMatch(source, /return \[config\.text_model\.model, \.\.\.ollamaModels\];/);
  assert.match(source, /当前手动输入的模型不在 Ollama 列表中/);
  assert.match(source, /#each ollamaModels as model \(model\)/);
});
