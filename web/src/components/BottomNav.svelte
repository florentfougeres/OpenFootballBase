<script lang="ts">
  import { route, href, t } from "../lib/app.svelte";
  import { searchUi } from "../lib/searchui.svelte";

  // Navigation principale sur mobile : une pilule flottante en bas, à portée du pouce, avec des libellés toujours visibles.
  // Cinq entrées : Accueil, Explorer, Recherche (bouton central, ouvre la recherche en plein écran), Compétitions, Suivis.
  // Une capsule glisse sous l'entrée active. Les pages secondaires (Ballon d'Or, couverture, à propos) et les réglages sont dans « Suivis ».
  const current = $derived(route.parts[0] ?? "home");
  const GROUPS: Record<string, string[]> = {
    home: ["home"],
    explore: ["explore", "clubs", "club", "players", "player", "country"],
    competitions: ["competitions", "competition"],
    follows: ["follows", "coverage", "about", "ballon-dor"],
  };
  const isActive = (k: string) => GROUPS[k]?.includes(current) ?? false;
  const KEYS = ["home", "explore", "search", "competitions", "follows"];
  // Colonne de la capsule : la recherche tant que la surcouche est ouverte ; aucune sur une page sans entrée (404).
  const lens = $derived(searchUi.bar ? 2 : KEYS.findIndex((k) => isActive(k)));
  const items = $derived([
    { key: "home", label: t("home"), to: href("") },
    { key: "explore", label: t("explore"), to: href("explore") },
    { key: "competitions", label: t("compsShort"), full: t("allComps"), to: href("competitions") },
    { key: "follows", label: t("follows"), to: href("follows") },
  ]);
  const ICON: Record<string, string> = {
    home: "M3.5 11 12 4l8.5 7M6 9.5V20h12V9.5M10 20v-5h4v5",
    explore: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM15.5 8.5l-2 5-5 2 2-5z",
    competitions: "M8 4h8v5a4 4 0 0 1-8 0zM8 6H5.5a2 2 0 0 0 0 4H8M16 6h2.5a2 2 0 0 1 0 4H16M12 13v4M8.5 20h7M10 17h4",
    follows: "M6.5 3.5h11v17L12 16.8l-5.5 3.7z",
  };
</script>

<!-- Dock : une bande pleine en bas de l'écran (rien de la page ne passe derrière) ; la pilule y est posée. -->
<div class="fixed inset-x-0 bottom-0 z-50 border-t border-line bg-bg px-3 pb-[calc(env(safe-area-inset-bottom)+0.5rem)] pt-2 lg:hidden">
  <nav class="pill mx-auto max-w-md rounded-full" aria-label={t("navMain")}>
    <ul class="tabs relative grid grid-cols-5 p-1" style="--i: {Math.max(lens, 0)}">
      <li class="lens" class:lens-off={lens < 0 || lens === 2} aria-hidden="true"></li>
      {#each items.slice(0, 2) as it (it.key)}
        <li class="relative">
          <a class="tab" class:on={isActive(it.key) && !searchUi.bar} href={it.to} aria-current={isActive(it.key) ? "page" : undefined}>
            <svg viewBox="0 0 24 24" class="size-[22px]" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d={ICON[it.key]} /></svg>
            <span class="truncate">{it.label}</span>
          </a>
        </li>
      {/each}
      <li class="relative">
        <button type="button" class="tab search" aria-label={t("searchTrigger")} aria-haspopup="dialog" aria-expanded={searchUi.bar} onclick={() => (searchUi.bar = true)}>
          <span class="puck"><svg viewBox="0 0 24 24" class="size-6" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m20 20-4-4" /></svg></span>
        </button>
      </li>
      {#each items.slice(2) as it (it.key)}
        <li class="relative">
          <a class="tab" class:on={isActive(it.key) && !searchUi.bar} href={it.to} aria-current={isActive(it.key) ? "page" : undefined} aria-label={it.full ?? it.label}>
            <svg viewBox="0 0 24 24" class="size-[22px]" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d={ICON[it.key]} /></svg>
            <span class="truncate">{it.label}</span>
          </a>
        </li>
      {/each}
    </ul>
  </nav>
</div>

<style>
  .pill {
    background: var(--surface);
    border: 1px solid color-mix(in oklab, var(--fg) 14%, transparent);
    box-shadow: inset 0 1px 0 color-mix(in oklab, white 14%, transparent), 0 8px 20px -8px rgb(0 0 0 / 0.45), 0 1px 4px rgb(0 0 0 / 0.16);
  }
  /* Capsule de sélection : un seul élément qui glisse sous l'entrée active (5 colonnes égales). */
  .lens {
    position: absolute; inset-block: 0.25rem; inset-inline-start: 0.25rem; width: calc((100% - 0.5rem) / 5);
    border-radius: 9999px; background: color-mix(in oklab, var(--accent) 17%, transparent);
    box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--accent) 28%, transparent), inset 0 1px 0 color-mix(in oklab, white 16%, transparent);
    transform: translateX(calc(var(--i) * 100%)); transition: transform 420ms cubic-bezier(0.22, 1, 0.36, 1), opacity 200ms; pointer-events: none;
  }
  .lens-off { opacity: 0; }
  .tab {
    position: relative; display: flex; min-height: 3.5rem; width: 100%; flex-direction: column; align-items: center; justify-content: center; gap: 0.125rem;
    border-radius: 9999px; padding-inline: 0.25rem; font-size: 0.6875rem; font-weight: 600; text-decoration: none;
    color: var(--muted);                                  /* posé ici : la règle globale `a { color: inherit }` passerait devant une classe d'utilitaire */
    transition: color 200ms;
  }
  .tab.on { color: var(--accent); }
  .tab svg { transition: transform 200ms cubic-bezier(0.22, 1, 0.36, 1); }
  .tab:active svg { transform: scale(0.88); }
  .tab:focus-visible { outline: 2px solid var(--accent); outline-offset: -3px; }
  /* Recherche : un bouton rond qui dépasse un peu de la pilule, l'action principale de l'app. */
  .puck {
    display: grid; place-items: center; width: 3.25rem; height: 3.25rem; margin-top: -1rem; border-radius: 9999px;
    background: var(--accent); color: var(--accent-fg); box-shadow: 0 4px 10px rgb(0 0 0 / 0.28); transition: transform 200ms cubic-bezier(0.22, 1, 0.36, 1);
  }
  .search:active .puck { transform: scale(0.93); }
  @media (prefers-reduced-motion: reduce) { .lens, .tab, .tab svg, .puck { transition: none; } }
</style>
