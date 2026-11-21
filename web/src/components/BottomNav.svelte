<script lang="ts">
  import { route, href, t } from "../lib/app.svelte";
  import { theme, cycleTheme } from "../lib/theme.svelte";

  // Navigation principale sur mobile : une pilule flottante en bas, à portée du pouce, en verre dépoli (à la manière des barres d'onglets d'iOS),
  // avec des libellés toujours visibles. Une capsule glisse sous l'onglet actif. Les pages secondaires sont sous « Plus ».
  let more = $state(false);
  const current = $derived(route.parts[0] ?? "home");
  const isActive = (k: string) =>
    k === "home" ? current === "home" : k === "clubs" ? ["clubs", "club"].includes(current) : k === "players" ? ["players", "player"].includes(current)
    : k === "competitions" ? ["competitions", "competition"].includes(current) : ["coverage", "about", "ballon-dor"].includes(current);
  const items = $derived([
    { key: "home", label: t("home"), to: href("") },
    { key: "clubs", label: t("clubs"), to: href("clubs") },
    { key: "players", label: t("players"), to: href("players") },
    { key: "competitions", label: t("allComps"), to: href("competitions") },
  ]);
  const KEYS = ["home", "clubs", "players", "competitions", "more"];
  // Position de la capsule : l'onglet « Plus » quand son panneau est ouvert ou qu'une page secondaire est affichée ; aucune capsule sur une page sans onglet (404).
  const lens = $derived(more ? 4 : KEYS.findIndex((k) => isActive(k)));
  $effect(() => { route.parts; more = false; });
  const themeLabel = $derived(theme.value === "dark" ? t("themeDark") : theme.value === "light" ? t("themeLight") : t("themeAuto"));
</script>

<svelte:window onkeydown={(e) => { if (e.key === "Escape") more = false; }} />

{#if more}
  <!-- Voile : un tap à côté ferme le panneau -->
  <button type="button" class="fixed inset-0 z-40 cursor-default bg-fg/20 lg:hidden" aria-label={t("close")} onclick={() => (more = false)} tabindex="-1"></button>
  <div id="more-panel" class="pill fixed inset-x-3 bottom-[calc(5.75rem+env(safe-area-inset-bottom))] z-50 mx-auto max-w-md rounded-3xl p-2 lg:hidden" role="menu">
    <a class="flex min-h-12 items-center rounded-2xl px-4 text-base font-semibold no-underline hover:bg-fg/10 {current === 'ballon-dor' ? 'bg-fg/10' : ''}" href={href("ballon-dor")} role="menuitem">{t("balloon")}</a>
    <a class="flex min-h-12 items-center rounded-2xl px-4 text-base font-semibold no-underline hover:bg-fg/10 {current === 'coverage' ? 'bg-fg/10' : ''}" href={href("coverage")} role="menuitem">{t("coverage")}</a>
    <a class="flex min-h-12 items-center rounded-2xl px-4 text-base font-semibold no-underline hover:bg-fg/10 {current === 'about' ? 'bg-fg/10' : ''}" href={href("about")} role="menuitem">{t("about")}</a>
    <button type="button" class="flex min-h-12 w-full items-center justify-between rounded-2xl px-4 text-left text-base font-semibold hover:bg-fg/10" role="menuitem" onclick={cycleTheme}>
      <span>{t("theme")}</span><span class="text-sm font-medium text-muted">{themeLabel}</span>
    </button>
  </div>
{/if}

<!-- Dock : une bande pleine en bas de l'écran (rien de la page ne passe derrière) ; la pilule y est posée. -->
<div class="fixed inset-x-0 bottom-0 z-50 border-t border-line bg-bg px-3 pb-[calc(env(safe-area-inset-bottom)+0.5rem)] pt-2 lg:hidden">
  <nav class="pill mx-auto max-w-md rounded-full" aria-label="Navigation">
    <ul class="tabs relative grid grid-cols-5 p-1" style="--i: {Math.max(lens, 0)}">
      <li class="lens" class:lens-off={lens < 0} aria-hidden="true"></li>
      {#each items as it (it.key)}
        <li class="relative">
          <a class="tab" class:on={isActive(it.key) && !more} href={it.to} aria-current={isActive(it.key) ? "page" : undefined}>
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
      <li class="relative">
        <button type="button" class="tab" class:on={more || isActive("more")} aria-expanded={more} aria-controls="more-panel" aria-haspopup="menu" onclick={() => (more = !more)}>
          <svg viewBox="0 0 24 24" class="size-[22px]" fill="currentColor" aria-hidden="true"><circle cx="5.5" cy="12" r="1.7" /><circle cx="12" cy="12" r="1.7" /><circle cx="18.5" cy="12" r="1.7" /></svg>
          <span>{t("more")}</span>
        </button>
      </li>
    </ul>
  </nav>
</div>

<style>
  /* La pilule : une surface pleine (comme un dock, aucun contenu ne se devine derrière), un filet clair en haut pour le relief et une ombre douce. */
  .pill {
    background: var(--surface);
    border: 1px solid color-mix(in oklab, var(--fg) 14%, transparent);
    box-shadow:
      inset 0 1px 0 color-mix(in oklab, white 14%, transparent),
      0 8px 20px -8px rgb(0 0 0 / 0.45),
      0 1px 4px rgb(0 0 0 / 0.16);
  }

  /* Capsule de sélection : un seul élément qui glisse sous l'onglet actif (5 colonnes égales). */
  .lens {
    position: absolute;
    inset-block: 0.25rem;
    inset-inline-start: 0.25rem;
    width: calc((100% - 0.5rem) / 5);
    border-radius: 9999px;
    background: color-mix(in oklab, var(--accent) 17%, transparent);
    box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--accent) 28%, transparent), inset 0 1px 0 color-mix(in oklab, white 16%, transparent);
    transform: translateX(calc(var(--i) * 100%));
    transition: transform 420ms cubic-bezier(0.22, 1, 0.36, 1), opacity 200ms;
    pointer-events: none;
  }
  .lens-off { opacity: 0; }

  .tab {
    position: relative;
    display: flex;
    min-height: 3.5rem;
    width: 100%;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.125rem;
    border-radius: 9999px;
    padding-inline: 0.25rem;
    font-size: 0.6875rem;
    font-weight: 600;
    text-decoration: none;
    color: var(--muted);                                  /* posé ici : la règle globale `a { color: inherit }` passerait devant une classe d'utilitaire */
    transition: color 200ms;
  }
  .tab.on { color: var(--accent); }
  .tab svg { transition: transform 200ms cubic-bezier(0.22, 1, 0.36, 1); }
  .tab:active svg { transform: scale(0.88); }
  .tab:active, .tab.on:active { color: var(--fg); }
  .tab:focus-visible { outline: 2px solid var(--accent); outline-offset: -3px; }

  @media (prefers-reduced-motion: reduce) {
    .lens, .tab, .tab svg { transition: none; }
  }
</style>
