import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('应提供 MiniMax 作为新的 AI 提供商并同步到前端默认配置与文档', async () => {
  const [clientSource, assistantServiceSource, readmeSource, readmeEnSource] = await Promise.all([
    readFile(new URL('./lib/api/client.js', import.meta.url), 'utf8'),
    readFile(new URL('../backend/app/services/assistant_service.py', import.meta.url), 'utf8'),
    readFile(new URL('../README.md', import.meta.url), 'utf8'),
    readFile(new URL('../README.en.md', import.meta.url), 'utf8'),
  ]);

  assert.match(clientSource, /id: 'minimax'/);
  assert.match(clientSource, /name: 'MiniMax'/);
  assert.match(clientSource, /default_endpoint: 'https:\/\/api\.minimaxi\.com\/v1'/);
  assert.match(assistantServiceSource, /'minimax'/);
  assert.match(assistantServiceSource, /url = f'\{endpoint\}\/chat\/completions'/);
  assert.match(readmeSource, /MiniMax/);
  assert.match(readmeEnSource, /MiniMax/);
});
