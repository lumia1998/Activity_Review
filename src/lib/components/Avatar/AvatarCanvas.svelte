<script>
  import { createEventDispatcher } from 'svelte';
  import { AVATAR_OUTLINE_LAYOUT, getAvatarOutline } from './avatarOutline.js';
  import {
    getAvatarActionLoopMeta,
    getAvatarIdleMotionMeta,
    getAvatarModeMeta,
  } from './avatarStateMeta.js';

  const dispatch = createEventDispatcher();

  export let state = {
    mode: 'idle',
    appName: 'Activity Review',
    contextLabel: '待命中',
    hint: '',
    isIdle: true,
    isGeneratingReport: false,
    avatarOpacity: 0.82,
  };
  export let transitionClass = '';
  export let motionBeat = 0;

  $: outline = getAvatarOutline();
  $: modeMeta = getAvatarModeMeta(state.mode, state.contextLabel);
  $: actionLoopMeta = getAvatarActionLoopMeta(state.mode, state.contextLabel, motionBeat);
  $: idleMotionMeta = getAvatarIdleMotionMeta(state.mode, state.contextLabel, motionBeat);
  $: resolvedMeta = { ...modeMeta, ...actionLoopMeta };
  $: eyePath = resolvedMeta.eyePath;
  $: mouthPath = resolvedMeta.mouthPath;
  $: leftPawClass = resolvedMeta.leftPawClass;
  $: rightPawClass = resolvedMeta.rightPawClass;
  $: tailClass = resolvedMeta.tailClass;
  $: shellClass = ['avatar-shell', resolvedMeta.shellClass, idleMotionMeta.shellClass, transitionClass]
    .filter(Boolean)
    .join(' ');
  $: headClass = ['head', idleMotionMeta.headClass].filter(Boolean).join(' ');
  $: shellStyle = `--ear-fill:${resolvedMeta.earTone}; --cheek-fill:${resolvedMeta.cheekTone}; --cheek-opacity:${resolvedMeta.cheekOpacity}; --avatar-shell-opacity:${state.avatarOpacity ?? 0.82};`;

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
        class={shellClass}
        style={shellStyle}
        on:mousedown={handlePointerDown}
        on:dblclick={handleActivate}
      >
        <g class={`tail ${tailClass}`}>
          <path d={outline.tailPath} class="avatar-hit avatar-fill avatar-stroke tail-detail" />
        </g>

        <g class="body">
          <path d={outline.bodyPath} class="avatar-hit avatar-fill avatar-stroke" />
        </g>

        <g class={headClass}>
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

  .idle-breathe {
    animation: idle-breathe 3.6s ease-in-out infinite;
  }

  .idle-sway {
    animation: idle-sway 4.2s ease-in-out infinite;
  }

  .idle-observe {
    animation: idle-observe 4.8s ease-in-out infinite;
  }

  .idle-groove {
    animation: idle-groove 2.8s ease-in-out infinite;
  }

  .idle-focus-pulse {
    animation: idle-focus-pulse 3.1s ease-in-out infinite;
  }

  .idle-head-neutral {
    transform-origin: 100px 104px;
  }

  .idle-head-tilt {
    transform-origin: 100px 104px;
    animation: idle-head-tilt 3.9s ease-in-out infinite;
  }

  .idle-head-peek {
    transform-origin: 100px 104px;
    animation: idle-head-peek 4.4s ease-in-out infinite;
  }

  .idle-head-dip {
    transform-origin: 100px 104px;
    animation: idle-head-dip 4s ease-in-out infinite;
  }

  .idle-head-bob {
    transform-origin: 100px 104px;
    animation: idle-head-bob 2.7s ease-in-out infinite;
  }

  .idle-head-focus {
    transform-origin: 100px 104px;
    animation: idle-head-focus 3.2s ease-in-out infinite;
  }

  .transition-alert {
    animation: transition-alert 0.72s ease-out;
  }

  .transition-settle {
    animation: transition-settle 0.68s ease-out;
  }

  .transition-snap-back {
    animation: transition-snap-back 0.76s ease-out;
  }

  .transition-focus-shift {
    animation: transition-focus-shift 0.64s ease-out;
  }

  .transition-glide {
    animation: transition-glide 0.62s ease-out;
  }

  .transition-lift {
    animation: transition-lift 0.66s ease-out;
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

  .paw-write-left {
    animation: paw-write-left 0.76s ease-in-out infinite;
  }

  .paw-write-right {
    animation: paw-write-right 0.76s ease-in-out infinite;
  }

  .paw-chat-left {
    animation: paw-chat-left 1.05s ease-in-out infinite;
  }

  .paw-chat-right {
    animation: paw-chat-right 1.05s ease-in-out infinite;
  }

  .paw-create-left {
    animation: paw-create-left 1.2s ease-in-out infinite;
  }

  .paw-create-right {
    animation: paw-create-right 1.2s ease-in-out infinite;
  }

  .paw-meeting-left {
    animation: paw-meeting-left 1.4s ease-in-out infinite;
  }

  .paw-meeting-right {
    animation: paw-meeting-right 1.4s ease-in-out infinite;
  }

  .paw-video-left {
    animation: paw-video-left 2.1s ease-in-out infinite;
  }

  .paw-video-right {
    animation: paw-video-right 2.1s ease-in-out infinite;
  }

  .paw-generate-left {
    animation: paw-generate-left 1s ease-in-out infinite;
  }

  .paw-generate-right {
    animation: paw-generate-right 1s ease-in-out infinite;
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

  .tail-writing {
    animation-duration: 2.8s;
  }

  .tail-coding {
    animation-duration: 1.7s;
  }

  .tail-planning {
    animation-duration: 2.6s;
  }

  .tail-scheduling {
    animation-duration: 2.9s;
  }

  .tail-chatting {
    animation-duration: 1.8s;
  }

  .tail-creative {
    animation-duration: 1.9s;
  }

  .tail-research {
    animation-duration: 2.2s;
  }

  .tail-observing {
    animation-duration: 3.5s;
  }

  .tail-slacking {
    animation-duration: 3.8s;
    opacity: 0.98;
  }

  .tail-music-groove {
    animation-duration: 1.35s;
  }

  .tail-loop-wide {
    animation: tail-swing-wide 1.8s ease-in-out infinite;
  }

  .tail-loop-tight {
    animation: tail-swing-tight 2.4s ease-in-out infinite;
  }

  .tail-loop-flick {
    animation: tail-flick 1.2s ease-in-out infinite;
  }

  .tail-podcast {
    animation-duration: 2.4s;
  }

  .tail-video-watch {
    animation-duration: 3.8s;
  }

  .tail-learning {
    animation-duration: 2.6s;
  }

  .tail-generating-focus {
    animation-duration: 1.75s;
  }

  .tail-presenting {
    animation-duration: 2.2s;
  }

  @keyframes avatar-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-2.4px); }
  }

  @keyframes idle-breathe {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-1.6px) scale(1.006); }
  }

  @keyframes idle-sway {
    0%, 100% { transform: translateX(0) translateY(0); }
    50% { transform: translateX(-1.8px) translateY(-1.2px); }
  }

  @keyframes idle-observe {
    0%, 100% { transform: translateY(0); }
    30% { transform: translate(-1px, -1.4px); }
    65% { transform: translate(1.4px, -0.6px); }
  }

  @keyframes idle-groove {
    0%, 100% { transform: translateX(0) translateY(0) rotate(0deg); }
    25% { transform: translateX(-1.6px) translateY(-1.2px) rotate(-0.8deg); }
    75% { transform: translateX(1.6px) translateY(-0.6px) rotate(0.8deg); }
  }

  @keyframes idle-focus-pulse {
    0%, 100% { transform: scale(1) translateY(0); }
    50% { transform: scale(1.01) translateY(-1px); }
  }

  @keyframes idle-head-tilt {
    0%, 100% { transform: rotate(0deg); }
    50% { transform: rotate(-2.6deg); }
  }

  @keyframes idle-head-peek {
    0%, 100% { transform: translateX(0); }
    50% { transform: translateX(2px); }
  }

  @keyframes idle-head-dip {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(1.6px); }
  }

  @keyframes idle-head-bob {
    0%, 100% { transform: rotate(0deg) translateY(0); }
    50% { transform: rotate(-1.6deg) translateY(1px); }
  }

  @keyframes idle-head-focus {
    0%, 100% { transform: translateX(0) scale(1); }
    50% { transform: translateX(1.2px) scale(1.01); }
  }

  @keyframes tail-swing {
    0%, 100% { transform: rotate(8deg); }
    50% { transform: rotate(-10deg); }
  }

  @keyframes tail-swing-wide {
    0%, 100% { transform: rotate(14deg); }
    50% { transform: rotate(-16deg); }
  }

  @keyframes tail-swing-tight {
    0%, 100% { transform: rotate(5deg); }
    50% { transform: rotate(-7deg); }
  }

  @keyframes tail-flick {
    0%, 100% { transform: rotate(8deg); }
    35% { transform: rotate(-4deg); }
    55% { transform: rotate(16deg); }
    75% { transform: rotate(-10deg); }
  }

  @keyframes transition-alert {
    0% { transform: scale(0.98) translateY(4px); }
    50% { transform: scale(1.02) translateY(-3px); }
    100% { transform: scale(1) translateY(0); }
  }

  @keyframes transition-settle {
    0% { transform: translateY(-3px) rotate(-1deg); }
    100% { transform: translateY(0) rotate(0); }
  }

  @keyframes transition-snap-back {
    0% { transform: translateX(-4px) translateY(2px); }
    60% { transform: translateX(2px) translateY(-2px); }
    100% { transform: translateX(0) translateY(0); }
  }

  @keyframes transition-focus-shift {
    0% { transform: translateX(2px); }
    50% { transform: translateX(-2px) translateY(-1px); }
    100% { transform: translateX(0) translateY(0); }
  }

  @keyframes transition-glide {
    0% { transform: translateY(2px); }
    100% { transform: translateY(0); }
  }

  @keyframes transition-lift {
    0% { transform: translateY(4px) scale(0.985); }
    55% { transform: translateY(-3px) scale(1.01); }
    100% { transform: translateY(0) scale(1); }
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

  @keyframes paw-write-left {
    0%, 100% { transform: translate(-1px, -1px) rotate(-2deg); }
    50% { transform: translate(-4px, -7px) rotate(-12deg); }
  }

  @keyframes paw-write-right {
    0%, 100% { transform: translate(1px, -3px) rotate(5deg); }
    50% { transform: translate(2px, 2px) rotate(10deg); }
  }

  @keyframes paw-chat-left {
    0%, 100% { transform: translateY(0) rotate(-3deg); }
    50% { transform: translate(-3px, -6px) rotate(-14deg); }
  }

  @keyframes paw-chat-right {
    0%, 100% { transform: translateY(-1px) rotate(3deg); }
    50% { transform: translate(4px, -4px) rotate(16deg); }
  }

  @keyframes paw-create-left {
    0%, 100% { transform: translate(-1px, 0) rotate(-4deg); }
    50% { transform: translate(-5px, -8px) rotate(-12deg); }
  }

  @keyframes paw-create-right {
    0%, 100% { transform: translate(1px, -2px) rotate(6deg); }
    50% { transform: translate(3px, 3px) rotate(14deg); }
  }

  @keyframes paw-meeting-left {
    0%, 100% { transform: translateY(-1px) rotate(-2deg); }
    50% { transform: translate(-2px, -5px) rotate(-9deg); }
  }

  @keyframes paw-meeting-right {
    0%, 100% { transform: translateY(-2px) rotate(3deg); }
    50% { transform: translate(2px, -4px) rotate(8deg); }
  }

  @keyframes paw-video-left {
    0%, 100% { transform: translateY(0) rotate(-1deg); }
    50% { transform: translate(-1px, -3px) rotate(-4deg); }
  }

  @keyframes paw-video-right {
    0%, 100% { transform: translateY(-1px) rotate(2deg); }
    50% { transform: translate(1px, -2px) rotate(5deg); }
  }

  @keyframes paw-generate-left {
    0%, 100% { transform: translate(-1px, -1px) rotate(-3deg); }
    50% { transform: translate(-3px, -5px) rotate(-9deg); }
  }

  @keyframes paw-generate-right {
    0%, 100% { transform: translate(1px, -3px) rotate(4deg); }
    50% { transform: translate(2px, 1px) rotate(8deg); }
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
