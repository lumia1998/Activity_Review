<script>
  import { onDestroy, onMount } from 'svelte';
  import { invoke, open, getVersion } from '$lib/runtime.js';
  import { locale, t } from '$lib/i18n/index.js';
  import { runUpdateFlow } from '$lib/utils/updater.js';

  let appVersion = '';
  let isCheckingUpdate = false;
  let updateStatus = '';
  let updateStatusTimer = null;
  $: currentLocale = $locale;

  onMount(async () => {
    try {
      appVersion = await getVersion();
    } catch (e) {
      console.error('初始化失败:', e);
      appVersion = '1.0.0';
    }
  });

  async function openGitHub() {
    await open('https://github.com/lumia1998/Acticity_Review');
  }

  async function openDataDir() {
    try {
      await invoke('open_data_dir');
    } catch (e) {
      console.error('打开目录失败:', e);
    }
  }

  async function checkForUpdates() {
    if (isCheckingUpdate) return;

    isCheckingUpdate = true;
    updateStatus = t('about.checkingUpdates');

    await runUpdateFlow({
      silentWhenUpToDate: false,
      confirmBeforeDownload: true,
      onStatusChange: (status) => {
        updateStatus = status;
      },
    });

    isCheckingUpdate = false;
    if (updateStatus) {
      clearTimeout(updateStatusTimer);
      updateStatusTimer = setTimeout(() => {
        updateStatus = '';
        updateStatusTimer = null;
      }, 3000);
    }
  }

  onDestroy(() => {
    clearTimeout(updateStatusTimer);
  });
</script>

<div class="page-shell about-editorial-shell" data-locale={currentLocale}>
  <div class="mx-auto w-full max-w-4xl about-minimal-shell">
    <section class="page-card about-brand-card">
      <div class="about-brand-head">
        <div class="about-brand-mark">
          <img src="/icons/256x256.png" alt="Activity Review" class="h-16 w-16 rounded-[18px] object-cover" />
        </div>
        <span class="page-inline-chip-brand">v{appVersion}</span>
      </div>

      <div class="about-brand-copy">
        <h1 class="about-brand-title">Activity Review</h1>
        <p class="about-brand-description">{t('about.description')}</p>
      </div>

      <div class="about-action-strip">
        <div class="about-action-row">
          <button on:click={openGitHub} class="page-action-secondary min-h-10 px-4 py-2">
            <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            <span class="leading-none">GitHub</span>
          </button>
          <button on:click={openDataDir} class="page-action-secondary min-h-10 px-4 py-2">
            <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
            <span class="leading-none">{t('about.openDataDir')}</span>
          </button>
        </div>

        <div class="flex justify-center">
          <button
            on:click={checkForUpdates}
            disabled={isCheckingUpdate}
            class="page-action-brand min-h-10 px-5 py-2 disabled:cursor-wait"
          >
            {#if isCheckingUpdate}
              <svg class="animate-spin h-4 w-4 shrink-0 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span class="leading-none">{t('about.checkingUpdates')}</span>
            {:else}
              <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              <span class="leading-none">{t('about.checkUpdates')}</span>
            {/if}
          </button>
        </div>
      </div>
    </section>

    <section class="about-trust-grid">
      <article class="page-card about-trust-card">
        <span class="about-trust-kicker">01</span>
        <h3 class="about-trust-title">{t('about.localFirstTitle')}</h3>
        <p class="about-trust-copy">{t('about.localFirstCopy')}</p>
      </article>
      <article class="page-card about-trust-card">
        <span class="about-trust-kicker">02</span>
        <h3 class="about-trust-title">{t('about.timelineTrustTitle')}</h3>
        <p class="about-trust-copy">{t('about.timelineTrustCopy')}</p>
      </article>
      <article class="page-card about-trust-card">
        <span class="about-trust-kicker">03</span>
        <h3 class="about-trust-title">{t('about.reportTrustTitle')}</h3>
        <p class="about-trust-copy">{t('about.reportTrustCopy')}</p>
      </article>
    </section>

    <section class="about-tech-stack">
      <span class="about-tech-pill about-tech-pill-primary"><span class="about-tech-pill-label">Python Backend</span></span>
      <span class="about-tech-pill"><span class="about-tech-pill-label">Svelte</span></span>
      <span class="about-tech-pill"><span class="about-tech-pill-label">FastAPI</span></span>
      <span class="about-tech-pill"><span class="about-tech-pill-label">SQLite</span></span>
    </section>

    {#if updateStatus}
      <div class="page-banner-warning about-update-banner">
        <div>
          <p class="font-semibold">{t('about.updateStatus')}</p>
          <p class="text-sm mt-1">{updateStatus}</p>
        </div>
      </div>
    {/if}
  </div>
</div>
