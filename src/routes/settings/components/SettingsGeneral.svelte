<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { invoke } from '$lib/runtime.js';
  import { formatDurationLocalized, locale, t } from '$lib/i18n/index.js';
  import { showToast } from '../../../lib/stores/toast.js';

  export let config;

  const dispatch = createEventDispatcher();
  $: currentLocale = $locale;
  let workHours = '—';
  const autoStartSupported = true;
  const dockVisibilitySupported = true;

  // 开机自启动状态（独立于 config，由系统 API 驱动）
  let autoStartEnabled = false;

  function showUnsupportedFeatureToast(error) {
    const message = error?.message || '该功能当前宿主暂不支持';
    showToast(message, 'error');
  }


  // 解析工作时间
  $: startHour = config.work_start_hour ?? 9;
  $: startMinute = config.work_start_minute ?? 0;
  $: endHour = config.work_end_hour ?? 18;
  $: endMinute = config.work_end_minute ?? 0;

  // 格式化为 HH:MM
  $: startTimeDisplay = `${String(startHour).padStart(2, '0')}:${String(startMinute).padStart(2, '0')}`;
  $: endTimeDisplay = `${String(endHour).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`;

  // 工作时长
  $: {
    currentLocale;
    const startTotal = startHour * 60 + startMinute;
    const endTotal = endHour * 60 + endMinute;
    const isZeroDuration = endTotal === startTotal;
    const diffMinutes = isZeroDuration
      ? 0
      : endTotal < startTotal
        ? endTotal + 24 * 60 - startTotal
        : endTotal - startTotal;
    const diffSeconds = diffMinutes * 60;
    workHours = isZeroDuration ? formatDurationLocalized(0) : formatDurationLocalized(diffSeconds);
  }

  function updateStart(h, m) {
    config.work_start_hour = h;
    config.work_start_minute = m;
    dispatch('change', config);
  }

  function updateEnd(h, m) {
    config.work_end_hour = h;
    config.work_end_minute = m;
    dispatch('change', config);
  }

  function handleChange() {
    dispatch('change', config);
  }

  onMount(async () => {
    try {
      autoStartEnabled = await invoke('is_autostart_enabled');
      config.auto_start = autoStartEnabled;
    } catch (e) {
      console.error('读取开机自启动状态失败:', e);
      autoStartEnabled = false;
      config.auto_start = false;
    }
  });

  // 开机自启动切换
  async function toggleAutoStart() {
    if (!autoStartSupported) {
      showToast(t('settingsGeneral.autoStartUnsupported'), 'error');
      return;
    }

    try {
      await invoke(autoStartEnabled ? 'disable_autostart' : 'enable_autostart');
      autoStartEnabled = !autoStartEnabled;
      config.auto_start = autoStartEnabled;
      dispatch('change', config);
    } catch (e) {
      console.error('设置开机自启动失败:', e);
      showUnsupportedFeatureToast(e);
    }
  }

  // Dock 图标
  async function toggleDockIcon() {
    if (!dockVisibilitySupported) {
      showToast(t('settingsGeneral.hideDockIconUnsupported'), 'error');
      return;
    }

    const nextValue = !config.hide_dock_icon;
    try {
      await invoke('set_dock_visibility', { visible: !nextValue });
      config.hide_dock_icon = nextValue;
      dispatch('change', config);
    } catch (e) {
      console.error('设置 Dock 图标失败:', e);
      showUnsupportedFeatureToast(e);
    }
  }

  function toggleLightweightMode() {
    config.lightweight_mode = !config.lightweight_mode;
    dispatch('change', config);
  }

  function updateAutoStartLaunchMode(silentMode) {
    config.auto_start_silent = silentMode;
    dispatch('change', config);
  }

</script>

<!-- 基本设置 -->
<div class="settings-card" data-locale={currentLocale}>
  <h3 class="settings-card-title">{t('settingsGeneral.title')}</h3>
  <p class="settings-card-desc">{t('settingsGeneral.description')}</p>

  <div class="settings-section">
    <!-- 工作时间 -->
    <div class="settings-block">
      <div class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span class="settings-text">{t('settingsGeneral.workTime')}</span>
        <span class="settings-muted">{t('settingsGeneral.totalWorkHours', { duration: workHours })}</span>
      </div>

      <div class="flex items-center gap-3">
        <!-- 开始时间 -->
        <div class="control-inline">
          <span class="settings-subtle">{t('settingsGeneral.from')}</span>
          <input
            type="time"
            value={startTimeDisplay}
            on:change={(e) => {
              const [h, m] = e.target.value.split(':').map(Number);
              updateStart(h, m);
            }}
            class="w-24 bg-transparent text-sm font-mono text-slate-800 dark:text-white focus:outline-none"
          />
        </div>

        <span class="text-slate-300 dark:text-slate-600">—</span>

        <!-- 结束时间 -->
        <div class="control-inline">
          <span class="settings-subtle">{t('settingsGeneral.to')}</span>
          <input
            type="time"
            value={endTimeDisplay}
            on:change={(e) => {
              const [h, m] = e.target.value.split(':').map(Number);
              updateEnd(h, m);
            }}
            class="w-24 bg-transparent text-sm font-mono text-slate-800 dark:text-white focus:outline-none"
          />
        </div>
      </div>
      <p class="settings-note">{t('settingsGeneral.workTimeHint')}</p>
    </div>

    <hr class="border-slate-200 dark:border-slate-700" />

    <!-- 开机自启动 -->
    <div class="flex items-center justify-between gap-4">
      <div>
        <div class="settings-text">{t('settingsGeneral.autoStart')}</div>
        <div class="settings-muted mt-0.5">{t('settingsGeneral.autoStartDescription')}</div>
      </div>
      <button
        on:click={toggleAutoStart}
        disabled={!autoStartSupported}
        class="switch-track disabled:cursor-not-allowed disabled:opacity-50 {autoStartEnabled ? 'bg-primary-500' : 'bg-slate-300 dark:bg-slate-600'}"
      >
        <span class="switch-thumb {autoStartEnabled ? 'translate-x-5' : 'translate-x-0'}"></span>
      </button>
    </div>

    {#if autoStartEnabled && autoStartSupported}
      <div class="settings-block pt-3 border-t border-slate-200 dark:border-slate-700">
        <div class="settings-text">{t('settingsGeneral.autoStartLaunchMode')}</div>
        <div class="mt-2 flex gap-2">
          <button
            type="button"
            on:click={() => updateAutoStartLaunchMode(false)}
            class="segment-btn {config.auto_start_silent ? 'settings-segment-base' : 'settings-segment-active'}"
          >
            {t('settingsGeneral.autoStartLaunchShow')}
          </button>
          <button
            type="button"
            on:click={() => updateAutoStartLaunchMode(true)}
            class="segment-btn {config.auto_start_silent ? 'settings-segment-active' : 'settings-segment-base'}"
          >
            {t('settingsGeneral.autoStartLaunchSilent')}
          </button>
        </div>
      </div>
    {/if}

    <hr class="border-slate-200 dark:border-slate-700" />

    <!-- Dock 图标 -->
    <div class="flex items-center justify-between gap-4">
      <div>
        <div class="settings-text">{t('settingsGeneral.hideDockIcon')}</div>
        <div class="settings-muted mt-0.5">{t('settingsGeneral.hideDockIconDescription')}</div>
        {#if !dockVisibilitySupported}
          <div class="settings-note mt-2">{t('settingsGeneral.hideDockIconUnsupported')}</div>
        {/if}
      </div>
      <button
        on:click={toggleDockIcon}
        disabled={!dockVisibilitySupported}
        class="switch-track disabled:cursor-not-allowed disabled:opacity-50 {config.hide_dock_icon ? 'bg-primary-500' : 'bg-slate-300 dark:bg-slate-600'}"
      >
        <span class="switch-thumb {config.hide_dock_icon ? 'translate-x-5' : 'translate-x-0'}"></span>
      </button>
    </div>

    <hr class="border-slate-200 dark:border-slate-700" />

    <div class="flex items-center justify-between">
      <div>
        <div class="settings-text">{t('settingsGeneral.lightweightMode')}</div>
        <div class="settings-muted mt-0.5">{t('settingsGeneral.lightweightModeDescription')}</div>
      </div>
      <button
        on:click={toggleLightweightMode}
        class="switch-track {config.lightweight_mode ? 'bg-primary-500' : 'bg-slate-300 dark:bg-slate-600'}"
      >
        <span class="switch-thumb {config.lightweight_mode ? 'translate-x-5' : 'translate-x-0'}"></span>
      </button>
    </div>
  </div>
</div>
