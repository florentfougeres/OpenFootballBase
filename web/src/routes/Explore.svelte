<script lang="ts">
  import { app, areaFlag, countryOf, href, route, t } from "../lib/app.svelte";
  import Clubs from "./Clubs.svelte";
  import Players from "./Players.svelte";
  import Flag from "../components/Flag.svelte";
  import Segmented from "../components/Segmented.svelte";

  // « Explorer » : l'entrée unique pour parcourir les clubs, les joueurs et les pays. La vue est dans l'adresse (`?v=`).
  type V = "clubs" | "players" | "countries";
  const view = $derived<V>((["clubs", "players", "countries"] as const).find((v) => v === route.query.get("v")) ?? "clubs");
  const go = (v: V) => { location.hash = `#/${route.lang}/explore${v === "clubs" ? "" : `?v=${v}`}`; };

  const countries = $derived.by(() => {
    const comps = [...app.comps.values()], clubs = [...app.clubs.values()];
    return [...app.countries.values()].map((c) => ({ ...countryOf(c.code as string), code: c.code as string,
      clubs: clubs.filter((x) => x.country_code === c.code).length, comps: comps.filter((x) => x.country_code === c.code).length }))
      .filter((c) => c.clubs || c.comps).sort((a, b) => b.clubs - a.clubs || a.name.localeCompare(b.name, app.lang));
  });
</script>

<h1 class="text-4xl font-extrabold leading-none tracking-tight sm:text-5xl">{t("explore")}</h1>
<Segmented class="mt-5" tabs={false} label={t("exploreViews")} idPrefix="xp" value={view} onselect={go}
  items={[{ key: "clubs", label: t("clubs") }, { key: "players", label: t("players") }, { key: "countries", label: t("countries") }]} />

<div class="mt-2">
  {#if view === "clubs"}
    <Clubs embedded />
  {:else if view === "players"}
    <Players embedded />
  {:else}
    <ul class="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {#each countries as c (c.code)}
        <li><a class="tile" href={href("country", c.code)}>
          <Flag code={areaFlag(c.code) ?? c.flag} label={c.name} size={26} />
          <span class="min-w-0 flex-1"><span class="block truncate font-semibold">{c.name}</span><span class="text-xs text-muted">{c.clubs} {t("clubs").toLowerCase()}</span></span>
        </a></li>
      {/each}
    </ul>
  {/if}
</div>
