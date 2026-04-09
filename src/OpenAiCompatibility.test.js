import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('AI 连接测试应使用配置的兼容端点，而不是写死官方 OpenAI 地址', async () => {
  const source = await readFile(new URL('../backend/app/services/assistant_service.py', import.meta.url), 'utf8');

  assert.doesNotMatch(source, /https:\/\/api\.openai\.com\/v1\/chat\/completions/);
  assert.match(source, /endpoint = _normalize_endpoint\(model_config.get\('endpoint'\)\)/);
  assert.match(source, /url = f'\{endpoint\}\/chat\/completions'/);
});
