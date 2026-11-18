<script lang="ts">
  import { app, countryOf, enc, href, isArea, t, type Row } from "../lib/app.svelte";
  import { nationalTeam } from "../lib/format";
  import Flag from "../components/Flag.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { AREA, CONFS, confOf } from "../lib/confed";
  import { NATIONAL, NATIONAL_ORDER, PLACE, bareName, isNational, type NationalGroup } from "../lib/ofcomps";
  import Crumbs from "../components/Crumbs.svelte";
  import CompetitionCard from "../components/CompetitionCard.svelte";
  import Icon, { type IconName } from "../components/Icon.svelte";
  import Spinner from "../components/Spinner.svelte";
  import ErrorBox from "../components/ErrorBox.svelte";

  // Deux vues : les compétitions de CLUBS (par confédération, puis le monde) et celles des ÉQUIPES NATIONALES.
  let view = $state<"clubs" | "national">("clubs");

  const latest = resource(async () => Object.fromEntries((await q(`SELECT cs.competition, cs.season, count(*) AS clubs FROM club_season cs
      JOIN (SELECT competition, max(season) AS season FROM club_season GROUP BY competition) m
        ON m.competition = cs.competition AND m.season = cs.season GROUP BY cs.competition, cs.season`)).map((r) => [r.competition, r])));

  // Compétitions de la source de matchs que nous n'avons pas comme championnat (« OF:* ») : sélections, Sudamericana, championnats du dépôt `world`.
  const of = resource(async () => {
    if (!app.has.match) return [] as Row[];
    const named = app.has.match_competition;
    return await q(`SELECT m.competition AS code, count(*) AS n, min(m.season) AS first, max(m.season) AS last${named ? ", any_value(c.name) AS name, any_value(c.logo_url) AS logo" : ""}
                    FROM match m ${named ? "LEFT JOIN match_competition c ON c.code = m.competition" : ""} WHERE m.competition LIKE 'OF:%' GROUP BY 1`);
  });
  const label = (c: Row) => NATIONAL[c.code as string]?.[app.lang] ?? bareName((c.name as string | undefined) ?? (c.code as string).slice(3));
  /** Pays d'une compétition « OF:* » : nom localisé et drapeau. */
  const placeOf = (c: Row) => { const k = PLACE[c.code as string]?.country; return k ? nationalTeam(k) : null; };
  const others = $derived((of.data ?? []).filter((c) => !isNational(c.code as string) && !PLACE[c.code as string]).sort((a, b) => label(a).localeCompare(label(b), app.lang)));
  const nationalGroups = $derived((["finals", "qualifying", "friendly"] as NationalGroup[]).map((g) => ({
    g, icon: (g === "finals" ? "trophy" : g === "qualifying" ? "target" : "ball") as IconName,
    items: NATIONAL_ORDER.filter((k) => NATIONAL[k].group === g).map((k) => (of.data ?? []).find((c) => c.code === k)).filter((c): c is Row => !!c),
  })).filter((x) => x.items.length));
  const nationalN = $derived(nationalGroups.reduce((s, g) => s + g.items.length, 0));

  type Item = { kind: "ours"; key: string; area: boolean; country: string; level: number; x: any; countryCode: string }
    | { kind: "of"; key: string; area: boolean; country: string; level: number; row: Row };

  // Confédération -> pays (les coupes d'Europe, pays « Europe », d'abord) -> championnats.
  const confs = $derived.by(() => {
    const byCountry = new Map<string, any[]>();
    for (const c of app.comps.values()) byCountry.set(c.country_code, [...(byCountry.get(c.country_code) ?? []), c]);
    const countries = [...byCountry.entries()].map(([code, comps]) => ({ ...countryOf(code), code, conf: confOf(code),
      comps: comps.sort((a, b) => a.level - b.level || a.code.localeCompare(b.code)) }));
    return CONFS.map((conf) => {
      // Une seule grille par confédération : nos compétitions (avec effectifs) et celles que la source de matchs ajoute (résultats seulement), triées
      // par zone (coupes continentales d'abord), pays, division.
      const items: Item[] = countries.filter((c) => c.conf === conf).flatMap((g) => g.comps.map((x: any): Item =>
        ({ kind: "ours", key: x.code, area: isArea(g.code), country: g.name, level: x.level, x, countryCode: g.code })));
      for (const c of of.data ?? []) {
        const pl = PLACE[c.code as string];
        if (pl?.conf !== conf) continue;
        const nt = placeOf(c);
        items.push({ kind: "of", key: c.code as string, area: !pl.country, country: nt?.name ?? "", level: pl.level, row: c });
      }
      items.sort((a, b) => Number(b.area) - Number(a.area) || a.country.localeCompare(b.country, app.lang) || a.level - b.level || a.key.localeCompare(b.key));
      return { conf, area: AREA[conf][app.lang], items, n: items.length };
    }).filter((c) => c.items.length);
  });
  const shown = (conf: string, area: string) => (conf === "WORLD" ? area : conf);

  const jump = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
</script>

{#snippet ofCard(c: Row)}
  <a class="tile group" href={href("competition", enc(c.code as string))}>
    {#if c.logo}
      <span class="block size-12 shrink-0 overflow-hidden rounded-lg bg-white p-1.5"><img class="size-full object-contain" src={c.logo as string} alt="" loading="lazy" /></span>
    {:else if placeOf(c)}
      <span class="grid size-12 shrink-0 place-items-center rounded-lg bg-surface-2"><Flag code={placeOf(c)?.flag} label={placeOf(c)?.name} size={28} /></span>
    {:else}
      <span class="grid size-12 shrink-0 place-items-center rounded-lg bg-surface-2 text-accent"><Icon name={NATIONAL[c.code as string]?.icon ?? "list"} size={26} /></span>
    {/if}
    <span class="min-w-0">
      <span class="block truncate font-semibold">{label(c)}</span>
      <span class="block truncate text-xs text-muted">{[placeOf(c)?.name, `${c.first}${c.first !== c.last ? ` – ${c.last}` : ""}`, `${(c.n as number).toLocaleString(app.lang)} ${t("matchesN")}`].filter(Boolean).join(" · ")}</span>
    </span>
  </a>
{/snippet}

<Crumbs trail={[{ label: t("allComps"), to: href("competitions") }]} />
<h1 class="text-4xl font-extrabold leading-none tracking-tight sm:text-5xl">{t("allComps")}</h1>
<p class="mt-2 max-w-2xl text-muted">{t("allCompsLead")}</p>

<div class="mt-6 inline-flex rounded-lg border border-line bg-surface p-0.5" role="tablist" aria-label={t("compKinds")}>
  {#each [["clubs", "shield", "compClubs"], ["national", "flag", "compNational"]] as [v, icon, key]}
    <button type="button" role="tab" aria-selected={view === v} class="flex items-center gap-2 rounded-md px-4 py-1.5 text-sm font-semibold transition {view === v ? 'bg-accent text-accent-fg' : 'text-muted hover:text-fg'}"
      onclick={() => (view = v as typeof view)}><Icon name={icon as IconName} size={16} />{t(key)}</button>
  {/each}
</div>

{#if latest.error}
  <div class="mt-6"><ErrorBox message={latest.error} /></div>
{:else if latest.loading && !latest.data}
  <Spinner />
{:else if view === "clubs"}
  <nav class="mt-5 flex flex-wrap gap-2" aria-label={t("compClubs")}>
    {#each confs as c (c.conf)}
      <button type="button" class="flex items-center gap-1.5 rounded-full border border-line bg-surface px-4 py-1.5 text-sm font-semibold transition hover:bg-surface-2" onclick={() => jump(`conf-${c.conf}`)}>
        {#if c.conf === "WORLD"}<Icon name="globe" size={15} />{/if}{shown(c.conf, c.area)} <span class="font-normal text-muted">· {c.n}</span>
      </button>
    {/each}
    {#if others.length}
      <button type="button" class="flex items-center gap-1.5 rounded-full border border-line bg-surface px-4 py-1.5 text-sm font-semibold transition hover:bg-surface-2" onclick={() => jump("conf-OTHERS")}>
        <Icon name="list" size={15} />{t("compOthers")} <span class="font-normal text-muted">· {others.length}</span>
      </button>
    {/if}
  </nav>

  {#each confs as c (c.conf)}
    <section class="mt-10 scroll-mt-20" id="conf-{c.conf}" aria-labelledby="h-{c.conf}">
      <h2 id="h-{c.conf}" class="mb-4 flex flex-wrap items-baseline gap-x-3 border-b border-line pb-2">
        <span class="display flex items-center gap-2 text-3xl font-extrabold tracking-tight">{#if c.conf === "WORLD"}<Icon name="globe" size={26} />{/if}{shown(c.conf, c.area)}</span>
        {#if c.conf !== "WORLD"}<span class="text-base text-muted">{c.area}</span>{/if}
      </h2>
      <!-- Une carte par championnat, toutes de même taille et alignées en lignes : le pays est dans le sous-titre, les divisions d'un même pays se suivent. -->
      <ul class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 min-[1536px]:grid-cols-5">
        {#each c.items as it (it.key)}
          <li>
            {#if it.kind === "ours"}
              <CompetitionCard code={it.x.code} countryCode={it.countryCode} logo={it.x.logo_url} clubs={latest.data?.[it.x.code]?.clubs} season={latest.data?.[it.x.code]?.season} />
            {:else}
              {@render ofCard(it.row)}
            {/if}
          </li>
        {/each}
      </ul>
    </section>
  {/each}

  {#if others.length}
    <section class="mt-10 scroll-mt-20" id="conf-OTHERS" aria-labelledby="h-OTHERS">
      <h2 id="h-OTHERS" class="mb-1 flex items-center gap-2 border-b border-line pb-2 text-3xl font-extrabold tracking-tight"><Icon name="list" size={26} /><span class="display">{t("compOthers")}</span></h2>
      <p class="mb-4 mt-2 text-sm text-muted">{t("compOthersLead")}</p>
      <ul class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 min-[1536px]:grid-cols-5">
        {#each others as c (c.code)}<li>{@render ofCard(c)}</li>{/each}
      </ul>
    </section>
  {/if}
{:else}
  <p class="mt-5 max-w-3xl text-sm text-muted">{t("compNationalLead")}</p>
  {#if of.loading && !of.data}
    <Spinner />
  {:else if !nationalN}
    <p class="mt-6 text-muted">{t("resNone")}</p>
  {:else}
    {#each nationalGroups as grp (grp.g)}
      <section class="mt-10" aria-labelledby="n-{grp.g}">
        <h2 id="n-{grp.g}" class="mb-4 flex items-center gap-2 border-b border-line pb-2 text-3xl font-extrabold tracking-tight"><Icon name={grp.icon} size={26} /><span class="display">{t("nat_" + grp.g)}</span></h2>
        <ul class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 min-[1536px]:grid-cols-5">
          {#each grp.items as c (c.code)}<li>{@render ofCard(c)}</li>{/each}
        </ul>
      </section>
    {/each}
  {/if}
{/if}
