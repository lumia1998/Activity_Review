<script>
  import { createEventDispatcher } from 'svelte';
  import { AVATAR_OUTLINE_LAYOUT, getAvatarOutline } from './avatarOutline.js';
  import { getAvatarModeMeta } from './avatarStateMeta.js';

  const dispatch = createEventDispatcher();

  export let state = {
    mode: 'idle',
    appName: 'Work Review',
    contextLabel: '待命中',
    hint: '',
    isIdle: true,
    isGeneratingReport: false,
    avatarOpacity: 0.82,
  };

  $: outline = getAvatarOutline();
  $: modeMeta = getAvatarModeMeta(state.mode);
  $: eyePath = modeMeta.eyePath;
  $: mouthPath = modeMeta.mouthPath;
  $: leftPawClass = modeMeta.leftPawClass;
  $: rightPawClass = modeMeta.rightPawClass;
  $: shellStyle = `--ear-fill:${modeMeta.earTone}; --cheek-fill:${modeMeta.cheekTone}; --cheek-opacity:${modeMeta.cheekOpacity}; --avatar-shell-opacity:${state.avatarOpacity ?? 0.82};`;

  function handlePointerDown(event) {
    dispatch('avatarpointerdown', { originalEvent: event });
  }

  function handleActivate(event) {
    dispatch('avataractivate', { originalEvent: event });
  }
</script>

<div class="relative h-full w-full overflow-visible select-none">
  <div class={AVATAR_OUTLINE_LAYOUT.figureClass}>
    <svg
      viewBox={AVATAR_OUTLINE_LAYOUT.viewBox}
      class="h-full w-full overflow-visible"
      aria-hidden="true"
    >
      <!-- svelte-ignore a11y-no-static-element-interactions -->
      <g
        class={`avatar-shell ${modeMeta.shellClass}`}
        style={shellStyle}
        on:mousedown={handlePointerDown}
        on:dblclick={handleActivate}
      >
        <g class={`tail ${modeMeta.tailClass}`}>
          <path d={outline.tailPath} class="avatar-hit avatar-fill avatar-stroke tail-detail" />
        </g>

        <g class="body">
          <path d={outline.bodyPath} class="avatar-hit avatar-fill avatar-stroke" />
        </g>

        <g class="head">
          <path d={outline.headPath} class="avatar-hit avatar-fill avatar-stroke" />
          <path d={outline.leftEarInnerPath} class="ear-detail" />
          <path d={outline.rightEarInnerPath} class="ear-detail" />
          <ellipse cx="82" cy="116" rx="5.2" ry="3.1" class="cheek-detail" />
          <ellipse cx="118" cy="116" rx="5.2" ry="3.1" class="cheek-detail" />
          <path d={eyePath} class="face-line" />
          <path d="M98 101 Q100 103 102 101" class="face-line" />
          <path d={mouthPath} class="face-line" />
          <path d="M67 110 H82 M118 110 H133" class="whisker" />
          <path d="M68 117 H83 M117 117 H132" class="whisker soft" />
        </g>

        <g class={`paw ${leftPawClass}`}>
          <path d={outline.leftPawPath} class="avatar-hit avatar-fill avatar-stroke paw-line" />
        </g>
        <g class={`paw ${rightPawClass}`}>
          <path d={outline.rightPawPath} class="avatar-hit avatar-fill avatar-stroke paw-line" />
        </g>
      </g>
    </svg>
  </div>
</div>

<style>
  svg {
    overflow: visible;
  }

  .avatar-shell {
    pointer-events: none;
    opacity: var(--avatar-shell-opacity);
  }

  .avatar-hit {
    pointer-events: visiblePainted;
    cursor: grab;
  }

  .avatar-hit:active {
    cursor: grabbing;
  }

  .tail-detail {
    filter: drop-shadow(0 0 1px rgba(255, 255, 255, 0.78));
  }

  .ear-detail,
  .cheek-detail {
    stroke: none;
    pointer-events: none;
  }

  .ear-detail {
    fill: var(--ear-fill);
  }

  .cheek-detail {
    fill: var(--cheek-fill);
    opacity: var(--cheek-opacity);
  }

  .avatar-stroke,
  .avatar-fill,
  .face-line,
  .whisker {
    fill: none;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .avatar-fill {
    fill: rgba(255, 255, 255, 0.96);
  }

  .avatar-stroke {
    stroke: rgba(30, 41, 59, 0.92);
    stroke-width: 5;
  }

  .face-line {
    stroke: rgba(30, 41, 59, 0.9);
    stroke-width: 4;
  }

  .whisker {
    stroke: rgba(30, 41, 59, 0.45);
    stroke-width: 2.5;
  }

  .whisker.soft {
    opacity: 0.75;
  }

  .avatar-float {
    animation: avatar-float 3.1s ease-in-out infinite;
  }

  .tail {
    transform-origin: 150px 145px;
    animation: tail-swing 2.4s ease-in-out infinite;
  }

  .paw {
    transform-origin: center top;
  }

  .paw-rest {
    animation: paw-rest 2.7s ease-in-out infinite;
  }

  .paw-work-left {
    animation: paw-work-left 0.42s ease-in-out infinite;
  }

  .paw-work-right {
    animation: paw-work-right 0.42s ease-in-out infinite;
  }

  .paw-think-left {
    animation: paw-think-left 0.9s ease-in-out infinite;
  }

  .paw-think-right {
    animation: paw-think-right 0.9s ease-in-out infinite;
  }

  .paw-music-left {
    animation: paw-music-left 0.8s ease-in-out infinite;
  }

  .paw-music-right {
    animation: paw-music-right 0.8s ease-in-out infinite;
  }

  .mode-idle {
    animation-duration: 4.2s;
  }

  .mode-idle .tail {
    animation-duration: 3.4s;
  }

  .tail-reading,
  .tail-meeting {
    animation-duration: 3s;
  }

  .tail-video {
    animation-duration: 3.2s;
  }

  .tail-music {
    animation-duration: 1.6s;
  }

  .tail-generating,
  .tail-working {
    animation-duration: 2s;
  }

  .tail-slacking {
    animation-duration: 3.8s;
    opacity: 0.98;
  }

  @keyframes avatar-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-2.4px); }
  }

  @keyframes tail-swing {
    0%, 100% { transform: rotate(8deg); }
    50% { transform: rotate(-10deg); }
  }

  @keyframes paw-rest {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-2px); }
  }

  @keyframes paw-work-left {
    0%, 100% { transform: translateY(0); }
    50% { transform: translate(-2px, -9px) rotate(-10deg); }
  }

  @keyframes paw-work-right {
    0%, 100% { transform: translateY(-9px) rotate(10deg); }
    50% { transform: translate(2px, 0); }
  }

  @keyframes paw-think-left {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px) rotate(-5deg); }
  }

  @keyframes paw-think-right {
    0%, 100% { transform: translateY(-2px); }
    50% { transform: translateY(1px) rotate(4deg); }
  }

  @keyframes paw-music-left {
    0%, 100% { transform: translate(-1px, 0) rotate(-4deg); }
    50% { transform: translate(-3px, -7px) rotate(-14deg); }
  }

  @keyframes paw-music-right {
    0%, 100% { transform: translate(1px, -1px) rotate(5deg); }
    50% { transform: translate(3px, -8px) rotate(15deg); }
  }

  :global(.dark) .avatar-stroke,
  :global(.dark) .face-line {
    stroke: rgba(241, 245, 249, 0.92);
  }

  :global(.dark) .avatar-fill {
    fill: rgba(248, 250, 252, 0.96);
  }

  :global(.dark) .whisker {
    stroke: rgba(241, 245, 249, 0.28);
  }
</style>
