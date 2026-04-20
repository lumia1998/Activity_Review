import { emitLocalEvent } from './events.js';

const API_BASE = window.__ACTICITY_API_BASE__ || 'http://127.0.0.1:8000';
const AI_PROVIDERS = [

  {
    id: 'ollama',
    name: 'Ollama',
    description: 'Local Ollama endpoint',
    default_endpoint: 'http://localhost:11434',
    default_model: 'qwen2.5',
    requires_api_key: false,
  },
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'OpenAI compatible API',
    default_endpoint: 'https://api.openai.com/v1',
    default_model: 'gpt-4.1-mini',
    requires_api_key: true,
  },
  {
    id: 'claude',
    name: 'Claude',
    description: 'Anthropic Claude API',
    default_endpoint: 'https://api.anthropic.com',
    default_model: 'claude-sonnet-4-6',
    requires_api_key: true,
  },
  {
    id: 'gemini',
    name: 'Gemini',
    description: 'Google Gemini API',
    default_endpoint: 'https://generativelanguage.googleapis.com',
    default_model: 'gemini-2.5-flash',
    requires_api_key: true,
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    description: 'DeepSeek compatible API',
    default_endpoint: 'https://api.deepseek.com/v1',
    default_model: 'deepseek-chat',
    requires_api_key: true,
  },
  {
    id: 'siliconflow',
    name: 'SiliconFlow',
    description: 'SiliconFlow compatible API',
    default_endpoint: 'https://api.siliconflow.cn/v1',
    default_model: 'Qwen/Qwen2.5-7B-Instruct',
    requires_api_key: true,
  },
  {
    id: 'minimax',
    name: 'MiniMax',
    description: 'MiniMax compatible API',
    default_endpoint: 'https://api.minimaxi.com/v1',
    default_model: 'MiniMax-M2.5',
    requires_api_key: true,
  },
];

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

function emitRecordingState(state) {
  if (!Array.isArray(state)) {
    return state;
  }

  emitLocalEvent('recording-state-changed', {
    isRecording: Boolean(state[0]),
    isPaused: Boolean(state[1]),
  });
  return state;
}

function getBrowserPlatform() {
  const platform = globalThis?.navigator?.userAgentData?.platform || globalThis?.navigator?.platform || '';
  const normalized = String(platform).toLowerCase();
  if (normalized.includes('mac')) return 'macos';
  if (normalized.includes('win')) return 'windows';
  if (normalized.includes('linux')) return 'linux';
  return 'unknown';
}

async function getLinuxSessionSupport() {
  try {
    return await request('/api/system/platform-support');
  } catch {
    const platform = getBrowserPlatform();
    if (platform !== 'linux') {
      return {
        platform,
        sessionType: 'unsupported',
        desktopEnvironment: 'unsupported',
        screenshotSupported: platform !== 'unknown',
        activeWindowSupported: platform !== 'unknown',
        activeWindowProvider: platform === 'windows' ? 'windows-api' : platform === 'macos' ? 'appkit' : 'unknown',
        browserUrlSupportLevel: 'limited',
      };
    }

    return {
      platform: 'linux',
      sessionType: 'unknown',
      desktopEnvironment: 'unknown',
      screenshotSupported: true,
      activeWindowSupported: false,
      activeWindowProvider: 'unknown',
      browserUrlSupportLevel: 'limited',
    };
  }
}

export async function invoke(command, payload = {}) {
  switch (command) {
    case 'get_today_stats':
      return request('/api/stats/today');
    case 'get_overview_stats': {
      const params = new URLSearchParams();
      if (payload.mode) params.set('mode', payload.mode);
      if (payload.dateFrom) params.set('dateFrom', payload.dateFrom);
      if (payload.dateTo) params.set('dateTo', payload.dateTo);
      const query = params.toString();
      return request(`/api/stats/overview${query ? `?${query}` : ''}`);
    }
    case 'get_timeline':
      return request(`/api/timeline?date=${encodeURIComponent(payload.date)}&limit=${payload.limit ?? 20}&offset=${payload.offset ?? 0}`);
    case 'get_hourly_summaries':
      return request(`/api/timeline/hourly-summaries?date=${encodeURIComponent(payload.date)}`);
    case 'get_activity':
      return request(`/api/timeline/activity/${encodeURIComponent(payload.id)}`);
    case 'generate_report':
      return request('/api/reports/generate', {
        method: 'POST',
        body: JSON.stringify({ date: payload.date, force: payload.force ?? true, locale: payload.locale ?? null }),
      });
    case 'get_saved_report': {
      const params = new URLSearchParams();
      if (payload.locale) params.set('locale', payload.locale);
      const query = params.toString();
      return request(`/api/reports/${encodeURIComponent(payload.date)}${query ? `?${query}` : ''}`);
    }
    case 'export_report_markdown':
      return request('/api/reports/export-markdown', {
        method: 'POST',
        body: JSON.stringify({
          date: payload.date,
          content: payload.content,
          exportDir: payload.exportDir,
          locale: payload.locale ?? null,
        }),
      });
    case 'chat_work_assistant':
      return request('/api/assistant/chat', {
        method: 'POST',
        body: JSON.stringify({
          question: payload.question,
          history: payload.history ?? [],
          modelConfig: payload.modelConfig ?? null,
          locale: payload.locale ?? null,
        }),
      });
    case 'get_config':
      return request('/api/config');
    case 'save_config':
      return request('/api/config', {
        method: 'PUT',
        body: JSON.stringify({ config: payload.config }),
      });
    case 'get_storage_stats':
      return request('/api/config/storage-stats');
    case 'get_data_dir':
      return request('/api/config/data-dir');
    case 'get_default_data_dir':
      return request('/api/config/default-data-dir');
    case 'change_data_dir':
      return request('/api/config/change-data-dir', {
        method: 'POST',
        body: JSON.stringify({ targetDir: payload.targetDir }),
      });
    case 'cleanup_old_data_dir':
      return request('/api/config/cleanup-old-data-dir', {
        method: 'POST',
        body: JSON.stringify({ targetDir: payload.targetDir }),
      });
    case 'clear_old_activities':
      return request('/api/config/clear-old-activities', {
        method: 'POST',
      });
    case 'get_running_apps':
      return request('/api/config/running-apps');
    case 'get_recent_apps':
      return request('/api/config/recent-apps');
    case 'get_linux_session_support':
      return getLinuxSessionSupport();
    case 'get_screenshot_thumbnail':
      return request(`/api/files/thumbnail?path=${encodeURIComponent(payload.path)}`);
    case 'get_screenshot_full':
      return request(`/api/files/full?path=${encodeURIComponent(payload.path)}`);
    case 'get_background_image':
      return request('/api/config/background-image');
    case 'save_background_image':
      return request('/api/config/background-image', {
        method: 'POST',
        body: JSON.stringify({ data: payload.data }),
      });
    case 'clear_background_image':
      return request('/api/config/background-image', {
        method: 'DELETE',
      });
    case 'get_ai_providers':
      return AI_PROVIDERS;
    case 'get_ollama_models': {
      const endpoint = String(payload.endpoint || 'http://localhost:11434').replace(/\/$/, '');
      const data = await requestJson(`${endpoint}/api/tags`);
      return Array.isArray(data?.models) ? data.models.map((item) => item.name).filter(Boolean) : [];
    }
    case 'test_model':
    case 'test_ai_model':
      return request('/api/assistant/test-model', {
        method: 'POST',
        body: JSON.stringify({
          modelConfig: payload.modelConfig ?? null,
        }),
      });
    case 'get_runtime_platform':
      return getBrowserPlatform();
    case 'capture_activity_tick': {
      return request('/api/runtime/activity-tick', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    }
    case 'get_recording_state':
      return emitRecordingState(await request('/api/runtime/recording-state'));
    case 'pause_recording': {
      const state = await request('/api/runtime/pause-recording', {
        method: 'POST',
      });
      emitRecordingState(state);
      return state;
    }
    case 'resume_recording': {
      const state = await request('/api/runtime/resume-recording', {
        method: 'POST',
      });
      emitRecordingState(state);
      return state;
    }
    case 'get_platform':
      return getBrowserPlatform();
    case 'get_app_icon':
      return request(`/api/config/app-icon?appName=${encodeURIComponent(payload.appName)}&executablePath=${encodeURIComponent(payload.executablePath ?? '')}`);
    case 'open_data_dir':
      return request('/api/config/open-data-dir', {
        method: 'POST',
      });
    case 'set_app_category_rule':
      return request('/api/config/app-category-rule', {
        method: 'POST',
        body: JSON.stringify({
          appName: payload.appName,
          category: payload.category,
          syncHistory: payload.syncHistory ?? true,
        }),
      });
    case 'set_domain_semantic_rule':
      return request('/api/config/domain-semantic-rule', {
        method: 'POST',
        body: JSON.stringify({
          domain: payload.domain,
          semanticCategory: payload.semanticCategory,
          syncHistory: payload.syncHistory ?? true,
        }),
      });
    case 'enable_autostart':
      return request('/api/runtime/enable-autostart', {
        method: 'POST',
      });
    case 'disable_autostart':
      return request('/api/runtime/disable-autostart', {
        method: 'POST',
      });
    case 'set_dock_visibility':
      return request('/api/runtime/set-dock-visibility', {
        method: 'POST',
        body: JSON.stringify({ visible: payload.visible !== false }),
      });
    case 'update_last_check_time':
      return request('/api/runtime/update-last-check-time', {
        method: 'POST',
      });
    case 'download_and_install_github_update':
      return request('/api/runtime/download-and-install-github-update', {
        method: 'POST',
        body: JSON.stringify({ expectedVersion: payload.expectedVersion ?? null }),
      });
    case 'quit_app_for_update':
      return request('/api/runtime/quit-app-for-update', {
        method: 'POST',
      });
    case 'check_github_update':
      return request('/api/runtime/check-github-update', {
        method: 'POST',
        body: JSON.stringify({ currentVersion: payload.currentVersion ?? null }),
      });
    case 'is_autostart_enabled':
      return request('/api/runtime/is-autostart-enabled');
    case 'should_check_updates':
      return request('/api/runtime/should-check-updates');
    // ---- 系统状态 API ----
    case 'is_screen_locked':
      return request('/api/system/is-screen-locked');
    case 'is_work_time':
      return request('/api/system/is-work-time');
    case 'check_permissions':
      return request('/api/system/check-permissions');
    case 'take_screenshot':
      return request('/api/system/take-screenshot', { method: 'POST' });
    case 'run_ocr':
      return request('/api/system/run-ocr', {
        method: 'POST',
        body: JSON.stringify({ imagePath: payload.imagePath }),
      });
    case 'check_ocr_available':
      return request('/api/system/ocr-available');
    case 'get_ocr_install_guide':
      return { available: true, guide: '安装 PaddleOCR: pip install paddleocr paddlepaddle' };
    case 'search_memory':
      return request('/api/assistant/search-memory', {
        method: 'POST',
        body: JSON.stringify({ query: payload.query, limit: payload.limit ?? 8 }),
      });
    case 'ask_memory':
      return request('/api/assistant/chat', {
        method: 'POST',
        body: JSON.stringify({ question: payload.question, locale: payload.locale ?? null }),
      });
    case 'start_recording':
    case 'stop_recording':
      return emitRecordingState([true, false]);
    case 'get_update_settings':
      return request('/api/runtime/should-check-updates');
    case 'save_update_settings':
      return request('/api/runtime/update-last-check-time', { method: 'POST' });
    default:
      throw new Error(`invoke not implemented: ${command}`);
  }
}
