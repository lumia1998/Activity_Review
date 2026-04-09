import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('前端应向日报生成与工作助手透传当前 locale，并让日期输入跟随语言切换', async () => {
  const [appSource, reportSource, askSource, timelineSource, summarySource] = await Promise.all([
    readFile(new URL('./App.svelte', import.meta.url), 'utf8'),
    readFile(new URL('./routes/report/Report.svelte', import.meta.url), 'utf8'),
    readFile(new URL('./routes/ask/Ask.svelte', import.meta.url), 'utf8'),
    readFile(new URL('./routes/timeline/Timeline.svelte', import.meta.url), 'utf8'),
    readFile(new URL('./routes/timeline/Summary.svelte', import.meta.url), 'utf8'),
  ]);

  assert.match(appSource, /const reportCacheKey = `\$\{today\}:\$\{currentLocale \|\| 'zh-CN'\}`/);
  assert.match(appSource, /invoke\('get_saved_report', \{ date: today, locale: currentLocale \}\)/);
  assert.match(appSource, /cache\.invalidate\('report', reportCacheKey\)/);
  assert.match(appSource, /invoke\('generate_report', \{ date: today, force: false, locale: currentLocale \}\)/);
  assert.match(reportSource, /invoke\('generate_report', \{ date: selectedDate, force, locale: currentLocale \}\)/);
  assert.match(reportSource, /invoke\('get_saved_report', \{ date: selectedDate, locale: currentLocale \}\)/);
  assert.match(askSource, /invoke\('chat_work_assistant', \{[\s\S]*locale: currentLocale,[\s\S]*\}\)/);

  assert.match(reportSource, /LocalizedDatePicker/);
  assert.match(timelineSource, /LocalizedDatePicker/);
  assert.match(summarySource, /LocalizedDatePicker/);
  assert.match(reportSource, /localeCode=\{currentLocale\}/);
  assert.match(timelineSource, /localeCode=\{currentLocale\}/);
  assert.match(summarySource, /localeCode=\{currentLocale\}/);
});

test('助手页展示层不应继续依赖写死中文的工作智能工具函数', async () => {
  const [askSource, workIntelligenceSource] = await Promise.all([
    readFile(new URL('./routes/ask/Ask.svelte', import.meta.url), 'utf8'),
    readFile(new URL('./lib/utils/workIntelligence.js', import.meta.url), 'utf8'),
  ]);

  assert.doesNotMatch(askSource, /from '\.\.\/\.\.\/lib\/utils\/workIntelligence\.js'/);
  assert.match(askSource, /formatDurationLocalized/);
  assert.doesNotMatch(workIntelligenceSource, /toLocaleString\('zh-CN'/);
});

test('Python 重构版后端日报链路应支持按 locale 存取与生成', async () => {
  const [reportsApiSource, reportServiceSource, dataServiceSource, assistantApiSource] = await Promise.all([
    readFile(new URL('../backend/app/api/reports.py', import.meta.url), 'utf8'),
    readFile(new URL('../backend/app/services/report_service.py', import.meta.url), 'utf8'),
    readFile(new URL('../backend/app/services/data_service.py', import.meta.url), 'utf8'),
    readFile(new URL('../backend/app/api/assistant.py', import.meta.url), 'utf8'),
  ]);

  assert.match(reportsApiSource, /locale: str \| None = None/);
  assert.match(reportsApiSource, /return get_report\(date, locale\)/);
  assert.match(reportsApiSource, /return generate_report_for_date\(payload\.date, payload\.force, payload\.locale\)/);
  assert.match(reportServiceSource, /def _normalize_locale\(locale: str \| None\) -> str:/);
  assert.match(reportServiceSource, /def _report_labels\(locale: str\) -> dict\[str, str\]:/);
  assert.match(reportServiceSource, /normalized_locale = _normalize_locale\(locale\)/);
  assert.match(dataServiceSource, /PRIMARY KEY \(date, locale\)/);
  assert.match(assistantApiSource, /locale: str \| None = None/);
});
