import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('后端检查更新应返回当前发布是否支持自动更新安装，并在当前阶段明确标记为手动引导', async () => {
  const [runtimeApiSource, updateServiceSource] = await Promise.all([
    readFile(new URL('../backend/app/api/runtime.py', import.meta.url), 'utf8'),
    readFile(new URL('../backend/app/services/update_service.py', import.meta.url), 'utf8'),
  ]);

  assert.match(runtimeApiSource, /@router\.post\('\/check-github-update'\)/);
  assert.match(runtimeApiSource, /return check_github_update\(/);
  assert.match(updateServiceSource, /def check_github_update\(/);
  assert.match(updateServiceSource, /'autoUpdateReady': False/);
  assert.match(updateServiceSource, /RELEASES_PAGE_URL = 'https:\/\/github\.com\/lumia1998\/Acticity_Review\/releases\/latest'/);
});
