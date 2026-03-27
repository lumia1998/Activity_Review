<script>
  import { createEventDispatcher, onDestroy, onMount } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import { showToast } from '$lib/stores/toast.js';
  import {
    AVATAR_OPACITY_DEFAULT,
    AVATAR_SCALE_DEFAULT,
    clampAvatarOpacity,
    clampAvatarScale,
    formatAvatarOpacityLabel,
    formatAvatarScaleLabel,
    getAvatarToggleToast,
    getAvatarToggleUiState,
    toggleAvatarSetting,
    updateAvatarOpacitySetting,
    updateAvatarScaleSetting,
  } from '$lib/utils/avatarToggle.js';

  export let config;

  const dispatch = createEventDispatcher();

  let avatarSaving = false;
  let avatarScaleSaving = false;
  let avatarOpacitySaving = false;
  let avatarScaleTimer = null;
  let avatarOpacityTimer = null;

  // === 背景图片 ===
  let bgPreview = null;
  let bgUploading = false;
  let appearanceDestroyed = false;

  const blurLabels = ['清晰', '轻微模糊', '中等模糊'];
  $: avatarToggleUi = getAvatarToggleUiState(Boolean(config.avatar_enabled), avatarSaving);
  $: avatarScale = clampAvatarScale(config.avatar_scale ?? AVATAR_SCALE_DEFAULT);
  $: avatarScaleLabel = formatAvatarScaleLabel(avatarScale);
  $: avatarOpacity = clampAvatarOpacity(config.avatar_opacity ?? AVATAR_OPACITY_DEFAULT);
  $: avatarOpacityLabel = formatAvatarOpacityLabel(avatarOpacity);

  onMount(async () => {
    try {
      const b64 = await invoke('get_background_image');
      if (b64) bgPreview = `data:image/jpeg;base64,${b64}`;
    } catch (e) { /* ignore */ }
  });

  onDestroy(() => {
    appearanceDestroyed = true;
    clearTimeout(avatarScaleTimer);
    clearTimeout(avatarOpacityTimer);
  });

  async function toggleAvatarMode() {
    if (avatarSaving) {
      return;
    }

    avatarSaving = true;

    try {
      const enabled = await toggleAvatarSetting(config, async (nextConfig) => {
        await invoke('save_config', { config: nextConfig });
      });

      dispatch('change', config);
      showToast(getAvatarToggleToast(enabled), enabled ? 'success' : 'info');
    } catch (e) {
      console.error('设置桌宠失败:', e);
      showToast(`桌宠设置失败: ${e}`, 'error');
    } finally {
      avatarSaving = false;
    }
  }

  function queueAvatarScaleSave(nextScale) {
    clearTimeout(avatarScaleTimer);
    avatarScaleTimer = setTimeout(async () => {
      avatarScaleSaving = true;

      try {
        const savedScale = await updateAvatarScaleSetting(config, nextScale, async (nextConfig) => {
          await invoke('save_config', { config: nextConfig });
        });
        config.avatar_scale = savedScale;
        dispatch('change', config);
      } catch (e) {
        console.error('保存桌宠缩放失败:', e);
        showToast(`桌宠缩放保存失败: ${e}`, 'error');
      } finally {
        avatarScaleSaving = false;
      }
    }, 120);
  }

  function handleAvatarScaleInput(event) {
    const nextScale = clampAvatarScale(Number(event.currentTarget.value));
    config.avatar_scale = nextScale;
    dispatch('change', config);
    queueAvatarScaleSave(nextScale);
  }

  function queueAvatarOpacitySave(nextOpacity) {
    clearTimeout(avatarOpacityTimer);
    avatarOpacityTimer = setTimeout(async () => {
      avatarOpacitySaving = true;

      try {
        const savedOpacity = await updateAvatarOpacitySetting(
          config,
          nextOpacity,
          async (nextConfig) => {
            await invoke('save_config', { config: nextConfig });
          }
        );
        config.avatar_opacity = savedOpacity;
        dispatch('change', config);
      } catch (e) {
        console.error('保存桌宠透明度失败:', e);
        showToast(`桌宠透明度保存失败: ${e}`, 'error');
      } finally {
        avatarOpacitySaving = false;
      }
    }, 120);
  }

  function handleAvatarOpacityInput(event) {
    const nextOpacity = clampAvatarOpacity(Number(event.currentTarget.value));
    config.avatar_opacity = nextOpacity;
    dispatch('change', config);
    queueAvatarOpacitySave(nextOpacity);
  }

  function handleBgFileSelect(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) return;
    if (file.size > 10 * 1024 * 1024) {
      showToast('图片大小不能超过 10MB', 'warning');
      return;
    }

    bgUploading = true;
    const reader = new FileReader();
    reader.onload = async () => {
      if (appearanceDestroyed) return;

      try {
        const b64Data = typeof reader.result === 'string' ? reader.result.split(',')[1] : null;
        if (!b64Data) {
          throw new Error('背景图读取失败');
        }
        await invoke('save_background_image', { data: b64Data });
        if (appearanceDestroyed) return;
        config.background_image = 'background.jpg';
        const freshB64 = await invoke('get_background_image');
        if (appearanceDestroyed) return;
        const imageUrl = freshB64 ? `data:image/jpeg;base64,${freshB64}` : null;
        bgPreview = imageUrl;
        dispatchBgEvent(imageUrl);
      } catch (e) {
        if (appearanceDestroyed) return;
        console.error('上传背景图失败:', e);
        showToast('上传失败: ' + e, 'error');
      } finally {
        if (!appearanceDestroyed) {
          bgUploading = false;
        }
      }
    };
    reader.readAsDataURL(file);
  }

  async function clearBg() {
    try {
      await invoke('clear_background_image');
      bgPreview = null;
      config.background_image = null;
      dispatchBgEvent(null);
    } catch (e) {
      console.error('清除背景图失败:', e);
      showToast('清除背景图失败: ' + e, 'error');
    }
  }

  function updateBgOpacity(val) {
    config.background_opacity = parseFloat(val);
    dispatch('change', config);
    dispatchBgEvent(bgPreview);
  }

  function updateBgBlur(val) {
    config.background_blur = parseInt(val);
    dispatch('change', config);
    dispatchBgEvent(bgPreview);
  }

  function dispatchBgEvent(image) {
    window.dispatchEvent(new CustomEvent('background-changed', {
      detail: {
        image,
        opacity: config.background_opacity ?? 0.25,
        blur: config.background_blur ?? 1,
      }
    }));
  }
</script>

<div class="settings-card">
  <div class="settings-section">
    <div class="flex items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2">
          <div class="settings-text">桌面化身</div>
          <span class="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-amber-700 dark:border-amber-400/30 dark:bg-amber-500/10 dark:text-amber-200">
            Beta
          </span>
        </div>
        <div class="settings-muted mt-0.5">显示独立桌宠窗口，用轻量状态反馈当前工作节奏</div>
        <div class="settings-muted mt-1 text-[12px]">实验功能，当前仍在持续优化显示细节、状态反馈与交互体验</div>
      </div>
      <button
        type="button"
        on:click={toggleAvatarMode}
        class="switch-track {avatarToggleUi.trackClass} {avatarToggleUi.buttonClass}"
        disabled={avatarSaving}
        aria-label={avatarToggleUi.ariaLabel}
        aria-pressed={config.avatar_enabled}
      >
        <span class="switch-thumb {avatarToggleUi.thumbClass}"></span>
      </button>
    </div>

    <hr class="border-slate-200 dark:border-slate-700" />

    <div class="settings-block pt-1">
      <div class="flex items-center justify-between gap-3">
        <div>
          <div class="settings-text">桌宠大小</div>
          <div class="settings-muted mt-0.5">连续缩放桌宠尺寸，调整后会立即同步到桌面窗口</div>
        </div>
        <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">
          {avatarScaleLabel}
          {#if avatarScaleSaving}
            <span class="ml-2 text-xs font-normal text-slate-400 dark:text-slate-500">同步中</span>
          {/if}
        </div>
      </div>

      <input
        type="range"
        min="0.7"
        max="1.3"
        step="0.05"
        value={avatarScale}
        on:input={handleAvatarScaleInput}
        class="mt-3 w-full accent-primary-500"
        aria-label="调整桌宠大小"
      />
      <div class="mt-2 flex justify-between text-[11px] text-slate-400 dark:text-slate-500">
        <span>更小</span>
        <span>默认 90%</span>
        <span>更大</span>
      </div>
    </div>

    <div class="settings-block pt-1">
      <div class="flex items-center justify-between gap-3">
        <div>
          <div class="settings-text">桌宠透明度</div>
          <div class="settings-muted mt-0.5">仅作用于猫体本身，不影响背景图片透明度</div>
        </div>
        <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">
          {avatarOpacityLabel}
          {#if avatarOpacitySaving}
            <span class="ml-2 text-xs font-normal text-slate-400 dark:text-slate-500">同步中</span>
          {/if}
        </div>
      </div>

      <input
        type="range"
        min="0.45"
        max="1"
        step="0.05"
        value={avatarOpacity}
        on:input={handleAvatarOpacityInput}
        class="mt-3 w-full accent-primary-500"
        aria-label="调整桌宠透明度"
      />
      <div class="mt-2 flex justify-between text-[11px] text-slate-400 dark:text-slate-500">
        <span>更透</span>
        <span>默认 82%</span>
        <span>更实</span>
      </div>
    </div>
  </div>
</div>

<!-- 背景图片 -->
<div class="settings-card">
  <h3 class="settings-card-title">背景图片</h3>
  <p class="settings-card-desc">上传图片作为应用背景底纹</p>

  <div class="settings-section">
    <!-- 预览 + 上传 -->
    <div class="flex items-start gap-4">
      {#if bgPreview}
        <div class="w-32 h-20 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700 flex-shrink-0">
          <img src={bgPreview} alt="背景预览" class="w-full h-full object-cover" />
        </div>
      {:else}
        <div class="w-32 h-20 rounded-lg border-2 border-dashed border-slate-200 dark:border-slate-700 flex items-center justify-center flex-shrink-0">
          <span class="settings-subtle">无背景</span>
        </div>
      {/if}

      <div class="flex-1 settings-field">
        <label class="settings-action-secondary cursor-pointer">
          {#if bgUploading}
            <div class="animate-spin rounded-full h-3 w-3 border-2 border-slate-500 border-t-transparent"></div>
            处理中...
          {:else}
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            选择图片
          {/if}
          <input type="file" accept="image/*" class="hidden" on:change={handleBgFileSelect} disabled={bgUploading} />
        </label>
        {#if bgPreview}
          <button
            on:click={clearBg}
            class="settings-link-danger"
          >
            清除背景
          </button>
        {/if}
        <p class="settings-muted">支持 JPG/PNG，建议不超过 10MB</p>
      </div>
    </div>

    {#if bgPreview || config.background_image}
      <hr class="border-slate-200 dark:border-slate-700" />

      <!-- 显示强度 -->
      <div class="settings-block">
        <div class="flex items-center justify-between">
          <span class="settings-text">显示强度</span>
          <span class="settings-value">{Math.round((config.background_opacity ?? 0.25) * 100)}%</span>
        </div>
        <input
          type="range"
          min="0.05"
          max="0.60"
          step="0.01"
          value={config.background_opacity ?? 0.25}
          on:input={(e) => updateBgOpacity(e.target.value)}
          class="range-input"
        />
        <div class="flex justify-between text-[10px] settings-subtle">
          <span>淡雅</span>
          <span>浓郁</span>
        </div>
      </div>

      <!-- 模糊度 -->
      <div class="settings-block">
        <div class="flex items-center justify-between">
          <span class="settings-text">模糊程度</span>
          <span class="settings-muted">{blurLabels[config.background_blur ?? 1]}</span>
        </div>
        <div class="flex gap-2">
          {#each [0, 1, 2] as level}
            <button
              on:click={() => updateBgBlur(level)}
              class="segment-btn
                {(config.background_blur ?? 1) === level
                  ? 'settings-segment-active'
                  : 'settings-segment-base'}"
            >
              {blurLabels[level]}
            </button>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</div>
