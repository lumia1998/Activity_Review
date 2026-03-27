<script>
  import { onMount } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import { getCurrentWindow } from '@tauri-apps/api/window';
  import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';
  import AvatarCanvas from '../../lib/components/Avatar/AvatarCanvas.svelte';
  import AvatarPopover from '../../lib/components/Avatar/AvatarPopover.svelte';
  import { getAvatarStateBubble } from '../../lib/components/Avatar/avatarStateMeta.js';

  const appWindow = getCurrentWebviewWindow();
  const nativeWindow = getCurrentWindow();

  let state = {
    mode: 'idle',
    appName: 'Work Review',
    contextLabel: '待命中',
    hint: '准备陪你开始工作',
    isIdle: true,
    isGeneratingReport: false,
    avatarOpacity: 0.82,
  };
  let bubble = null;
  let bubbleTimer = null;
  let lastStateBubbleAt = 0;

  function showBubble(payload) {
    bubble = payload;
    clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => {
      bubble = null;
      bubbleTimer = null;
    }, payload?.duration ?? 4200);
  }

  async function openMainWindow() {
    try {
      await invoke('show_main_window');
    } catch (e) {
      console.error('显示主窗口失败:', e);
    }
  }

  async function startAvatarDrag(event) {
    const originalEvent = event.detail?.originalEvent ?? event;

    if (originalEvent.button !== 0) {
      return;
    }

    originalEvent.preventDefault?.();

    try {
      await nativeWindow.startDragging();
    } catch (e) {
      console.error('拖动桌宠失败:', e);
    }
  }

  onMount(() => {
    let unlistenState = () => {};
    let unlistenBubble = () => {};

    (async () => {
      try {
        state = await invoke('get_avatar_state');
      } catch (e) {
        console.error('获取桌宠状态失败:', e);
      }

      unlistenState = await appWindow.listen('avatar-state-changed', (event) => {
        const nextState = event.payload;
        const stateBubble = getAvatarStateBubble(nextState.mode);

        if (
          stateBubble &&
          nextState.mode !== state.mode &&
          Date.now() - lastStateBubbleAt > 900
        ) {
          lastStateBubbleAt = Date.now();
          showBubble(stateBubble);
        }

        state = nextState;
      });

      unlistenBubble = await appWindow.listen('avatar-bubble', (event) => {
        showBubble(event.payload);
      });
    })();

    return () => {
      clearTimeout(bubbleTimer);
      unlistenState();
      unlistenBubble();
    };
  });
</script>

<div class="relative h-screen w-screen overflow-visible bg-transparent select-none">
  <AvatarPopover {bubble} />

  <div class="h-full w-full">
    <AvatarCanvas
      {state}
      on:avatarpointerdown={startAvatarDrag}
      on:avataractivate={openMainWindow}
    />
  </div>
</div>

<style>
  :global(:root),
  :global(html),
  :global(body) {
    background: transparent !important;
  }

  :global(body) {
    margin: 0;
    overflow: hidden;
  }
</style>
