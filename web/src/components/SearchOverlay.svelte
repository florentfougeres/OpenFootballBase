<script lang="ts">
  import { route, t } from "../lib/app.svelte";
  import { searchUi } from "../lib/searchui.svelte";
  import SearchBox from "./SearchBox.svelte";

  // Recherche : plein écran sur mobile (champ en haut, récents et suggestions dessous), palette centrée sur grand écran.
  // « / » et ⌘K l'ouvrent ; Échap, le voile ou « Annuler » la ferment ; un changement de page aussi.
  $effect(() => { route.parts; searchUi.bar = false; });
  const close = () => (searchUi.bar = false);
  function onKey(e: KeyboardEvent) {
    const el = e.target as HTMLElement | null;
    const typing = /^(input|textarea|select)$/i.test(el?.tagName ?? "") || Boolean(el?.isContentEditable);
    if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey && !e.altKey)) { e.preventDefault(); searchUi.bar = true; }
  }
</script>

<svelte:window onkeydown={onKey} />

{#if searchUi.bar}
  <div class="fixed inset-0 z-[70] flex flex-col bg-bg lg:items-center lg:justify-start lg:bg-transparent lg:pt-[12vh]" role="dialog" aria-modal="true" aria-label={t("searchTrigger")}>
    <!-- Voile (grand écran) : un clic à côté ferme -->
    <button type="button" class="fade absolute inset-0 hidden cursor-default bg-black/55 backdrop-blur-[2px] lg:block" aria-label={t("close")} tabindex="-1" onclick={close}></button>
    <div class="panel relative flex min-h-0 w-full flex-1 flex-col px-3 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))] lg:max-w-2xl lg:flex-none lg:rounded-2xl lg:border lg:border-line lg:bg-surface lg:p-3 lg:shadow-2xl">
      <div class="grid min-h-0 grid-cols-[minmax(0,1fr)_auto] content-start items-center gap-x-1 max-lg:flex-1 lg:block">
        <SearchBox variant="overlay" autofocus onclose={close} />
        <button type="button" class="col-start-2 row-start-1 min-h-11 shrink-0 rounded-xl px-3 text-sm font-semibold text-accent lg:hidden" onclick={close}>{t("cancel")}</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .panel { animation: up 250ms cubic-bezier(0.2, 0.8, 0.2, 1); }
  .fade { animation: fade 200ms ease-out; }
  @keyframes up { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
  @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
  @media (prefers-reduced-motion: reduce) { .panel, .fade { animation: none; } }
</style>
