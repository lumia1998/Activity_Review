export const AVATAR_SCALE_MIN = 0.7;
export const AVATAR_SCALE_MAX = 1.3;
export const AVATAR_SCALE_DEFAULT = 0.9;
export const AVATAR_OPACITY_MIN = 0.45;
export const AVATAR_OPACITY_MAX = 1;
export const AVATAR_OPACITY_DEFAULT = 0.82;

export function getAvatarToggleToast(enabled) {
  return enabled
    ? '桌宠已显示，可在屏幕右下角附近查看'
    : '桌宠已隐藏';
}

export function getAvatarToggleUiState(enabled, saving = false) {
  return {
    trackClass: enabled
      ? 'bg-primary-500 hover:bg-primary-500/90'
      : 'bg-slate-300 hover:bg-slate-400 dark:bg-slate-600 dark:hover:bg-slate-500',
    thumbClass: enabled ? 'translate-x-5' : 'translate-x-0',
    buttonClass: saving ? 'cursor-wait opacity-80' : 'cursor-pointer',
    ariaLabel: enabled ? '关闭桌面化身' : '开启桌面化身',
  };
}

export async function toggleAvatarSetting(config, saveConfig) {
  const previousEnabled = Boolean(config.avatar_enabled);
  const nextEnabled = !previousEnabled;

  config.avatar_enabled = nextEnabled;

  try {
    await saveConfig(config);
    return nextEnabled;
  } catch (error) {
    config.avatar_enabled = previousEnabled;
    throw error;
  }
}

export function clampAvatarScale(value) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return AVATAR_SCALE_DEFAULT;
  }

  return Math.min(AVATAR_SCALE_MAX, Math.max(AVATAR_SCALE_MIN, numericValue));
}

export function formatAvatarScaleLabel(value) {
  return `${Math.round(clampAvatarScale(value) * 100)}%`;
}

export async function updateAvatarScaleSetting(config, nextScale, saveConfig) {
  const previousScale = clampAvatarScale(config.avatar_scale);
  const clampedScale = clampAvatarScale(nextScale);

  config.avatar_scale = clampedScale;

  try {
    await saveConfig(config);
    return clampedScale;
  } catch (error) {
    config.avatar_scale = previousScale;
    throw error;
  }
}

export function clampAvatarOpacity(value) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return AVATAR_OPACITY_DEFAULT;
  }

  return Math.min(AVATAR_OPACITY_MAX, Math.max(AVATAR_OPACITY_MIN, numericValue));
}

export function formatAvatarOpacityLabel(value) {
  return `${Math.round(clampAvatarOpacity(value) * 100)}%`;
}

export async function updateAvatarOpacitySetting(config, nextOpacity, saveConfig) {
  const previousOpacity = clampAvatarOpacity(config.avatar_opacity);
  const clampedOpacity = clampAvatarOpacity(nextOpacity);

  config.avatar_opacity = clampedOpacity;

  try {
    await saveConfig(config);
    return clampedOpacity;
  } catch (error) {
    config.avatar_opacity = previousOpacity;
    throw error;
  }
}
