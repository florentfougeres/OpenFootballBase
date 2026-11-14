<script lang="ts">
  import { app, href, enc, t } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { compName } from "../lib/format";
  import Trophy from "./Trophy.svelte";

  // Palmarès d'un joueur : le Ballon d'Or (classements publiés) et les titres remportés avec un club dont il figure dans l'effectif listé la saison du titre.
  // C'est une approximation (il a pu partir en cours de saison ou peu jouer) : dite comme telle, jamais présentée comme un fait établi.
  let { pkey, qid }: { pkey: string; qid: string | null } = $props();

  type Title = { competition: string; years: number[]; clubs: string[] };
  const data = resource(async () => {
    const titles: Title[] = [];
    if (app.has.winner) {
      const rows = await q(`SELECT w.competition, w.season_start, s.club FROM squad s
          JOIN winner w ON w.club = s.club AND w.season_start = CAST(left(s.season, 4) AS INTEGER)
          WHERE COALESCE(s.player_qid, 'name:' || s.player) = ? AND COALESCE(s.stint, '') NOT IN ('loan_out', 'left_mid')
          GROUP BY ALL ORDER BY w.competition, w.season_start DESC`, [pkey]);
      const by = new Map<string, Title>();
      for (const r of rows) {
        const g = by.get(r.competition) ?? { competition: r.competition as string, years: [], clubs: [] };
        if (!g.years.includes(r.season_start)) g.years.push(r.season_start as number);
        if (!g.clubs.includes(r.club)) g.clubs.push(r.club as string);
        by.set(r.competition, g);
      }
      titles.push(...by.values());
    }
    const awards = qid && app.has.award ? await q(`SELECT year, rank, club_name, points FROM award WHERE player_qid = ? ORDER BY year`, [qid]) : [];
    return { titles, awards };
  });
  // Compétitions continentales d'abord, puis par niveau, puis par nombre de titres.
  const sorted = $derived.by(() => {
    const lvl = (c: string) => (app.comps.get(c)?.country_code === "EUR" || !app.comps.get(c)?.country_code ? 0 : 1);
    return [...(data.data?.titles ?? [])].sort((a, b) => lvl(a.competition) - lvl(b.competition) || (app.comps.get(a.competition)?.level ?? 9) - (app.comps.get(b.competition)?.level ?? 9) || b.years.length - a.years.length);
  });
  const total = $derived(sorted.reduce((n, g) => n + g.years.length, 0));
  const wins = $derived((data.data?.awards ?? []).filter((a) => a.rank === 1));
  const podium = $derived((data.data?.awards ?? []).filter((a) => a.rank === 2 || a.rank === 3));
  const ord = (n: number) => (app.lang === "fr" ? `${n}e` : n === 2 ? "2nd" : "3rd");
  const season = (y: number) => `${y}/${String(y + 1).slice(2)}`;
</script>

{#if data.data && (total || data.data.awards.length)}
  <section class="card mt-6 overflow-hidden" aria-labelledby="player-honours">
    <div class="flex items-center gap-2 px-5 pt-4"><Trophy size={20} /><h2 id="player-honours" class="text-lg font-bold">{t("honours")}</h2></div>

    {#if data.data.awards.length}
      <div class="mx-5 mt-3 rounded-xl border border-line bg-accent-soft px-4 py-3">
        <div class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          {#if wins.length}<span class="display text-3xl font-extrabold leading-none tabular-nums text-accent">{wins.length}</span><a class="font-semibold no-underline hover:text-accent" href={href("ballon-dor")}>{t("balloon")}</a>{/if}
          {#if wins.length}<span class="text-sm tabular-nums text-muted">{wins.map((a) => a.year).join(" · ")}</span>{/if}
        </div>
        {#if podium.length}
          <p class="mt-1.5 text-sm text-muted">{t("podium")} : {podium.map((a) => `${a.year} (${ord(a.rank)})`).join(" · ")}</p>
        {/if}
        {#if !wins.length && !podium.length}<p class="text-sm text-muted">{t("balloonRanked")} : {data.data.awards.map((a) => `${a.year} (${a.rank})`).join(" · ")}</p>{/if}
      </div>
    {/if}

    {#if total}
      <div class="mt-4 px-5">
        <div class="flex items-baseline gap-2"><span class="display text-3xl font-extrabold leading-none tabular-nums">{total}</span><span class="font-semibold">{total > 1 ? t("titlesN") : t("titleN")}</span></div>
      </div>
      <ul class="mt-2 divide-y divide-line/60 px-5">
        {#each sorted as g (g.competition)}
          <li class="py-2.5">
            <details class="group">
              <summary class="flex cursor-pointer list-none items-center gap-3 [&::-webkit-details-marker]:hidden">
                <span class="display w-8 text-2xl font-bold tabular-nums">{g.years.length}</span>
                <span class="min-w-0 flex-1">
                  <a class="block truncate font-semibold no-underline hover:text-accent" href={href("competition", g.competition)}>{compName(g.competition)}</a>
                  <span class="block truncate text-xs tabular-nums text-muted">{g.years.slice(0, 4).map(season).join(" · ")}{g.years.length > 4 ? " …" : ""}</span>
                </span>
                {#if g.years.length > 4}<span class="text-muted transition group-open:rotate-90" aria-hidden="true">›</span>{/if}
              </summary>
              {#if g.years.length > 4}<p class="mt-1.5 pl-11 text-sm leading-relaxed tabular-nums text-muted">{g.years.map(season).join(" · ")}</p>{/if}
            </details>
          </li>
        {/each}
      </ul>
      <p class="border-t border-line px-5 py-3 text-xs text-muted">{t("honoursPlayerNote")}</p>
    {/if}
  </section>
{/if}
