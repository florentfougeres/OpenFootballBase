<script lang="ts">
  import { app, route, href, t } from "../lib/app.svelte";
  import { theme, cycleTheme } from "../lib/theme.svelte";
  import { focusSearch, searchUi } from "../lib/searchui.svelte";
  import SearchBox from "./SearchBox.svelte";
  const other = $derived(app.lang === "fr" ? "en" : "fr");
  const switchHref = $derived(`#/${other}/${route.parts.map(encodeURIComponent).join("/")}`);
  const current = $derived(route.parts[0] ?? "home");
  const links = $derived([
    { key: "home", label: t("home"), to: href("") },
    { key: "clubs", label: t("clubs"), to: href("clubs") },
    { key: "players", label: t("players"), to: href("players") },
    { key: "competitions", label: t("allComps"), to: href("competitions") },
    { key: "ballon-dor", label: t("balloon"), to: href("ballon-dor") },
    { key: "coverage", label: t("coverage"), to: href("coverage") },
    { key: "about", label: t("about"), to: href("about") },
  ]);
  const main = $derived(links.slice(0, 4));
  const extra = $derived(links.slice(4));                 // Ballon d'Or (en ligne dès xl), Couverture, À propos
  let more = $state(false);
  const active = (k: string) => (k === "competitions" ? ["competitions", "competition"].includes(current) : k === "clubs" ? ["clubs", "club"].includes(current) : k === "players" ? ["players", "player"].includes(current) : k === "home" ? ["home", "country"].includes(current) : current === k);
  $effect(() => { route.parts; searchUi.bar = false; more = false; });
  // « / » (hors champ de saisie) ou ⌘K / Ctrl+K : va à la recherche.
  function onKey(e: KeyboardEvent) {
    const el = e.target as HTMLElement | null;
    const typing = /^(input|textarea|select)$/i.test(el?.tagName ?? "") || Boolean(el?.isContentEditable);
    if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey && !e.altKey)) { e.preventDefault(); focusSearch(); }
  }
</script>

<svelte:window onkeydown={onKey} />

<header class="sticky top-0 z-30 border-b border-line bg-bg/90 backdrop-blur">
  <div class="mx-auto flex max-w-6xl items-center gap-3 px-4 py-2">
    <a class="display flex shrink-0 items-center gap-2 text-xl font-extrabold tracking-tight no-underline sm:text-2xl" href={href("")}>
      <img class="size-9" src={import.meta.env.BASE_URL + "logo.svg"} alt="" width="36" height="36" />
      OpenFootballBase
    </a>
    <nav class="ml-4 hidden min-w-0 items-center gap-1 lg:flex 2xl:ml-8" aria-label="Navigation">
      {#each main as l}
        <a class="whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-semibold no-underline transition hover:bg-surface-2 {active(l.key) ? 'bg-surface-2 text-fg' : 'text-muted'}"
          href={l.to} aria-current={active(l.key) ? "page" : undefined}>{l.label}</a>
      {/each}
      <!-- Liens secondaires : en ligne sur grand écran, dans un menu « Plus » en dessous (la barre ne tient pas sur une largeur moyenne) -->
      {#each extra.slice(0, 1) as l}
        <a class="hidden whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-semibold no-underline transition hover:bg-surface-2 xl:inline-block {active(l.key) ? 'bg-surface-2 text-fg' : 'text-muted'}"
          href={l.to} aria-current={active(l.key) ? "page" : undefined}>{l.label}</a>
      {/each}
      <div class="relative">
        <button type="button" class="flex items-center gap-1 whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-semibold transition hover:bg-surface-2 {extra.slice(1).some((l) => active(l.key)) || more ? 'bg-surface-2 text-fg' : 'text-muted'}"
          aria-expanded={more} aria-haspopup="menu" onclick={() => (more = !more)}>{t("more")}
          <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg></button>
        {#if more}
          <button type="button" class="fixed inset-0 z-30 cursor-default" aria-label={t("close")} tabindex="-1" onclick={() => (more = false)}></button>
          <div class="absolute left-0 top-full z-40 mt-1.5 min-w-44 rounded-xl border border-line bg-surface p-1.5 shadow-2xl" role="menu">
            {#each extra as l, i}
              <a class="flex items-center rounded-lg px-3 py-2 text-sm font-semibold no-underline hover:bg-surface-2 {i === 0 ? 'xl:hidden' : ''} {active(l.key) ? 'bg-surface-2' : ''}" href={l.to} role="menuitem">{l.label}</a>
            {/each}
          </div>
        {/if}
      </div>
    </nav>
    <div class="ml-auto flex items-center gap-2">
      <!-- Recherche : un champ dans l'en-tête sur grand écran ; sur mobile, une icône qui déplie une barre sous l'en-tête. « / » et ⌘K y amènent aussi. -->
      <SearchBox variant="header" />
      <button class="btn-ghost min-h-11 min-w-11 justify-center !px-3 lg:hidden" type="button" onclick={() => (searchUi.bar = !searchUi.bar)} aria-expanded={searchUi.bar} aria-label={t("searchTrigger")}>
        <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg></button>
      <button class="btn-ghost hidden min-h-11 min-w-11 justify-center !px-3 sm:inline-flex" type="button" onclick={cycleTheme} title={t("theme")} aria-label={t("theme")}>
        <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          {#if theme.value === "dark"}<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z" />
          {:else if theme.value === "light"}<circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
          {:else}<rect x="3" y="4" width="18" height="12" rx="2" /><path d="M8 20h8M12 16v4" />{/if}
        </svg>
      </button>
      <a class="btn-ghost min-h-11 min-w-11 justify-center !px-3 uppercase" href={switchHref} hreflang={other} lang={other}>{other}</a>
    </div>
  </div>
  {#if searchUi.bar}
    <div class="border-t border-line px-4 py-2.5 lg:hidden"><SearchBox variant="bar" autofocus onclose={() => (searchUi.bar = false)} /></div>
  {/if}
</header>
