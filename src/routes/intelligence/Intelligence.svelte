<script>
  import { invoke } from '$lib/runtime.js';
  import { formatDurationLocalized, locale, t } from '$lib/i18n/index.js';
  import LocalizedDatePicker from '../../lib/components/LocalizedDatePicker.svelte';

  function getLocalDateString() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  }

  function getWeekStartDateString() {
    const now = new Date();
    const day = now.getDay() || 7;
    now.setDate(now.getDate() - day + 1);
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  }

  function formatTimestamp(timestamp) {
    if (!timestamp) return '-';
    return new Date(timestamp * 1000).toLocaleString(currentLocale);
  }

  let dateFrom = getWeekStartDateString();
  let dateTo = getLocalDateString();
  let sessions = [];
  let intents = [];
  let weeklyReview = null;
  let todos = [];
  let todoSummary = '';
  let loading = true;
  let error = null;
  let lastQueryKey = '';
  $: currentLocale = $locale;
  $: queryKey = `${dateFrom}:${dateTo}:${currentLocale}`;

  async function loadIntelligence() {
    loading = true;
    error = null;
    try {
      const [nextSessions, nextIntents, nextReview, nextTodos] = await Promise.all([
        invoke('get_work_sessions', { dateFrom, dateTo }),
        invoke('recognize_work_intents', { dateFrom, dateTo }),
        invoke('generate_weekly_review', { dateFrom, dateTo }),
        invoke('extract_todo_items', { dateFrom, dateTo }),
      ]);
      sessions = Array.isArray(nextSessions) ? nextSessions : [];
      intents = Array.isArray(nextIntents?.summary) ? nextIntents.summary : [];
      weeklyReview = nextReview || null;
      todos = Array.isArray(nextTodos?.items) ? nextTodos.items : [];
      todoSummary = nextTodos?.summary || '';
    } catch (e) {
      error = e?.message || String(e);
    } finally {
      loading = false;
    }
  }

  $: if (dateFrom && dateTo && queryKey !== lastQueryKey) {
    lastQueryKey = queryKey;
    loadIntelligence();
  }
</script>

<div class="p-6 animate-fadeIn space-y-6" data-locale={currentLocale}>
  <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
    <div>
      <h2 class="text-lg font-semibold text-slate-800 dark:text-white">{t('timelineSummary.intelligenceTitle')}</h2>
      <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">{t('timelineSummary.intelligenceSubtitle')}</p>
    </div>

    <div class="flex flex-wrap gap-3 items-center">
      {#key `intelligence-from-${currentLocale}`}
        <LocalizedDatePicker bind:value={dateFrom} max={dateTo} localeCode={currentLocale} triggerClass="page-control-input w-auto" />
      {/key}
      {#key `intelligence-to-${currentLocale}`}
        <LocalizedDatePicker bind:value={dateTo} min={dateFrom} max={getLocalDateString()} localeCode={currentLocale} triggerClass="page-control-input w-auto" />
      {/key}
      <button class="page-action-secondary min-h-10 px-4 py-2" on:click={loadIntelligence} disabled={loading}>
        {loading ? t('timelineSummary.loading') : t('timelineSummary.loadAction')}
      </button>
    </div>
  </div>

  {#if error}
    <div class="card p-4 text-sm text-red-500">{error}</div>
  {/if}

  <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
    <div class="card p-4">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-base font-semibold text-slate-800 dark:text-white">{t('timelineSummary.sessionsTitle')}</h3>
        <span class="text-xs text-slate-400">{t('timelineSummary.sessionsCount', { count: sessions.length })}</span>
      </div>
      {#if !loading && sessions.length === 0}
        <p class="text-sm text-slate-500 dark:text-slate-400">{t('timelineSummary.emptySessions')}</p>
      {:else}
        <div class="space-y-3 max-h-[28rem] overflow-auto pr-1">
          {#each sessions as session}
            <div class="rounded-xl border border-slate-200 dark:border-slate-700 p-3 space-y-2">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <div class="font-medium text-slate-800 dark:text-slate-100">{session.title || session.dominantApp}</div>
                  <div class="text-xs text-slate-400">{formatTimestamp(session.startTimestamp)} - {formatTimestamp(session.endTimestamp)}</div>
                </div>
                <div class="text-right shrink-0">
                  <div class="text-sm font-semibold text-primary-600 dark:text-primary-400">{formatDurationLocalized(session.duration)}</div>
                  <div class="text-xs text-slate-400">{session.intentLabel}</div>
                </div>
              </div>
              <div class="flex flex-wrap gap-2 text-xs">
                <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{t('timelineSummary.confidence')}: {session.intentConfidence}</span>
                {#if session.topApps?.length}
                  <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{t('timelineSummary.topApps')}: {session.topApps.map((item) => item.name).slice(0, 3).join(', ')}</span>
                {/if}
                {#if session.topKeywords?.length}
                  <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{t('timelineSummary.topKeywords')}: {session.topKeywords.slice(0, 4).join(', ')}</span>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="space-y-4">
      <div class="card p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-base font-semibold text-slate-800 dark:text-white">{t('timelineSummary.intentsTitle')}</h3>
          <span class="text-xs text-slate-400">{t('timelineSummary.intentsCount', { count: intents.length })}</span>
        </div>
        {#if !loading && intents.length === 0}
          <p class="text-sm text-slate-500 dark:text-slate-400">{t('timelineSummary.noData')}</p>
        {:else}
          <div class="space-y-2">
            {#each intents as intent}
              <div>
                <div class="flex items-center justify-between text-sm mb-1">
                  <span class="text-slate-700 dark:text-slate-200">{intent.label}</span>
                  <span class="text-slate-400">{formatDurationLocalized(intent.duration)}</span>
                </div>
                <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
                  <div class="h-full bg-primary-500 rounded-full" style={`width: ${Math.max(8, Math.min(100, intents[0]?.duration ? (intent.duration / intents[0].duration) * 100 : 0))}%`}></div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <div class="card p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-base font-semibold text-slate-800 dark:text-white">{t('timelineSummary.todosTitle')}</h3>
          <span class="text-xs text-slate-400">{t('timelineSummary.todosCount', { count: todos.length })}</span>
        </div>
        {#if !loading && todos.length === 0}
          <p class="text-sm text-slate-500 dark:text-slate-400">{t('timelineSummary.emptyTodos')}</p>
        {:else}
          <div class="space-y-2 max-h-64 overflow-auto pr-1">
            {#each todos as item}
              <div class="rounded-xl border border-slate-200 dark:border-slate-700 p-3">
                <div class="font-medium text-sm text-slate-800 dark:text-slate-100">{item.title}</div>
                <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('timelineSummary.source')}: {item.sourceApp} / {item.sourceTitle}</div>
              </div>
            {/each}
          </div>
          {#if todoSummary}
            <p class="text-xs text-slate-400 mt-3">{todoSummary}</p>
          {/if}
        {/if}
      </div>
    </div>
  </div>

  <div class="card p-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-base font-semibold text-slate-800 dark:text-white">{t('timelineSummary.weeklyReviewTitle')}</h3>
      {#if weeklyReview}
        <div class="flex flex-wrap gap-2 text-xs text-slate-400 justify-end">
          <span>{t('timelineSummary.totalDuration')}: {formatDurationLocalized(weeklyReview.totalDuration)}</span>
          <span>{t('timelineSummary.activeDays')}: {weeklyReview.activeDays}</span>
          <span>{t('timelineSummary.sessionCount')}: {weeklyReview.sessionCount}</span>
          <span>{t('timelineSummary.deepWorkSessions')}: {weeklyReview.deepWorkSessions}</span>
        </div>
      {/if}
    </div>
    {#if !loading && !weeklyReview}
      <p class="text-sm text-slate-500 dark:text-slate-400">{t('timelineSummary.emptyReview')}</p>
    {:else if weeklyReview}
      <div class="space-y-3">
        {#if weeklyReview.highlights?.length}
          <div>
            <div class="text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">Highlights</div>
            <ul class="text-sm text-slate-600 dark:text-slate-300 space-y-1">
              {#each weeklyReview.highlights as item}
                <li>• {item}</li>
              {/each}
            </ul>
          </div>
        {/if}
        {#if weeklyReview.risks?.length}
          <div>
            <div class="text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">Risks</div>
            <ul class="text-sm text-slate-600 dark:text-slate-300 space-y-1">
              {#each weeklyReview.risks as item}
                <li>• {item}</li>
              {/each}
            </ul>
          </div>
        {/if}
        {#if weeklyReview.markdown}
          <pre class="whitespace-pre-wrap text-sm text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-900 rounded-xl p-4 overflow-auto">{weeklyReview.markdown}</pre>
        {/if}
      </div>
    {/if}
  </div>
</div>
