import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('时间线详情应支持修改应用默认分类并二次确认后回填历史', async () => {
  const source = await readFile(new URL('./Timeline.svelte', import.meta.url), 'utf8');

  assert.match(source, /import\s+\{\s*confirm\s*\}\s+from\s+'\.\.\/\.\.\/lib\/stores\/confirm\.js'/);
  assert.match(source, /invoke\('set_app_category_rule'/);
  assert.match(source, /timeline\.changeCategoryMessage/);
  assert.match(source, /timeline\.detail\.appCategoryHelp/);
  assert.match(source, /syncHistory:\s*true/);
  assert.match(source, /cache\.invalidate\('overview'\)/);
});

test('时间线应用分类修改应命中后端 app-category-rule 接口，而不是前端本地假实现', async () => {
  const [timelineSource, clientSource, backendSource] = await Promise.all([
    readFile(new URL('./Timeline.svelte', import.meta.url), 'utf8'),
    readFile(new URL('../../lib/api/client.js', import.meta.url), 'utf8'),
    readFile(new URL('../../../backend/app/api/config.py', import.meta.url), 'utf8'),
  ]);

  assert.match(timelineSource, /invoke\('set_app_category_rule'/);
  assert.match(clientSource, /case 'set_app_category_rule':[\s\S]*request\('\/api\/config\/app-category-rule'/);
  assert.match(clientSource, /case 'set_domain_semantic_rule':[\s\S]*request\('\/api\/config\/domain-semantic-rule'/);
  assert.match(backendSource, /@router\.post\('\/app-category-rule'\)/);
  assert.match(backendSource, /return set_app_category_rule\(payload\.appName, payload\.category, payload\.syncHistory\)/);
});

