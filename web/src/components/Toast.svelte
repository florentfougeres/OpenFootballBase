<script lang="ts">
  import { toast } from "../lib/toast.svelte";
</script>

<!-- Au-dessus de la barre du bas sur mobile, en bas à droite sur grand écran. -->
<div class="pointer-events-none fixed inset-x-0 bottom-[calc(6.5rem+env(safe-area-inset-bottom))] z-[60] flex justify-center px-4 lg:bottom-6 lg:justify-end lg:px-8" role="status" aria-live="polite">
  {#if toast.text}
    {#key toast.n}
      <div class="toast rounded-xl bg-fg px-4 py-2.5 text-sm font-semibold text-bg shadow-lg">{toast.text}</div>
    {/key}
  {/if}
</div>

<style>
  .toast { animation: rise 250ms cubic-bezier(0.2, 0.8, 0.2, 1); }
  @keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
  @media (prefers-reduced-motion: reduce) { .toast { animation: none; } }
</style>
