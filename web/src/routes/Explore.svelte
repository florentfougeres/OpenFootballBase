<script lang="ts">
  import { app, areaFlag, countryOf, href, route, t } from "../lib/app.svelte";
  import Clubs from "./Clubs.svelte";
  import Players from "./Players.svelte";
  import Flag from "../components/Flag.svelte";
  import Segmented from "../components/Segmented.svelte";
  import WorldMap from "../components/WorldMap.svelte";

  // « Explorer » : l'entrée unique pour parcourir les clubs, les joueurs et les pays. La vue est dans l'adresse (`?v=`).
  type V = "clubs" | "players" | "countries";
  const view = $derived<V>((["clubs", "players", "countries"] as const).find((v) => v === route.query.get("v")) ?? "clubs");
  // Affichage : liste ou carte (clubs et pays seulement), lui aussi dans l'adresse (`?m=map`).
  const asMap = $derived(view !== "players" && route.query.get("m") === "map");
  const go = (v: V) => {
    const q = new URLSearchParams();
    if (v !== "clubs") q.set("v", v);
    if (v !== "players" && route.query.get("m") === "map") q.set("m", "map");
    location.hash = `#/${route.lang}/explore${q.size ? `?${q}` : ""}`;
  };
  const setMode = (m: "list" | "map") => {
    const q = new URLSearchParams(route.query);
    if (m === "map") q.set("m", "map"); else q.delete("m");
    location.hash = `#/${route.lang}/explore${q.size ? `?${q}` : ""}`;
  };

  const countries = $derived.by(() => {
    const comps = [...app.comps.values()], clubs = [...app.clubs.values()];
    return [...app.countries.values()].map((c) => ({ ...countryOf(c.code as string), code: c.code as string,
      clubs: clubs.filter((x) => x.country_code === c.code).length, comps: comps.filter((x) => x.country_code === c.code).length }))
      .filter((c) => c.clubs || c.comps).sort((a, b) => b.clubs - a.clubs || a.name.localeCompare(b.name, app.lang));
  });
</script>

<div class="flex items-center justify-between gap-3">
  <h1 class="text-4xl font-extrabold leading-none tracking-tight sm:text-5xl">{t("explore")}</h1>
  {#if view !== "players"}
    <Segmented class="shrink-0" tabs={false} label={t("displayMode")} idPrefix="xm" value={asMap ? "map" : "list"} onselect={setMode}
      items={[{ key: "list", label: t("listMode") }, { key: "map", label: t("mapMode") }]} />
  {/if}
</div>
<Segmented class="mt-5" tabs={false} label={t("exploreViews")} idPrefix="xp" value={view} onselect={go}
  items={[{ key: "clubs", label: t("clubs") }, { key: "players", label: t("players") }, { key: "countries", label: t("countries") }]} />


<div class="mt-2">
  {#if asMap && app.ready}
    {#key view}<WorldMap mode={view === "clubs" ? "clubs" : "countries"} />{/key}
  {:else if view === "clubs"}
    <Clubs embedded />
  {:else if view === "players"}
    <Players embedded />
  {:else}
    <div class="card mt-4 overflow-hidden">
      <ul class="-mb-px grid sm:grid-cols-2 sm:gap-x-px sm:bg-line/60 lg:grid-cols-3">
        {#each countries as c (c.code)}
          <li class="border-b border-line/60 bg-surface">
            <a class="row" href={href("country", c.code)}>
              <Flag code={areaFlag(c.code) ?? c.flag} label={c.name} size={24} />
              <span class="min-w-0 flex-1 truncate font-semibold">{c.name}</span>
              <span class="shrink-0 text-xs tabular-nums text-muted">{c.clubs}</span>
              <span class="shrink-0 text-muted" aria-hidden="true">›</span>
            </a>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>
