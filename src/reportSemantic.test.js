import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('日报生成应在网站访问部分保留域名与语义分类相关数据来源', async () => {
  const [dataServiceSource, runtimeServiceSource, reportServiceSource] = await Promise.all([
    readFile(new URL('../backend/app/services/data_service.py', import.meta.url), 'utf8'),
    readFile(new URL('../backend/app/services/runtime_service.py', import.meta.url), 'utf8'),
    readFile(new URL('../backend/app/services/report_service.py', import.meta.url), 'utf8'),
  ]);

  assert.match(dataServiceSource, /semantic_category TEXT/);
  assert.match(dataServiceSource, /"semantic_category": domain.get\("semantic_category"\)/);
  assert.match(runtimeServiceSource, /semantic_category = _normalize_text\(payload.get\('semanticCategory'\)\) or None/);
  assert.match(reportServiceSource, /browser_url = item.get\("browser_url"\) or ""/);
  assert.match(reportServiceSource, /domain_usage_map\[domain\] = domain_usage_map.get\(domain, 0\) \+ int\(item.get\("duration"\) or 0\)/);
});

test('日报生成应体现按小时活跃度分布', async () => {
  const [dataServiceSource, reportServiceSource] = await Promise.all([
    readFile(new URL('../backend/app/services/data_service.py', import.meta.url), 'utf8'),
    readFile(new URL('../backend/app/services/report_service.py', import.meta.url), 'utf8'),
  ]);

  assert.match(dataServiceSource, /"hourly_activity_distribution": hourly_activity_distribution/);
  assert.match(reportServiceSource, /## 5\. \{labels\['hourly'\]\}/);
  assert.match(reportServiceSource, /for summary in summaries\[:12\]:/);
});
