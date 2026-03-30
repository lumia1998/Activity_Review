import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('关于页应提供赞助支持按钮并展示微信与支付宝收款码', async () => {
  const source = await readFile(new URL('./About.svelte', import.meta.url), 'utf8');

  assert.match(source, /let isSponsorshipOpen = false;/);
  assert.match(source, /赞助支持/);
  assert.match(source, /text-rose-500/);
  assert.match(source, /微信赞赏/);
  assert.match(source, /支付宝赞赏/);
  assert.match(source, /docs\/sponsorship\/vx\.png/);
  assert.match(source, /docs\/sponsorship\/zfb\.png/);
});

test('关于页赞助弹层应展示鼓励文案，检查更新按钮应单独居中', async () => {
  const source = await readFile(new URL('./About.svelte', import.meta.url), 'utf8');

  assert.match(source, /如果这个项目对你有帮助，帮你省了点时间，欢迎请我喝杯咖啡 ☕/);
  assert.match(source, /你的支持会让我持续维护和改进这个项目～/);
  assert.doesNotMatch(source, /推荐微信扫码支持/);
  assert.doesNotMatch(source, /也可以使用支付宝扫码/);
  assert.match(source, /if \(event\.key === 'Escape' && isSponsorshipOpen\)/);
  assert.ok(
    source.indexOf('<span class="leading-none">赞助支持</span>')
      < source.indexOf('<span class="leading-none">检查更新</span>'),
    '赞助支持按钮应位于检查更新之前的首排按钮区'
  );
  assert.ok(
    source.indexOf('<div class="flex justify-center">')
      < source.indexOf('<span class="leading-none">检查更新</span>'),
    '检查更新按钮应放在单独居中的第二排'
  );
});
