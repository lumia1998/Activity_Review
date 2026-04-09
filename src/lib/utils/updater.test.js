import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('发现新版本但当前发布未准备好在线更新时不应继续安装', async () => {
  const source = await readFile(new URL('./updater.js', import.meta.url), 'utf8');

  assert.match(source, /if \(!releaseInfo\.autoUpdateReady\)/);
  assert.match(source, /t\('updater\.availableManual'\)/);
  assert.match(source, /open\(releaseInfo\.releaseUrl\)/);

  const manualBranchIndex = source.indexOf('if (!releaseInfo.autoUpdateReady)');
  const installIndex = source.indexOf("await invoke('download_and_install_github_update'");
  assert.notEqual(manualBranchIndex, -1);
  assert.notEqual(installIndex, -1);
  assert.ok(manualBranchIndex < installIndex);
});

test('更新检查成功后才应记录最后检查时间', async () => {
  const source = await readFile(new URL('./updater.js', import.meta.url), 'utf8');

  assert.match(source, /const releaseInfo = await invoke\('check_github_update'\);/);
  assert.match(source, /await invoke\('update_last_check_time'\)\.catch/);
});

test('更新状态提示应走前端本地化映射，而不是直接展示后端中文状态', async () => {
  const source = await readFile(new URL('./updater.js', import.meta.url), 'utf8');

  assert.match(source, /function localizeRuntimeStatusMessage/);
  assert.match(source, /onStatusChange\(localizeRuntimeStatusMessage\(payload\.message\)\)/);
});

test('Python 重构版的更新能力应命中 runtime API，并在当前阶段退回真实发布页引导', async () => {
  const [clientSource, updaterSource, runtimeSource] = await Promise.all([
    readFile(new URL('../api/client.js', import.meta.url), 'utf8'),
    readFile(new URL('./updater.js', import.meta.url), 'utf8'),
    readFile(new URL('../../../backend/app/services/update_service.py', import.meta.url), 'utf8'),
  ]);

  assert.match(clientSource, /case 'check_github_update':[\s\S]*request\('\/api\/runtime\/check-github-update'/);
  assert.match(clientSource, /case 'update_last_check_time':[\s\S]*request\('\/api\/runtime\/update-last-check-time'/);
  assert.match(clientSource, /case 'download_and_install_github_update':[\s\S]*request\('\/api\/runtime\/download-and-install-github-update'/);
  assert.match(updaterSource, /if \(!releaseInfo\.autoUpdateReady\)/);
  assert.match(updaterSource, /confirmBeforeDownload/);
  assert.match(runtimeSource, /'autoUpdateReady': False/);
  assert.match(runtimeSource, /RELEASES_PAGE_URL = 'https:\/\/github\.com\/lumia1998\/Acticity_Review\/releases\/latest'/);
  assert.doesNotMatch(clientSource, /case 'check_github_update':[\s\S]*return unsupportedFeature\(command\);/);
});


