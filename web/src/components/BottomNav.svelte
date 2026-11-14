<script lang="ts">
  import { route, href, t } from "../lib/app.svelte";
  import { theme, cycleTheme } from "../lib/theme.svelte";

  // Navigation principale sur mobile : une barre fixe en bas, à portée du pouce, avec des libellés toujours visibles
  // (un menu hamburger en haut à droite cache la navigation et se trouve mal). Les pages secondaires sont sous « Plus ».
  let more = $state(false);
  const current = $derived(route.parts[0] ?? "home");
  const isActive = (k: string) =>
    k === "home" ? current === "home" : k === "clubs" ? ["clubs", "club"].includes(current) : k === "players" ? ["players", "player"].includes(current)
    : k === "competitions" ? ["competitions", "competition"].includes(current) : ["coverage", "about"].includes(current);
  const items = $derived([
    { key: "home", label: t("home"), to: href("") },
    { key: "clubs", label: t("clubs"), to: href("clubs") },
    { key: "players", label: t("players"), to: href("players") },
    { key: "competitions", label: t("allComps"), to: href("competitions") },
  ]);
  $effect(() => { route.parts; more = false; });
  const themeLabel = $derived(theme.value === "dark" ? t("themeDark") : theme.value === "light" ? t("themeLight") : t("themeAuto"));
</script>

<svelte:window onkeydown={(e) => { if (e.key === "Escape") more = false; }} />

{#if more}
  <!-- Voile : un tap à côté ferme le panneau -->
  <button type="button" class="fixed inset-0 z-40 cursor-default bg-fg/20 md:hidden" aria-label={t("close")} onclick={() => (more = false)} tabindex="-1"></button>
  <div id="more-panel" class="fixed inset-x-3 bottom-[calc(4.25rem+env(safe-area-inset-bottom))] z-50 rounded-2xl border border-line bg-surface p-2 shadow-2xl md:hidden" role="menu">
    <a class="flex min-h-12 items-center rounded-xl px-4 text-base font-semibold no-underline hover:bg-surface-2 {current === 'coverage' ? 'bg-surface-2' : ''}" href={href("coverage")} role="menuitem">{t("coverage")}</a>
    <a class="flex min-h-12 items-center rounded-xl px-4 text-base font-semibold no-underline hover:bg-surface-2 {current === 'about' ? 'bg-surface-2' : ''}" href={href("about")} role="menuitem">{t("about")}</a>
    <button type="button" class="flex min-h-12 w-full items-center justify-between rounded-xl border-t border-line px-4 text-left text-base font-semibold hover:bg-surface-2" role="menuitem" onclick={cycleTheme}>
      <span>{t("theme")}</span><span class="text-sm font-medium text-muted">{themeLabel}</span>
    </button>
  </div>
{/if}

<nav class="fixed inset-x-0 bottom-0 z-50 border-t border-line bg-bg/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden" aria-label="Navigation">
  <ul class="mx-auto grid max-w-lg grid-cols-5">
    {#each items as it (it.key)}
      <li>
        <a class="relative flex min-h-14 flex-col items-center justify-center gap-0.5 px-1 text-[0.68rem] font-semibold no-underline transition {isActive(it.key) ? 'text-accent' : 'text-muted active:text-fg'}"
          href={it.to} aria-current={isActive(it.key) ? "page" : undefined}>
          {#if isActive(it.key)}<span class="absolute inset-x-5 top-0 h-0.5 rounded-b bg-accent" aria-hidden="true"></span>{/if}
          <svg viewBox="0 0 24 24" class="size-[22px]" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            {#if it.key === "home"}<path d="M3.5 11 12 4l8.5 7M6 9.5V20h12V9.5M10 20v-5h4v5" />
            {:else if it.key === "clubs"}<path d="M12 3 5 5.5V11c0 4.2 2.8 7.4 7 9 4.2-1.6 7-4.8 7-9V5.5z" /><path d="M12 8v5m-2.5-2.5h5" />
            {:else if it.key === "players"}<circle cx="12" cy="8" r="3.5" /><path d="M5 20c.7-3.6 3.3-5.5 7-5.5s6.3 1.9 7 5.5" />
            {:else}<path d="M8 4h8v5a4 4 0 0 1-8 0z" /><path d="M8 6H5.5a2 2 0 0 0 0 4H8M16 6h2.5a2 2 0 0 1 0 4H16" /><path d="M12 13v4M8.5 20h7M10 17h4" />{/if}
          </svg>
          <span class="truncate">{it.label}</span>
        </a>
      </li>
    {/each}
    <li>
      <button type="button" class="relative flex min-h-14 w-full flex-col items-center justify-center gap-0.5 px-1 text-[0.68rem] font-semibold transition {more || isActive('more') ? 'text-accent' : 'text-muted active:text-fg'}"
        aria-expanded={more} aria-controls="more-panel" aria-haspopup="menu" onclick={() => (more = !more)}>
        {#if isActive("more") && !more}<span class="absolute inset-x-5 top-0 h-0.5 rounded-b bg-accent" aria-hidden="true"></span>{/if}
        <svg viewBox="0 0 24 24" class="size-[22px]" fill="currentColor" aria-hidden="true"><circle cx="5.5" cy="12" r="1.7" /><circle cx="12" cy="12" r="1.7" /><circle cx="18.5" cy="12" r="1.7" /></svg>
        <span>{t("more")}</span>
      </button>
    </li>
  </ul>
</nav>
