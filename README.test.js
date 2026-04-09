import test from 'node:test';
import assert from 'node:assert/strict';
import { access, readFile } from 'node:fs/promises';

test('README 应提供中英文切换入口并包含英文文档', async () => {
  const source = await readFile(new URL('./README.md', import.meta.url), 'utf8');

  assert.match(
    source,
    /href="\.\/*README\.en\.md"[^>]*>English<\/a>/,
    'README 顶部应提供 English 切换链接'
  );
  assert.match(
    source,
    /href="\.\/*README\.md"[^>]*>中文<\/a>/,
    'README 顶部应保留中文入口，形成双语切换'
  );

  await access(new URL('./README.en.md', import.meta.url));
});

test('中英文 README 底部都应展示 Star History，并在 License 后加入分隔线', async () => {
  const [zhSource, enSource] = await Promise.all([
    readFile(new URL('./README.md', import.meta.url), 'utf8'),
    readFile(new URL('./README.en.md', import.meta.url), 'utf8'),
  ]);

  assert.match(zhSource, /Activity Review/);
  assert.match(enSource, /Activity Review/);
  assert.match(zhSource, /## License\s+MIT\s+---\s+## 历史星标/s);
  assert.match(enSource, /## License\s+MIT\s+---\s+## Star History/s);
  assert.match(enSource, /star-history\.com\/#lumia1998\/Acticity_Review&Date/);
});
