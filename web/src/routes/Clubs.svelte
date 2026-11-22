<script lang="ts">
  let { embedded = false }: { embedded?: boolean } = $props();       // dans la page Explorer : sans fil d'Ariane ni grand titre
  import { app, countryOf, href, enc, t } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { clubName } from "../lib/format";
  import Crumbs from "../components/Crumbs.svelte";
  import Flag from "../components/Flag.svelte";
  import Logo from "../components/Logo.svelte";
  import Spinner from "../components/Spinner.svelte";

  let term = $state("");
  let country = $state("");

  const counts = resource(async () => Object.fromEntries((await q(`SELECT club, count(*) AS n FROM club_season GROUP BY club`)).map((r) => [r.club, Number(r.n)])));
  const flat = (s: string) => s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();

  const all = $derived([...app.clubs.values()].map((c) => ({ c, name: clubName(c), key: flat(clubName(c)) }))
    .sort((a, b) => a.name.localeCompare(b.name, app.lang)));
  const countries = $derived([...new Set(all.map((x) => x.c.country_code as string))].map((code) => countryOf(code))
    .sort((a, b) => a.name.localeCompare(b.name, app.lang)));
  const filtered = $derived.by(() => {
    const f = flat(term.trim());
    return all.filter((x) => (!country || x.c.country_code === country) && (!f || x.key.includes(f)));
  });
  /** Clubs groupés par pays (ordre alphabétique de la langue), clubs par nom dans chaque pays. */
  const groups = $derived.by(() => {
    const by = new Map<string, typeof filtered>();
    for (const x of filtered) by.set(x.c.country_code, [...(by.get(x.c.country_code) ?? []), x]);
    return [...by.entries()].map(([code, items]) => ({ ...countryOf(code), code, items }))
      .sort((a, b) => a.name.localeCompare(b.name, app.lang));
  });
</script>

{#if !embedded}
<Crumbs trail={[{ label: t("clubs"), to: href("clubs") }]} />
<h1 class="text-4xl font-extrabold leading-none tracking-tight sm:text-5xl">{t("allClubs")}</h1>
<p class="mt-2 max-w-2xl text-muted">{t("allClubsLead")}</p>
{/if}

<div class="mt-6 flex flex-col gap-2 sm:flex-row">
  <input class="min-w-0 flex-1 rounded-lg border border-line bg-surface px-4 py-2.5 text-base outline-none placeholder:text-muted focus:border-accent focus:ring-2 focus:ring-accent/40"
    type="search" bind:value={term} placeholder={t("filterClubs")} aria-label={t("filterClubs")} autocomplete="off" />
  <select class="rounded-lg border border-line bg-surface px-3 py-2.5 text-base outline-none focus:border-accent focus:ring-2 focus:ring-accent/40" bind:value={country} aria-label={t("countries")}>
    <option value="">{t("allCountries")}</option>
    {#each countries as c (c.code)}<option value={c.code}>{c.name}</option>{/each}
  </select>
</div>
<p class="mt-3 text-sm text-muted" aria-live="polite"><span class="tabular-nums">{filtered.length}</span> {t("clubsFound")}</p>

{#if !all.length}
  <Spinner />
{:else if !filtered.length}
  <p class="mt-6 text-muted">{t("noClub")}</p>
{:else}
  {#each groups as g (g.code)}
    <section class="mt-6" aria-labelledby="g-{g.code}">
      <!-- En-tête de pays collant (esprit FotMob) : on sait toujours dans quel pays on défile. -->
      <h2 id="g-{g.code}" class="sticky top-[calc(3.5rem+env(safe-area-inset-top))] z-10 -mx-4 flex items-center gap-2.5 bg-bg/95 px-4 py-2 text-xl font-bold backdrop-blur lg:top-0"><Flag code={g.flag} label={g.name} size={22} /> {g.name}
        <span class="display text-base font-semibold text-muted">{g.items.length}</span></h2>
      <div class="card mt-1 overflow-hidden">
        <ul class="-mb-px grid lg:grid-cols-2 lg:gap-x-px lg:bg-line/60">
          {#each g.items as x (x.c.wikipedia_title)}
            {@const n = counts.data?.[x.c.wikipedia_title]}
            <li class="border-b border-line/60 bg-surface lg:border-b-0 lg:[&:not(:nth-last-child(-n+2))]:border-b">
              <a class="row" href={href("club", enc(x.c.wikipedia_title))}>
                <Logo club={x.c} size={30} />
                <span class="min-w-0 flex-1 truncate font-semibold">{x.name}</span>
                {#if n}<span class="shrink-0 text-xs tabular-nums text-muted">{n} {t("seasonsOf")}</span>{/if}
                <span class="shrink-0 text-muted" aria-hidden="true">›</span>
              </a>
            </li>
          {/each}
        </ul>
      </div>
    </section>
  {/each}
{/if}
