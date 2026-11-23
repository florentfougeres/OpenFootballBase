<script lang="ts">
  import type { Snippet } from "svelte";
  import { t } from "../lib/app.svelte";

  // Feuille modale : montée depuis le bas sur mobile, boîte centrée sur grand écran. Échap, le voile ou le bouton la ferment ;
  // le focus y entre à l'ouverture, y reste (Tab) et revient au déclencheur à la fermeture.
  let { open, onclose, title, children }: { open: boolean; onclose: () => void; title: string; children: Snippet } = $props();
  let box: HTMLElement | undefined = $state();
  let from: HTMLElement | null = null;

  $effect(() => {
    if (!open) return;
    from = document.activeElement as HTMLElement | null;
    queueMicrotask(() => box?.focus());
    return () => from?.focus?.();
  });

  function onKey(e: KeyboardEvent) {
    if (e.key === "Escape") { e.preventDefault(); onclose(); return; }
    if (e.key !== "Tab" || !box) return;
    const f = [...box.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),select,input,[tabindex]:not([tabindex="-1"])')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    const a = document.activeElement;
    if (e.shiftKey && (a === f[0] || a === box)) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && a === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
  }
</script>

{#if open}
  <div class="fixed inset-0 z-[65] flex items-end justify-center lg:items-center" role="presentation" onkeydown={onKey}>
    <button type="button" class="veil absolute inset-0 cursor-default bg-black/55" aria-label={t("close")} tabindex="-1" onclick={onclose}></button>
    <div bind:this={box} tabindex="-1" role="dialog" aria-modal="true" aria-label={title}
      class="sheet relative flex max-h-[85dvh] w-full flex-col rounded-t-3xl border border-line bg-surface pb-[env(safe-area-inset-bottom)] shadow-2xl outline-none lg:max-w-md lg:rounded-3xl">
      <div class="mx-auto mt-2.5 h-1 w-10 rounded-full bg-line lg:hidden" aria-hidden="true"></div>
      <div class="flex items-center justify-between gap-3 px-5 pb-2 pt-3">
        <h2 class="text-xl font-bold">{title}</h2>
        <button type="button" class="grid size-11 place-items-center rounded-xl text-muted transition hover:bg-surface-2 hover:text-fg" aria-label={t("close")} onclick={onclose}>
          <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg>
        </button>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto overscroll-contain px-2 pb-4">{@render children()}</div>
    </div>
  </div>
{/if}

<style>
  .sheet { animation: rise 250ms cubic-bezier(0.2, 0.8, 0.2, 1); }
  .veil { animation: fade 200ms ease-out; }
  @keyframes rise { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: none; } }
  @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
  @media (prefers-reduced-motion: reduce) { .sheet, .veil { animation: none; } }
</style>
