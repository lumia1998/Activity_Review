<script>
  export let bubble = null;

  $: bubbleChars = bubble?.message ? Array.from(bubble.message.replace(/\s+/g, '')) : [];
  $: toneClasses =
    bubble?.tone === 'success'
      ? 'border-emerald-200/80 bg-emerald-50/92 text-emerald-900'
      : 'border-white/80 bg-white/92 text-slate-700';
</script>

{#if bubble}
  <div class="pointer-events-none absolute top-0 z-20" style="right: 4%; top: 2%;">
    <div class="flex flex-col items-end">
      <div
        class="rounded-[18px] border text-center shadow-[0_14px_28px_rgba(15,23,42,0.14)] backdrop-blur-xl {toneClasses}"
        style="min-width: clamp(22px, 14vw, 30px); padding: clamp(6px, 4vw, 9px) clamp(6px, 3.2vw, 8px);"
      >
        <div
          class="flex flex-col items-center"
          style="gap: clamp(1px, 0.8vw, 3px); font-size: clamp(10px, 7vw, 13px); line-height: 1;"
        >
          {#each bubbleChars as char}
            <span class="block font-semibold tracking-[0.02em]">{char}</span>
          {/each}
        </div>
      </div>
      <div
        class="mr-2 mt-[-1px] h-2.5 w-2.5 rotate-45 border-b border-r shadow-[2px_2px_4px_rgba(15,23,42,0.06)] {toneClasses}"
        aria-hidden="true"
      />
    </div>
  </div>
{/if}
