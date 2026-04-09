import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('Python 重构版当前应明确以录制暂停态作为空闲剔除主开关，而不是继续依赖 Rust 空闲判定链', async () => {
  const [appSource, runtimeSource] = await Promise.all([
    readFile(new URL('./App.svelte', import.meta.url), 'utf8'),
    readFile(new URL('../backend/app/services/runtime_service.py', import.meta.url), 'utf8'),
  ]);

  assert.match(appSource, /if \(document\.hidden \|\| isPaused\) \{/);
  assert.match(runtimeSource, /if _RUNTIME_STATE\.get\('is_paused'\):/);
  assert.match(runtimeSource, /'is_paused'/);
});
