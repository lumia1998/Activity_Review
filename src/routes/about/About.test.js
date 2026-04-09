import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('关于页应提供赞助支持按钮并展示微信与支付宝收款码', async () => {
  const source = await readFile(new URL('./About.svelte', import.meta.url), 'utf8');

  assert.match(source, /let isSponsorshipOpen = false;/);
  assert.match(source, /about\.sponsorship/);
  assert.match(source, /text-rose-500/);
  assert.match(source, /about\.wechat/);
  assert.match(source, /about\.alipay/);
  assert.match(source, /docs\/sponsorship\/vx\.png/);
  assert.match(source, /docs\/sponsorship\/zfb\.png/);
});

test('关于页赞助弹层应展示鼓励文案，检查更新按钮应单独居中', async () => {
  const source = await readFile(new URL('./About.svelte', import.meta.url), 'utf8');

  assert.match(source, /about\.supportCopy/);
  assert.match(source, /about\.supportCopy2/);
  assert.doesNotMatch(source, /推荐微信扫码支持/);
  assert.doesNotMatch(source, /也可以使用支付宝扫码/);
  assert.match(source, /if \(event\.key === 'Escape' && isSponsorshipOpen\)/);
  assert.match(source, /confirmBeforeDownload: true/);
  assert.ok(
    source.indexOf("t('about.sponsorship')")
      < source.indexOf("t('about.checkUpdates')"),
    '赞助支持按钮应位于检查更新之前的首排按钮区'
  );
  assert.ok(
    source.indexOf('<div class="flex justify-center">')
      < source.indexOf("t('about.checkUpdates')"),
    '检查更新按钮应放在单独居中的第二排'
  );
});

test('关于页应展示 Linux 会话兼容性提示，Wayland 状态可直接查看', async () => {
  const source = await readFile(new URL('./About.svelte', import.meta.url), 'utf8');

  assert.match(source, /invoke\('get_linux_session_support'\)/);
  assert.match(source, /about\.linuxSessionTitle/);
  assert.match(source, /about\.linuxSessionWaylandWarning/);
  assert.match(source, /linuxSessionInfo/);
  assert.match(source, /desktopEnvironment/);
  assert.match(source, /activeWindowProvider/);
  assert.match(source, /browserUrlSupportLevel/);
  assert.match(source, /sessionType === 'wayland'/);
  assert.match(source, /about\.linuxSessionGnomeWaylandReady/);
  assert.match(source, /about\.linuxSessionProviderLabel/);
  assert.match(source, /about\.linuxBrowserUrlCapabilityTitle/);
});

test('关于页应展示当前 Python 重构版运行形态，而不是继续标注 Tauri/Rust', async () => {
  const source = await readFile(new URL('./About.svelte', import.meta.url), 'utf8');

  assert.match(source, /Activity Review/);
  assert.match(source, /Python Backend/);
  assert.match(source, /Desktop Bridge/);
  assert.match(source, /Svelte/);
  assert.match(source, /SQLite/);
  assert.doesNotMatch(source, />Tauri 2</);
  assert.doesNotMatch(source, />Rust</);
});

test('Linux 会话信息在非 Linux 环境下不应伪装成 mixed 能力的 windows 会话', async () => {
  const source = await readFile(new URL('../../lib/api/client.js', import.meta.url), 'utf8');

  assert.match(source, /function getLinuxSessionSupport\(/);
  assert.match(source, /if \(platform !== 'linux'\)/);
  assert.match(source, /sessionType: 'unsupported'/);
  assert.match(source, /desktopEnvironment: 'unsupported'/);
  assert.match(source, /browserUrlSupportLevel: 'limited'/);
  assert.doesNotMatch(source, /sessionType: 'native'/);
  assert.doesNotMatch(source, /desktopEnvironment: 'windows'/);
  assert.doesNotMatch(source, /browserUrlSupportLevel: 'mixed'/);
});

test('关于页更新入口应接到真实 runtime 检查，并在当前阶段采用发布页引导', async () => {
  const [aboutSource, updaterSource, runtimeSource] = await Promise.all([
    readFile(new URL('./About.svelte', import.meta.url), 'utf8'),
    readFile(new URL('../../lib/utils/updater.js', import.meta.url), 'utf8'),
    readFile(new URL('../../../backend/app/services/update_service.py', import.meta.url), 'utf8'),
  ]);

  assert.match(aboutSource, /await runUpdateFlow\(/);
  assert.match(aboutSource, /confirmBeforeDownload: true/);
  assert.match(updaterSource, /if \(!releaseInfo\.autoUpdateReady\)/);
  assert.match(updaterSource, /open\(releaseInfo\.releaseUrl\)/);
  assert.match(runtimeSource, /LATEST_RELEASE_API = 'https:\/\/api\.github\.com\/repos\/lumia1998\/Acticity_Review\/releases\/latest'/);
  assert.match(runtimeSource, /'autoUpdateReady': False/);
});

