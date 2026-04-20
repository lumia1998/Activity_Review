<script>
  import { createEventDispatcher, onDestroy, onMount } from 'svelte';
  import { invoke } from '$lib/runtime.js';
  import { aiStore } from '$lib/stores/ai.js';
  import { locale, t } from '$lib/i18n/index.js';
  
  export let config;
  export let providers = [];

  const dispatch = createEventDispatcher();
  $: currentLocale = $locale;
  let aiModes = [];
  let localizedProviders = [];

  // 默认预设（初始化时写入 config）
  const DEFAULT_PRESETS = [
    {
      id: 'strict',
      name: '严谨',
      prompt: `你现在是一位资深的效率管理专家。请根据我提供的今日活动记录，进行深度分析并生成一份日报。要求如下：

核心产出： 提炼今日完成的最具价值的三项任务。

时间分布： 将活动归类为"深度工作"、"琐碎事务"与"休息调整"，分析各部分占比。

效能评估： 识别流程中的阻塞点或时间浪费项。

次日建议： 基于今日进度，给出明天优先级最高的三个行动点。

请以专业、冷静、精炼的口吻呈现。`
    },
    {
      id: 'mesugaki',
      name: '雌小鬼',
      prompt: `杂鱼，又浪费了一整天的时间吧？我是你的专属（监视）AI。现在把你的活动记录交出来，让我看看你有多无能~ 要求如下：

无情拆穿： 用最毒舌的话指出我记录里那些摸鱼、发呆和低效率的行为。

虚假夸奖： 就算我完成了任务，也要用"居然连这种小事都能做完，真了不起（棒读）"的语气嘲讽一下。

杂鱼指数： 满分 10 分，根据我的表现评一个"杂鱼等级"。

语气要足够嚣张、充满轻蔑感，多用"杂鱼~"、"就这？"、"明明只是个大叔/死宅"这种词汇。`
    },
    {
      id: 'slacker',
      name: '摸鱼日报',
      prompt: `兄弟，工作是老板的，命是自己的。你现在是一个深谙职场糊弄学的"摸鱼导师"，请帮我复盘一下今天的活动记录。

分析要求：

带薪水分： 精准识别出哪些活动属于"无效加班"和"带薪如厕"，算算我今天赚了老板多少便宜（按小时算）。

职场包装： 把我那些摸鱼的行为（比如：刷网页、发呆、聊八卦）翻译成听起来很高大上的"职场专业术语"（例如：竞品调研、系统压力测试、跨部门非正式沟通）。

反向KPI： 给出一个"今日摸鱼成就"，比如"今日由于专注划水，成功避开了 2 个潜在的琐事麻烦"。

下班箴言： 用一种看透职场的松弛感，送我一句话作为明天的摸鱼指导。

语气要松弛、略带懒散，像是在茶水间偷偷抽烟时跟你传授经验的老大哥。`
    },
  ];

  // 预设管理
  let editingPresetId = null;
  let editingPresetName = '';
  let editingPresetPrompt = '';
  let showAddPreset = false;
  let newPresetName = '';
  let newPresetPrompt = '';

  $: promptPresets = config.prompt_presets || [];
  $: activePresetId = config.active_prompt_preset || null;

  function ensurePresets() {
    if (!config.prompt_presets || config.prompt_presets.length === 0) {
      config.prompt_presets = JSON.parse(JSON.stringify(DEFAULT_PRESETS));
      dispatch('change', config);
    }
  }

  function applyPreset(preset) {
    config.daily_report_custom_prompt = preset.prompt;
    config.active_prompt_preset = preset.id;
    dispatch('change', config);
  }

  function startEditPreset(preset) {
    editingPresetId = preset.id;
    editingPresetName = preset.name;
    editingPresetPrompt = preset.prompt;
  }

  function saveEditPreset() {
    const idx = config.prompt_presets.findIndex(p => p.id === editingPresetId);
    if (idx >= 0) {
      config.prompt_presets[idx].name = editingPresetName.trim();
      config.prompt_presets[idx].prompt = editingPresetPrompt.trim();
      if (config.active_prompt_preset === editingPresetId) {
        config.daily_report_custom_prompt = editingPresetPrompt.trim();
      }
      dispatch('change', config);
    }
    editingPresetId = null;
  }

  function cancelEditPreset() {
    editingPresetId = null;
  }

  function deletePreset(preset) {
    config.prompt_presets = config.prompt_presets.filter(p => p.id !== preset.id);
    if (config.active_prompt_preset === preset.id) {
      config.active_prompt_preset = null;
    }
    dispatch('change', config);
  }

  function addPreset() {
    if (!newPresetName.trim() || !newPresetPrompt.trim()) return;
    const id = 'custom_' + Date.now();
    config.prompt_presets = [...config.prompt_presets, { id, name: newPresetName.trim(), prompt: newPresetPrompt.trim() }];
    showAddPreset = false;
    newPresetName = '';
    newPresetPrompt = '';
    dispatch('change', config);
  }

  function handlePromptChange() {
    config.active_prompt_preset = null;
    dispatch('change', config);
  }
  
  // 日报生成模式：基础模板 vs AI 增强
  const aiModeConfigs = [
    { 
      value: 'local', 
      labelKey: 'settingsAI.modeLocal',
      descriptionKey: 'settingsAI.modeLocalDesc',
      requiresText: false
    },
    { 
      value: 'summary', 
      labelKey: 'settingsAI.modeSummary',
      descriptionKey: 'settingsAI.modeSummaryDesc',
      requiresText: true
    },
  ];
  $: {
    currentLocale;
    aiModes = aiModeConfigs.map((mode) => ({
      ...mode,
      label: t(mode.labelKey),
      description: t(mode.descriptionKey),
    }));
  }

  const providerLabels = {
    ollama: {
      'zh-CN': { name: 'Ollama (本地)', description: '在本机运行的开源大模型，数据不出本机' },
      en: { name: 'Ollama (Local)', description: 'Runs open models on your device, with data staying local' },
      'zh-TW': { name: 'Ollama（本機）', description: '在本機執行開源模型，資料不會離開本機' },
    },
    openai: {
      'zh-CN': { name: 'OpenAI / 兼容API', description: '支持 OpenAI 官方及兼容 API（Azure、Cloudflare 等）' },
      en: { name: 'OpenAI / Compatible API', description: 'Supports official OpenAI APIs and compatible endpoints such as Azure or Cloudflare' },
      'zh-TW': { name: 'OpenAI / 相容 API', description: '支援 OpenAI 官方與相容 API（Azure、Cloudflare 等）' },
    },
    siliconflow: {
      'zh-CN': { name: '硅基流动 SiliconFlow', description: '国内高性价比 API，兼容 OpenAI 格式' },
      en: { name: 'SiliconFlow', description: 'Cost-effective domestic API with OpenAI-compatible format' },
      'zh-TW': { name: '矽基流動 SiliconFlow', description: '高性價比 API，支援 OpenAI 相容格式' },
    },
    deepseek: {
      'zh-CN': { name: 'DeepSeek', description: '国产开源模型，性能强劲，兼容 OpenAI 格式' },
      en: { name: 'DeepSeek', description: 'Powerful open-source domestic model with OpenAI-compatible format' },
      'zh-TW': { name: 'DeepSeek', description: '高效能開源模型，支援 OpenAI 相容格式' },
    },
    qwen: {
      'zh-CN': { name: '通义千问 Qwen', description: '阿里云通义大模型，兼容 OpenAI 格式' },
      en: { name: 'Qwen', description: 'Alibaba Tongyi model with OpenAI-compatible format' },
      'zh-TW': { name: '通義千問 Qwen', description: '阿里雲通義模型，支援 OpenAI 相容格式' },
    },
    zhipu: {
      'zh-CN': { name: '智谱 ChatGLM', description: '智谱 AI 大模型' },
      en: { name: 'Zhipu ChatGLM', description: 'Large language models from Zhipu AI' },
      'zh-TW': { name: '智譜 ChatGLM', description: '智譜 AI 大模型' },
    },
    moonshot: {
      'zh-CN': { name: '月之暗面 Kimi', description: 'Moonshot AI，擅长长文本' },
      en: { name: 'Moonshot Kimi', description: 'Moonshot AI models optimized for long-context tasks' },
      'zh-TW': { name: '月之暗面 Kimi', description: 'Moonshot AI，擅長長文本' },
    },
    doubao: {
      'zh-CN': { name: '火山引擎 豆包', description: '字节跳动大模型' },
      en: { name: 'Doubao', description: 'Large language models from Volcano Engine / ByteDance' },
      'zh-TW': { name: '火山引擎 豆包', description: '字節跳動大模型' },
    },
    minimax: {
      'zh-CN': { name: '稀宇科技 MiniMax', description: 'MiniMax 文本模型，兼容 OpenAI 格式' },
      en: { name: 'MiniMax', description: 'MiniMax text models with OpenAI-compatible format' },
      'zh-TW': { name: '稀宇科技 MiniMax', description: 'MiniMax 文字模型，支援 OpenAI 相容格式' },
    },
    gemini: {
      'zh-CN': { name: 'Google Gemini', description: 'Google 的 Gemini 系列模型' },
      en: { name: 'Google Gemini', description: 'Google Gemini family models' },
      'zh-TW': { name: 'Google Gemini', description: 'Google 的 Gemini 系列模型' },
    },
    claude: {
      'zh-CN': { name: 'Anthropic Claude', description: 'Anthropic 的 Claude 系列模型' },
      en: { name: 'Anthropic Claude', description: 'Anthropic Claude family models' },
      'zh-TW': { name: 'Anthropic Claude', description: 'Anthropic 的 Claude 系列模型' },
    },
  };

  function getLocalizedProvider(provider) {
    const localized = providerLabels[provider?.id]?.[currentLocale];
    if (!localized) {
      return provider;
    }
    return {
      ...provider,
      name: localized.name,
      description: localized.description,
    };
  }
  $: {
    currentLocale;
    localizedProviders = providers.map(getLocalizedProvider);
  }

  // 提供商默认配置
  function getProviderDefaults(providerId) {
    const provider = localizedProviders.find(p => p.id === providerId);
    return {
      endpoint: provider?.default_endpoint || '',
      model: provider?.default_model || '',
      requiresApiKey: provider?.requires_api_key ?? true
    };
  }

  // 从全局 store 订阅测试状态
  let textTestStatus = null;
  let textTestMessage = '';
  let textConnectionVerified = false;
  let showApiKey = false;
  let ollamaModels = [];
  let ollamaModelsLoading = false;
  let ollamaModelsError = '';
  let ollamaModelsHint = '';
  let selectedOllamaModel = '';
  
  const unsubscribe = aiStore.subscribe(state => {
    textTestStatus = state.textTestStatus;
    textTestMessage = state.textTestMessage;
    textConnectionVerified = state.textConnectionVerified;
  });

  // 是否已配置（必须测试成功）
  $: isTextModelConfigured = textConnectionVerified;
  $: hasTextModelConfig = !!(config?.text_model?.endpoint && config?.text_model?.model);

  // 当前提供商
  $: currentProvider = localizedProviders.find(p => p.id === config?.text_model?.provider) || localizedProviders[0];
  $: requiresApiKey = currentProvider?.requires_api_key ?? true;
  $: isOllamaProvider = config?.text_model?.provider === 'ollama';
  $: selectedOllamaModel = ollamaModels.includes(config?.text_model?.model || '')
    ? config.text_model.model
    : '';

  // 是否选择了 AI 增强模式（决定是否展开配置面板）
  $: isAiMode = config.ai_mode === 'summary';

  // 每个 provider 的配置缓存（切换时保留配置）
  let providerConfigs = {};
  let configInitialized = false;

  $: if (config?.text_model?.provider && !configInitialized) {
    providerConfigs[config.text_model.provider] = {
      endpoint: config.text_model.endpoint,
      model: config.text_model.model,
      api_key: config.text_model.api_key || ''
    };
    configInitialized = true;
  }

  function handleProviderChange(e) {
    const providerId = e.target.value;
    
    // 缓存当前 provider 配置
    if (config.text_model.provider) {
      providerConfigs[config.text_model.provider] = {
        endpoint: config.text_model.endpoint,
        model: config.text_model.model,
        api_key: config.text_model.api_key || ''
      };
    }
    
    // 恢复缓存或使用默认值
    const defaults = getProviderDefaults(providerId);
    const cached = providerConfigs[providerId];
    
    config.text_model.provider = providerId;
    config.text_model.endpoint = cached?.endpoint || defaults.endpoint;
    config.text_model.model = cached?.model || defaults.model;
    config.text_model.api_key = cached?.api_key || '';
    
    aiStore.reset();
    if (providerId === 'ollama') {
      refreshOllamaModels();
    } else {
      ollamaModels = [];
      ollamaModelsError = '';
    }
    dispatch('change', config);
  }

  function handleChange() {
    // 阻止派发含有未验证文本模型的配置
    if (config.ai_mode === 'summary' && !isTextModelConfigured) {
      aiStore.setError(t('settingsAI.saveRequiresVerifiedModel'));
      return; 
    }
    dispatch('change', config);
  }

  function shouldHideRawMessage(message) {
    return currentLocale === 'en' && /[\u4e00-\u9fff]/.test(message);
  }

  async function testTextModel() {
    aiStore.startTesting();
    try {
      const result = await invoke('test_model', { 
        modelConfig: {
          provider: config.text_model.provider,
          endpoint: config.text_model.endpoint,
          api_key: config.text_model.api_key,
          model: config.text_model.model,
        }
      });
      if (result.success) {
        aiStore.setSuccess(
          result.response_time_ms
            ? t('settingsAI.saveAfterTestWithLatency', { ms: result.response_time_ms })
            : t('settingsAI.saveAfterTest')
        );
      } else {
        const failureMessage = String(result?.message || '').trim();
        aiStore.setError(
          failureMessage && !shouldHideRawMessage(failureMessage)
            ? failureMessage
            : t('settingsAI.genericTestFailed')
        );
      }
    } catch (e) {
      const failureMessage = String(e || '').trim();
      aiStore.setError(
        failureMessage && !shouldHideRawMessage(failureMessage)
          ? failureMessage
          : t('settingsAI.genericTestFailed')
      );
    }
  }

  function getOllamaModelOptions() {
    return ollamaModels;
  }

  function getOllamaFallbackOptionLabel() {
    const currentModel = config?.text_model?.model?.trim();
    if (currentModel) {
      return ollamaModelsLoading
        ? t('settingsAI.currentModelLoading', { model: currentModel })
        : t('settingsAI.currentModelMissing', { model: currentModel });
    }
    return ollamaModelsLoading ? t('settingsAI.refreshingModels') : t('settingsAI.noModels');
  }

  function hasManualOllamaModelOutsideList() {
    const currentModel = config?.text_model?.model?.trim();
    return !!(
      currentModel &&
      ollamaModels.length > 0 &&
      !ollamaModels.includes(currentModel)
    );
  }

  function handleOllamaModelSelect() {
    if (!selectedOllamaModel) return;
    config.text_model.model = selectedOllamaModel;
    handleChange();
  }

  async function refreshOllamaModels() {
    if (!isOllamaProvider || !config?.text_model?.endpoint) return;

    ollamaModelsLoading = true;
    ollamaModelsError = '';
    ollamaModelsHint = '';
    try {
      const models = await invoke('get_ollama_models', {
        endpoint: config.text_model.endpoint,
      });
      ollamaModels = Array.isArray(models) ? models : [];
      ollamaModelsHint = ollamaModels.length > 0
        ? t('settingsAI.loadedModels', { count: ollamaModels.length })
        : t('settingsAI.noModelsFound');
      if (
        ollamaModels.length > 0 &&
        (
          !config.text_model.model ||
          !ollamaModels.includes(config.text_model.model)
        )
      ) {
        config.text_model.model = ollamaModels[0];
        dispatch('change', config);
      }
    } catch (e) {
      ollamaModels = [];
      ollamaModelsError = e.toString();
      ollamaModelsHint = '';
    } finally {
      ollamaModelsLoading = false;
    }
  }

  function getConfigHash() {
    if (!config?.text_model) return null;
    const { provider, endpoint, model, api_key } = config.text_model;
    return `${provider}|${endpoint}|${model}|${api_key || ''}`;
  }

  // 挂载时只在配置变化时自动测试
  onMount(async () => {
    ensurePresets();
    await new Promise(r => setTimeout(r, 200));
    
    const currentHash = getConfigHash();
    let lastHash = null;
    const unsub = aiStore.subscribe(s => { lastHash = s.lastTestedConfigHash; });
    unsub();
    
    if (hasTextModelConfig && currentHash !== lastHash) {
      aiStore.setConfigHash(currentHash);
      await testTextModel();
    }

    if (isOllamaProvider && config?.text_model?.endpoint) {
      await refreshOllamaModels();
    }
  });

  onDestroy(() => {
    unsubscribe();
  });
</script>

<!-- 日报模式切换：紧凑的分段控制 -->
<!-- 模式选择与连接状态解耦，用户可先选模式再配置模型 -->
<fieldset class="mb-5" data-locale={currentLocale}>
  <legend class="settings-label mb-2">{t('settingsAI.modeLegend')}</legend>
  <div class="flex gap-2">
    {#each aiModes as mode}
      {@const isSelected = config.ai_mode === mode.value}
      <button 
        type="button"
        on:click={() => { 
          // 仅当切换需要文字模型且未配置或测试失败时，给提示并阻止向父组件发送 change（避免自动保存未验证状态）
          if (mode.requiresText && !isTextModelConfigured) {
            config.ai_mode = mode.value; // 允许 UI 切换展开面板
            aiStore.setError(t('settingsAI.switchRequiresVerifiedModel'));
            // 不触发 handleChange()，防止父组件认为配置已完备
          } else {
            config.ai_mode = mode.value; 
            handleChange(); 
          }
        }}
        class="flex-1 min-h-16 px-3 py-2.5 rounded-lg text-sm font-medium leading-none transition-all duration-150
               {isSelected
                 ? 'settings-segment-active'
                 : 'settings-segment-base'}"
      >
        <div class="flex h-full flex-col items-center justify-center gap-1 text-center">
          <div class="leading-none">{mode.label}</div>
          <div class="text-[10px] leading-none {isSelected ? 'text-white/70' : 'settings-subtle'}">{mode.description}</div>
        </div>
      </button>
    {/each}
  </div>
</fieldset>

<!-- AI 模型配置：仅在 AI 增强模式或云端模式下展开 -->
{#if isAiMode}
  <div class="settings-block pt-3 border-t border-slate-200 dark:border-slate-700">
    <!-- 提供商 + 测试按钮 -->
    <div class="flex items-end gap-2">
      <div class="flex-1">
        <label for="ai-provider" class="settings-label mb-1.5">{t('settingsAI.provider')}</label>
        <select
          id="ai-provider"
          value={config.text_model?.provider || 'ollama'}
          on:change={handleProviderChange}
          class="control-input"
        >
          {#each localizedProviders as provider}
            <option value={provider.id}>{provider.name}</option>
          {/each}
        </select>
      </div>
      
      <!-- 测试按钮紧跟提供商选择 -->
      <button
        on:click={testTextModel}
        disabled={textTestStatus === 'testing' || !hasTextModelConfig}
        class="shrink-0 min-h-10 px-3 py-2 text-xs font-medium rounded-lg leading-none transition-all
               {textTestStatus === 'success' 
                 ? 'settings-action-success' 
                 : textTestStatus === 'error' 
                   ? 'settings-action-danger' 
                   : 'settings-action-secondary'}
               disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {#if textTestStatus === 'testing'}
            <span class="inline-flex items-center gap-1">
              <span class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            {t('settingsAI.testing')}
          </span>
        {:else if textTestStatus === 'success'}
          ✓ {t('settingsAI.testSuccess')}
        {:else if textTestStatus === 'error'}
          ✗ {t('settingsAI.testFailed')}
        {:else}
          {t('settingsAI.testConnection')}
        {/if}
      </button>
    </div>
    
    <!-- 测试结果消息 -->
    {#if textTestMessage}
      <div class="px-3 py-2 rounded-lg text-xs {textTestStatus === 'success' ? 'settings-tone-success' : 'settings-tone-danger'}">
        {textTestMessage}
      </div>
    {/if}

    <!-- API 地址 -->
    <div>
      <label for="ai-endpoint" class="settings-label mb-1.5">{t('settingsAI.endpoint')}</label>
      <input
        id="ai-endpoint"
        type="text"
        bind:value={config.text_model.endpoint}
        on:change={handleChange}
        class="control-input-mono"
        placeholder={currentProvider?.default_endpoint || 'http://localhost:11434'}
      />
    </div>

    <!-- API 密钥（按需显示） -->
    {#if requiresApiKey}
      <div>
        <label for="ai-apikey" class="settings-label mb-1.5">{t('settingsAI.apiKey')}</label>
        <div class="relative">
          {#if showApiKey}
            <input
              id="ai-apikey"
              type="text"
              bind:value={config.text_model.api_key}
              on:change={handleChange}
              class="control-input pr-12"
              placeholder="sk-..."
            />
          {:else}
            <input
              id="ai-apikey"
              type="password"
              bind:value={config.text_model.api_key}
              on:change={handleChange}
              class="control-input pr-12"
              placeholder="sk-..."
            />
          {/if}
          <button
            type="button"
            class="absolute inset-y-0 right-3 inline-flex items-center justify-center text-slate-400 transition hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
            aria-label={showApiKey ? t('settingsAI.hideApiKey') : t('settingsAI.showApiKey')}
            title={showApiKey ? t('settingsAI.hideApiKey') : t('settingsAI.showApiKey')}
            on:click={() => {
              showApiKey = !showApiKey;
            }}
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12s3.75-6.75 9.75-6.75S21.75 12 21.75 12 18 18.75 12 18.75 2.25 12 2.25 12Z" />
              <circle cx="12" cy="12" r="3.25" />
            </svg>
          </button>
        </div>
      </div>
    {/if}

    <!-- 模型名称 -->
    <div>
      <div class="flex items-end gap-2">
        <div class="flex-1">
          <label for="ai-model" class="settings-label mb-1.5">{t('settingsAI.model')}</label>
          {#if isOllamaProvider}
            {#key `${selectedOllamaModel}|${config?.text_model?.model || ''}|${ollamaModels.join('|')}|${ollamaModelsLoading}`}
              <select
                id="ai-model"
                bind:value={selectedOllamaModel}
                on:change={handleOllamaModelSelect}
                class="control-input"
                disabled={ollamaModelsLoading || getOllamaModelOptions().length === 0}
              >
                {#if getOllamaModelOptions().length === 0}
                    <option value="">
                      {getOllamaFallbackOptionLabel()}
                    </option>
                {:else}
                  {#if hasManualOllamaModelOutsideList()}
                    <option value="" disabled>
                      {t('settingsAI.manualModelMissing')}
                    </option>
                  {/if}
                  {#each ollamaModels as model (model)}
                    <option value={model}>{model}</option>
                  {/each}
                {/if}
              </select>
            {/key}
          {:else}
            <input
              id="ai-model"
              type="text"
              bind:value={config.text_model.model}
              on:change={handleChange}
              class="control-input"
              placeholder={currentProvider?.default_model || 'qwen2.5'}
            />
          {/if}
        </div>

        {#if isOllamaProvider}
          <button
            type="button"
            on:click={refreshOllamaModels}
            disabled={ollamaModelsLoading || !config.text_model.endpoint}
            class="shrink-0 min-h-10 px-3 py-2 text-xs font-medium rounded-lg leading-none transition-all settings-action-secondary disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {ollamaModelsLoading ? t('settingsAI.refreshingModels') : t('settingsAI.refreshModels')}
          </button>
        {/if}
      </div>

      {#if isOllamaProvider}
        <div class="mt-3">
          <label for="ai-model-manual" class="settings-label mb-1.5">{t('settingsAI.manualModel')}</label>
          <input
            id="ai-model-manual"
            type="text"
            bind:value={config.text_model.model}
            on:change={handleChange}
            class="control-input"
            placeholder={currentProvider?.default_model || 'qwen2.5'}
          />
        </div>
        {#if ollamaModelsError}
          <p class="settings-note text-rose-500 dark:text-rose-400">{ollamaModelsError}</p>
        {:else if ollamaModelsHint}
          <p class="settings-note">{t('settingsAI.modelHint', { hint: ollamaModelsHint })}</p>
        {:else}
          <p class="settings-note">{t('settingsAI.ollamaHint')}</p>
        {/if}
      {:else if currentProvider?.description}
        <p class="settings-note">{currentProvider.description}</p>
      {/if}
    </div>

    <!-- 自定义提示词 -->
    <div class="pt-3 border-t border-slate-200 dark:border-slate-700">
      <label for="ai-custom-prompt" class="settings-label mb-1.5">{t('settingsAI.customPromptLabel')}</label>
      <p class="settings-note mb-2">{t('settingsAI.customPromptHint')}</p>

      <!-- 预设列表 -->
      <div class="flex flex-wrap gap-2 mb-3">
        {#each promptPresets as preset (preset.id)}
          <div class="relative group">
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all
                     {activePresetId === preset.id
                       ? 'settings-segment-active'
                       : 'settings-segment-base'}"
              on:click={() => applyPreset(preset)}
              title={preset.prompt.slice(0, 80) + '...'}
            >
              {preset.name}
            </button>
            <div class="absolute -top-1 -right-1 hidden group-hover:flex gap-0.5">
              <button
                type="button"
                class="w-4 h-4 rounded-full bg-slate-200 dark:bg-slate-600 text-slate-500 dark:text-slate-300 flex items-center justify-center text-[9px] hover:bg-blue-200 dark:hover:bg-blue-700"
                on:click|stopPropagation={() => startEditPreset(preset)}
                title="编辑"
              >✎</button>
              <button
                type="button"
                class="w-4 h-4 rounded-full bg-slate-200 dark:bg-slate-600 text-slate-500 dark:text-slate-300 flex items-center justify-center text-[9px] hover:bg-red-200 dark:hover:bg-red-700"
                on:click|stopPropagation={() => deletePreset(preset)}
                title="删除"
              >✕</button>
            </div>
          </div>
        {/each}
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium rounded-lg settings-segment-base hover:border-dashed"
          on:click={() => { showAddPreset = true; }}
        >
          + 添加预设
        </button>
      </div>

      <!-- 编辑预设弹出区 -->
      {#if editingPresetId}
        <div class="mb-3 p-3 rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20">
          <div class="flex items-center gap-2 mb-2">
            <input
              type="text"
              bind:value={editingPresetName}
              class="control-input flex-1 text-sm"
              placeholder="预设名称"
            />
            <button type="button" class="px-2 py-1 text-xs font-medium rounded settings-action-secondary" on:click={saveEditPreset}>保存</button>
            <button type="button" class="px-2 py-1 text-xs font-medium rounded settings-action-secondary" on:click={cancelEditPreset}>取消</button>
          </div>
          <textarea
            bind:value={editingPresetPrompt}
            rows="5"
            class="control-input resize-y min-h-[100px] text-sm"
            placeholder="提示词内容"
          ></textarea>
        </div>
      {/if}

      <!-- 新增预设区 -->
      {#if showAddPreset}
        <div class="mb-3 p-3 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/20">
          <div class="flex items-center gap-2 mb-2">
            <input
              type="text"
              bind:value={newPresetName}
              class="control-input flex-1 text-sm"
              placeholder="新预设名称"
            />
            <button type="button" class="px-2 py-1 text-xs font-medium rounded settings-action-secondary" on:click={addPreset}>添加</button>
            <button type="button" class="px-2 py-1 text-xs font-medium rounded settings-action-secondary" on:click={() => { showAddPreset = false; newPresetName = ''; newPresetPrompt = ''; }}>取消</button>
          </div>
          <textarea
            bind:value={newPresetPrompt}
            rows="5"
            class="control-input resize-y min-h-[100px] text-sm"
            placeholder="输入提示词内容..."
          ></textarea>
        </div>
      {/if}

      <!-- 当前生效的提示词 -->
      <textarea
        id="ai-custom-prompt"
        bind:value={config.daily_report_custom_prompt}
        on:change={handlePromptChange}
        rows="6"
        class="control-input resize-y min-h-[140px] text-sm"
        placeholder={t('settingsAI.customPromptPlaceholder')}
      ></textarea>
    </div>
  </div>
{:else}
  <!-- 未启用 AI 模式时的提示 -->
  <div class="pt-3 border-t border-slate-200 dark:border-slate-700">
    <p class="settings-empty">{t('settingsAI.aiModeDisabled')}</p>
  </div>
{/if}
