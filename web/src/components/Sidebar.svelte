<script lang="ts">
  import { app, route, href } from "../lib/app.svelte";
  import { t } from "../lib/app.svelte";
  import { theme, cycleTheme } from "../lib/theme.svelte";
  import { searchUi } from "../lib/searchui.svelte";
  import { follows } from "../lib/follow.svelte";

  // Navigation de bureau (à partir de 1024 px) : une barre latérale fixe à gauche, à la place de la barre du haut.
  const other = $derived(app.lang === "fr" ? "en" : "fr");
  const switchHref = $derived(`#/${other}/${route.parts.map(encodeURIComponent).join("/")}`);
  const current = $derived(route.parts[0] ?? "home");
  const GROUPS: Record<string, string[]> = {
    home: ["home"], explore: ["explore", "clubs", "club", "players", "player", "country"], competitions: ["competitions", "competition", "ballon-dor"],
    follows: ["follows"], lineup: ["lineup"], coverage: ["coverage"], about: ["about"],
  };
  const on = (k: string) => GROUPS[k]?.includes(current) ?? false;
  const main = $derived([
    { k: "home", label: t("home"), to: href(""), d: "M3.5 11 12 4l8.5 7M6 9.5V20h12V9.5M10 20v-5h4v5" },
    { k: "explore", label: t("explore"), to: href("explore"), d: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM15.5 8.5l-2 5-5 2 2-5z" },
    { k: "competitions", label: t("allComps"), to: href("competitions"), d: "M8 4h8v5a4 4 0 0 1-8 0zM8 6H5.5a2 2 0 0 0 0 4H8M16 6h2.5a2 2 0 0 1 0 4H16M12 13v4M8.5 20h7M10 17h4" },
    { k: "lineup", label: t("lineupTitle"), to: href("lineup"), d: "M4 4h16v16H4zM4 12h16M12 4v16" },
    { k: "follows", label: t("follows"), to: href("follows"), d: "M6.5 3.5h11v17L12 16.8l-5.5 3.7z" },
  ]);
  const more = $derived([
    { k: "coverage", label: t("coverage"), to: href("coverage") }, { k: "about", label: t("about"), to: href("about") },
  ]);
  const KIND = { club: "M12 3 5 5.5V11c0 4.2 2.8 7.4 7 9 4.2-1.6 7-4.8 7-9V5.5z", player: "M12 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM5 20c.7-3.6 3.3-5.5 7-5.5s6.3 1.9 7 5.5", comp: "M8 4h8v5a4 4 0 0 1-8 0zM12 13v4M8.5 20h7" } as const;
  const link = "flex min-h-11 items-center gap-3 rounded-xl px-3 text-[0.95rem] font-semibold no-underline transition";
</script>

<aside class="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col gap-1 overflow-y-auto border-r border-line bg-surface px-3 py-4 lg:flex" aria-label={t("navMain")}>
  <a class="display mb-2 flex items-center gap-2.5 px-2 text-2xl font-extrabold tracking-tight no-underline" href={href("")}>
    <img class="size-9" src={import.meta.env.BASE_URL + "logo.svg"} alt="" width="36" height="36" />OpenFootballBase
  </a>
  <button type="button" class="mb-2 flex h-11 items-center gap-2.5 rounded-xl bg-surface-2 px-3 text-sm text-muted transition hover:text-fg" aria-haspopup="dialog" onclick={() => (searchUi.bar = true)}>
    <svg viewBox="0 0 24 24" class="size-[18px]" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
    {t("searchTrigger")}<kbd class="ml-auto rounded border border-line px-1.5 text-xs font-semibold" aria-hidden="true">/</kbd>
  </button>

  <nav class="flex flex-col gap-0.5" aria-label={t("navMain")}>
    {#each main as l (l.k)}
      <a class="{link} {on(l.k) ? 'bg-accent-soft text-accent' : 'text-muted hover:bg-surface-2 hover:text-fg'}" href={l.to} aria-current={on(l.k) ? "page" : undefined}>
        <svg viewBox="0 0 24 24" class="size-5 shrink-0" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d={l.d} /></svg>{l.label}
      </a>
    {/each}
  </nav>

  <h2 class="mt-5 px-3 text-xs font-semibold uppercase tracking-wide text-muted">{t("sideFollows")}</h2>
  <ul class="flex flex-col gap-0.5">
    {#each follows.items.slice(0, 8) as f (f.kind + f.id)}
      <li><a class="{link} !min-h-10 font-medium text-muted hover:bg-surface-2 hover:text-fg" href={`#/${app.lang}/${f.path}`}>
        <svg viewBox="0 0 24 24" class="size-[18px] shrink-0" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d={KIND[f.kind]} /></svg><span class="truncate">{f.label}</span></a></li>
    {:else}
      <li class="px-3 py-1 text-sm text-muted">{t("followsNone")}</li>
    {/each}
  </ul>

  <div class="mt-auto flex flex-col gap-0.5 pt-4">
    {#each more as l (l.k)}
      <a class="{link} !min-h-10 font-medium {on(l.k) ? 'bg-accent-soft text-accent' : 'text-muted hover:bg-surface-2 hover:text-fg'}" href={l.to} aria-current={on(l.k) ? "page" : undefined}>{l.label}</a>
    {/each}
    <div class="mt-2 flex gap-2 border-t border-line pt-3">
      <button type="button" class="btn-ghost min-h-11 flex-1 justify-center" onclick={cycleTheme} title={t("theme")} aria-label={t("theme")}>
        <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          {#if theme.value === "dark"}<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z" />
          {:else if theme.value === "light"}<circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
          {:else}<rect x="3" y="4" width="18" height="12" rx="2" /><path d="M8 20h8M12 16v4" />{/if}
        </svg>
      </button>
      <a class="btn-ghost min-h-11 flex-1 justify-center uppercase" href={switchHref} hreflang={other} lang={other}>{other}</a>
    </div>
  </div>
</aside>
