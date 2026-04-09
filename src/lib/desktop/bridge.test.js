import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('桌面桥接的 ask 应保留标题等确认参数，而不是只透传纯消息字符串', async () => {
  const [bridgeSource, storageSource] = await Promise.all([
    readFile(new URL('./bridge.js', import.meta.url), 'utf8'),
    readFile(new URL('../../routes/settings/components/SettingsStorage.svelte', import.meta.url), 'utf8'),
  ]);

  assert.match(bridgeSource, /export async function ask\(message, options = \{\}\)/);
  assert.match(bridgeSource, /return desktop\.confirm\(\{[\s\S]*message,[\s\S]*\.\.\.options,[\s\S]*\}\)/);
  assert.match(storageSource, /await ask\(t\('settingsStorage\.clearHistoryConfirmMessage'\), \{/);
  assert.match(storageSource, /title: t\('settingsStorage\.clearHistoryConfirmTitle'\)/);
});
