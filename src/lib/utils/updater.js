import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { relaunch } from '@tauri-apps/plugin-process';
import { confirm } from '$lib/stores/confirm.js';
import { showToast } from '$lib/stores/toast.js';

const UPDATE_STATUS_EVENT = 'update-status';

let updateInFlight = false;

export async function runUpdateFlow(options = {}) {
  const {
    silentWhenUpToDate = false,
    confirmBeforeDownload = false,
    onStatusChange = () => {},
  } = options;

  if (updateInFlight) {
    return { skipped: true, reason: 'in-flight' };
  }

  updateInFlight = true;
  onStatusChange('正在检查更新...');

  try {
    const releaseInfo = await invoke('check_github_update');

    if (!releaseInfo?.available) {
      onStatusChange(silentWhenUpToDate ? '' : '当前已是最新版本');
      if (!silentWhenUpToDate) {
        showToast('当前已是最新版本', 'success');
      }
      return { updated: false, available: false };
    }

    if (confirmBeforeDownload) {
      const shouldStart = await confirm({
        title: '发现新版本',
        message: `检测到新版本 ${releaseInfo.latestVersion}。是否现在开始更新？`,
        confirmText: '立即更新',
        cancelText: '稍后再说',
        tone: 'info',
      });

      if (!shouldStart) {
        onStatusChange('');
        return { updated: false, cancelled: true };
      }
    }

    const unlistenUpdateStatus = await listen(UPDATE_STATUS_EVENT, (event) => {
      const payload = event.payload || {};
      if (payload.message) {
        onStatusChange(payload.message);
      }
    });

    try {
      await invoke('download_and_install_github_update', {
        expectedVersion: releaseInfo.latestVersion,
      });
    } finally {
      await unlistenUpdateStatus();
    }

    onStatusChange('安装完成，正在重启...');
    await relaunch();
    return { updated: true };
  } catch (error) {
    const errMsg = String(error);
    console.error('检查更新失败:', error);

    if (errMsg.includes('timeout') || errMsg.includes('timed out')) {
      onStatusChange('在线更新超时');
      showToast('在线更新超时，已尝试全部更新源', 'error');
    } else if (
      errMsg.includes('Download request failed') ||
      errMsg.includes('failed to download') ||
      errMsg.includes('Network')
    ) {
      onStatusChange('在线更新失败');
      showToast('在线更新失败，已尝试全部更新源', 'error');
    } else {
      onStatusChange('在线更新失败');
      showToast('在线更新失败', 'error');
    }

    await confirm({
      title: '更新错误',
      message: `在线更新未完成：${errMsg}`,
      confirmText: '我知道了',
      cancelText: '稍后重试',
      tone: 'error',
    });

    return { updated: false, error: errMsg };
  } finally {
    updateInFlight = false;
  }
}
