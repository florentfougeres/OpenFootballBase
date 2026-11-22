<script lang="ts">
  import { app, route, href, nav, t } from "../lib/app.svelte";
  import { page } from "../lib/app.svelte";

  // En-tête mobile (sur grand écran, la barre latérale prend le relais) : un retour quand on est dans une page enfant, sinon la marque ;
  // le titre de la page apparaît quand on a défilé ; un engrenage (page Réglages : thème, langue…) à droite. La recherche est le bouton central de la barre du bas.
  let scrolled = $state(false);
  const title = $derived(page.name ?? "");
</script>

<svelte:window onscroll={() => (scrolled = scrollY > 56)} />

<header class="sticky top-0 z-30 border-b border-line bg-bg/90 backdrop-blur lg:hidden">
  <div class="flex min-h-14 items-center gap-1 px-2 pt-[env(safe-area-inset-top)]">
    {#if nav.depth > 0}
      <button type="button" class="grid size-11 shrink-0 place-items-center rounded-xl transition active:bg-surface-2" aria-label={t("back")} onclick={() => history.back()}>
        <svg viewBox="0 0 24 24" class="size-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 5-7 7 7 7" /></svg>
      </button>
      <span class="display min-w-0 flex-1 truncate text-lg font-bold transition-opacity {scrolled && title ? 'opacity-100' : 'opacity-0'}" aria-hidden="true">{title}</span>
    {:else}
      <a class="display flex min-w-0 flex-1 items-center gap-2 pl-2 text-xl font-extrabold tracking-tight no-underline" href={href("")}>
        <img class="size-8" src={import.meta.env.BASE_URL + "logo.svg"} alt="" width="32" height="32" />OpenFootballBase
      </a>
    {/if}
    <a class="grid size-11 shrink-0 place-items-center rounded-xl no-underline transition active:bg-surface-2" href={href("settings")} aria-label={t("settings")} aria-current={route.parts[0] === "settings" ? "page" : undefined}>
      <svg viewBox="0 0 24 24" class="size-[22px]" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" /></svg>
    </a>
  </div>
</header>
