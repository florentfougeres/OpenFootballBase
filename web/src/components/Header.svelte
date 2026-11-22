<script lang="ts">
  import { app, route, href, nav, t } from "../lib/app.svelte";
  import { theme, cycleTheme } from "../lib/theme.svelte";
  import { page } from "../lib/app.svelte";

  // En-tête mobile (sur grand écran, la barre latérale prend le relais) : un retour quand on est dans une page enfant, sinon la marque ;
  // le titre de la page apparaît quand on a défilé ; la langue et le thème à droite. La recherche est le bouton central de la barre du bas.
  const other = $derived(app.lang === "fr" ? "en" : "fr");
  const switchHref = $derived(`#/${other}/${route.parts.map(encodeURIComponent).join("/")}`);
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
    <button class="grid size-11 shrink-0 place-items-center rounded-xl transition active:bg-surface-2" type="button" onclick={cycleTheme} title={t("theme")} aria-label={t("theme")}>
      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        {#if theme.value === "dark"}<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z" />
        {:else if theme.value === "light"}<circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        {:else}<rect x="3" y="4" width="18" height="12" rx="2" /><path d="M8 20h8M12 16v4" />{/if}
      </svg>
    </button>
    <a class="grid size-11 shrink-0 place-items-center rounded-xl text-sm font-bold uppercase no-underline transition active:bg-surface-2" href={switchHref} hreflang={other} lang={other}>{other}</a>
  </div>
</header>
