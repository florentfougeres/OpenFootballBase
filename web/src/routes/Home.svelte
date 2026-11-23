<script lang="ts">
  import { app, areaFlag, enc, href, route, seasonSlug, t } from "../lib/app.svelte";
  import { clubName } from "../lib/format";
  import { follows } from "../lib/follow.svelte";
  import FollowAvatar from "../components/FollowAvatar.svelte";
  import { searchUi } from "../lib/searchui.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import Flag from "../components/Flag.svelte";
  import Logo from "../components/Logo.svelte";
  import SearchResults from "../components/SearchResults.svelte";
  import ErrorBox from "../components/ErrorBox.svelte";
  import Spinner from "../components/Spinner.svelte";

  // « Voir tous les résultats » de la palette arrive ici avec ?q=… : la page affiche alors la liste complète.
  const urlTerm = $derived(route.query.get("q")?.trim() ?? "");

  const nf = (n: number) => n.toLocaleString(app.lang);
  const seasonsN = $derived(Object.keys(app.manifest.seasons).length);

  type HomeData = { stats: { clubs: number; players: number }; countries: { code: string; name_en: string; name_fr: string; flag: string | null; comps: number; clubs: number }[];
    clubs: { wikipedia_title: string; name_en: string; name_fr: string | null; logo_url: string | null; colors_hex: string | null; season: string }[];
    competitions?: { code: string; name_en: string; name_fr: string; country_code: string; logo_url: string | null; flag: string | null }[] };

  // L'accueil s'affiche sans attendre DuckDB-WASM : un petit JSON (`home`) est publié avec les données. Anciens exports : requêtes DuckDB.
  const data = resource(async (): Promise<HomeData | null> => {
    const m = app.manifest;
    if (m.home) return await (await fetch(new URL(import.meta.env.BASE_URL + "data/" + m.home.path, location.href))).json();
    if (!app.ready) return null;
    const [stats] = await q(`SELECT (SELECT count(*) FROM club) AS clubs, (SELECT count(DISTINCT coalesce(player_qid, 'n:' || player)) FROM squad) AS players`);
    const comps = [...app.comps.values()];
    const squadClubs = [...app.clubs.values()].filter((x) => app.squadClubs.has(x.wikipedia_title as string));
    const countries = [...app.countries.values()].map((c) => ({
      code: c.code, name_en: c.name_en, name_fr: c.name_fr, flag: c.flag as string | null,
      comps: comps.filter((x) => x.country_code === c.code).length,
      clubs: squadClubs.filter((x) => x.country_code === c.code).length,
    })).filter((c) => c.comps || c.clubs);
    const last = Object.fromEntries((await q(`SELECT club, max(season) AS season FROM club_season WHERE players > 0 GROUP BY club`)).map((r) => [r.club, r.season as string]));
    const clubs = squadClubs.filter((c) => last[c.wikipedia_title]).sort((a, b) => (b.wikipedia_count ?? 0) - (a.wikipedia_count ?? 0)).slice(0, 12)
      .map((c) => ({ wikipedia_title: c.wikipedia_title, name_en: c.name_en, name_fr: c.name_fr, logo_url: c.logo_url, colors_hex: c.colors_hex, season: last[c.wikipedia_title] }));
    return { stats: { clubs: stats.clubs, players: stats.players }, countries, clubs };
  });
  // Compétitions à la une : liste publiée avec l'accueil ; un export plus ancien n'en a pas, on la compose dès que DuckDB est prêt.
  const FEATURED = ["ENG-PL", "UEFA-CL", "UEFA-EL", "DEU-BL", "ESP-LL", "ITA-SA", "FRA-L1", "USA-MLS"];
  const featuredComps = $derived.by(() => {
    if (data.data?.competitions?.length) return data.data.competitions;
    if (!app.ready) return [];
    return FEATURED.filter((c) => app.comps.has(c)).map((c) => {
      const x = app.comps.get(c)!;
      return { code: c, name_en: x.name_en as string, name_fr: x.name_fr as string, country_code: x.country_code as string, logo_url: (x.logo_url as string | null) ?? null,
               flag: areaFlag(x.country_code) ?? ((app.countries.get(x.country_code)?.flag as string | null) ?? null) };
    });
  });
  const countries = $derived((data.data?.countries ?? []).map((c) => ({ ...c, name: app.lang === "fr" ? c.name_fr : c.name_en }))
    .sort((a, b) => a.name.localeCompare(b.name, app.lang)));
  // 116 pays d'un coup font une liste interminable : les mieux couverts d'abord, le reste derrière un bouton.
  const TOP = 12;
  let showAll = $state(false);
  const topCountries = $derived([...countries].sort((a, b) => b.clubs - a.clubs).slice(0, TOP).sort((a, b) => a.name.localeCompare(b.name, app.lang)));
  const topCodes = $derived(new Set(topCountries.map((c) => c.code)));
  const otherCountries = $derived(countries.filter((c) => !topCodes.has(c.code)));
</script>

<div class="mx-auto max-w-6xl px-4 pb-6 pt-3 lg:pt-8">
  <h1 class="sr-only">{t("heroTitle")}</h1>
  <!-- Une entrée de recherche (ouvre la recherche) ; les chiffres de la base sont en bas de page. -->
  <button type="button" class="flex h-12 w-full items-center gap-3 rounded-2xl border border-line bg-surface px-4 text-left text-muted transition hover:border-accent lg:h-14 lg:max-w-2xl lg:text-lg" aria-haspopup="dialog" onclick={() => (searchUi.bar = true)}>
    <svg viewBox="0 0 24 24" class="size-5 shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
    <span class="truncate">{t("spPlaceholder")}</span>
    <kbd class="ml-auto hidden rounded border border-line px-1.5 text-xs font-semibold lg:inline" aria-hidden="true">/</kbd>
  </button>
  <p class="mt-3 max-w-2xl text-sm leading-snug text-muted">{t("heroLead")} <a class="link" href={href("about")}>{t("about")}</a></p>

  {#if urlTerm}
    <div class="mt-6 flex items-baseline justify-between gap-3">
      <h2 class="text-lg font-bold">{t("spAll").replace(/\s+pour$|\s+for$/, "")} « {urlTerm} »</h2>
      <a class="link text-sm" href={href("")}>{t("sqReset")}</a>
    </div>
    {#if app.ready}<SearchResults term={urlTerm} />{:else}<p class="mt-6 flex items-center gap-3 text-sm text-muted"><Spinner /> {t("searchWaiting")}</p>{/if}
  {/if}

  {#if data.error}
    <div class="mt-10"><ErrorBox message={data.error} /></div>
  {:else if data.loading && !data.data}
    <Spinner />
  {:else if data.data}
    {#if follows.items.length}
      <section class="mt-6" aria-labelledby="my-follows">
        <div class="flex items-baseline justify-between">
          <h2 id="my-follows" class="text-xl font-bold">{t("followsMine")}</h2>
          <a class="link inline-flex min-h-11 items-center text-sm" href={href("follows")}>{t("seeAll")} →</a>
        </div>
        <ul class="-mx-4 mt-1 flex snap-x gap-2.5 overflow-x-auto px-4 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden lg:mx-0 lg:grid lg:grid-cols-4 lg:overflow-visible lg:px-0">
          {#each follows.items.slice(0, 8) as f (f.kind + f.id)}
            <li class="snap-start max-lg:w-56 max-lg:shrink-0">
              <a class="flex h-full items-center gap-3 rounded-2xl border border-line bg-surface p-3 no-underline transition hover:border-accent active:scale-[0.98]" href={`#/${app.lang}/${f.path}`}>
                <FollowAvatar {f} size={40} />
                <span class="min-w-0"><span class="block truncate font-semibold leading-tight">{f.label}</span>{#if f.sub}<span class="block truncate text-xs text-muted">{f.sub}</span>{/if}</span>
              </a>
            </li>
          {/each}
        </ul>
      </section>
    {/if}

    {#if featuredComps.length}
      <section class="mt-7" aria-labelledby="feat-comps">
        <div class="flex items-baseline justify-between">
          <h2 id="feat-comps" class="text-xl font-bold">{t("featuredComps")}</h2>
          <a class="link inline-flex min-h-11 items-center text-sm" href={href("competitions")}>{t("allComps")} →</a>
        </div>
        <ul class="-mx-4 mt-1 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden lg:mx-0 lg:flex-wrap lg:px-0">
          {#each featuredComps as c (c.code)}
            <li class="shrink-0">
              <a class="flex h-11 items-center gap-2.5 rounded-full border border-line bg-surface pl-2 pr-4 text-sm font-semibold no-underline transition hover:border-accent hover:bg-surface-2" href={href("competition", c.code)}>
                {#if c.logo_url}<span class="block size-7 overflow-hidden rounded-full bg-white p-0.5"><img class="size-full object-contain" src={c.logo_url} alt="" loading="lazy" /></span>
                {:else}<span class="grid size-7 place-items-center rounded-full bg-surface-2"><Flag code={c.flag} size={16} /></span>{/if}
                {app.lang === "fr" ? c.name_fr : c.name_en}
              </a>
            </li>
          {/each}
        </ul>
      </section>
    {/if}

    <div class="mt-7 grid gap-x-8 gap-y-7 lg:grid-cols-2">
      <section aria-labelledby="feat-clubs">
        <div class="flex items-baseline justify-between">
          <h2 id="feat-clubs" class="text-xl font-bold">{t("featuredClubs")}</h2>
          <a class="link inline-flex min-h-11 items-center text-sm" href={href("explore")}>{t("allClubs")} →</a>
        </div>
        <ul class="card mt-1 divide-y divide-line/60 overflow-hidden">
          {#each data.data.clubs.slice(0, 8) as x (x.wikipedia_title)}
            <li>
              <a class="row" href={href("club", enc(x.wikipedia_title), seasonSlug(x.season))}>
                <Logo club={x} size={32} />
                <span class="min-w-0 flex-1 truncate font-semibold">{clubName(x)}</span>
                <span class="shrink-0 text-xs tabular-nums text-muted">{x.season}</span>
                <span class="shrink-0 text-muted" aria-hidden="true">›</span>
              </a>
            </li>
          {/each}
        </ul>
      </section>

      <section aria-labelledby="by-country">
        <div class="flex items-baseline justify-between">
          <h2 id="by-country" class="text-xl font-bold">{t("byCountry")}</h2>
          <a class="link inline-flex min-h-11 items-center text-sm" href={href("explore") + "?v=countries"}>{t("seeAll")} →</a>
        </div>
        <ul class="card mt-1 divide-y divide-line/60 overflow-hidden">
          {#each topCountries.slice(0, 8) as c (c.code)}
            <li>
              <a class="row" href={href("country", c.code)}>
                <Flag code={areaFlag(c.code) ?? c.flag} label={c.name} size={24} />
                <span class="min-w-0 flex-1 truncate font-semibold">{c.name}</span>
                <span class="shrink-0 text-xs tabular-nums text-muted">{c.clubs || ""}</span>
                <span class="shrink-0 text-muted" aria-hidden="true">›</span>
              </a>
            </li>
          {/each}
        </ul>
      </section>
    </div>

    <dl class="mt-8 flex flex-wrap gap-x-8 gap-y-3 border-t border-line pt-5 text-sm text-muted">
      {#each [[nf(data.data.stats.players), t("statPlayers")], [nf(data.data.stats.clubs), t("statClubs")], [seasonsN, t("statSeasons")], [countries.length, t("countries").toLowerCase()]] as [n, label]}
        <div class="flex items-baseline gap-1.5"><dd class="display text-xl font-bold tabular-nums text-fg">{n}</dd><dt>{label}</dt></div>
      {/each}
    </dl>
  {/if}
</div>
