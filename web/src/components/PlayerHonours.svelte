<script lang="ts">
  import { app, href, enc, t } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { compKind, compName, nationalTeam, titleYear } from "../lib/format";
  import Flag from "./Flag.svelte";
  import Trophy from "./Trophy.svelte";
  import CompLogo from "./CompLogo.svelte";

  // Palmarès d'un joueur : le Ballon d'Or (classements publiés) et les titres remportés avec un club dont il figure dans l'effectif listé la saison du titre.
  // C'est une approximation (il a pu partir en cours de saison ou peu jouer) : dite comme telle, jamais présentée comme un fait établi.
  // `has` : vrai quand il y a quelque chose à afficher (la page joueur s'en sert pour n'afficher l'onglet Palmarès que s'il est utile).
  let { pkey, qid, has = $bindable(false) }: { pkey: string; qid: string | null; has?: boolean } = $props();

  type Title = { competition: string; years: number[]; clubs: string[] };
  const data = resource(async () => {
    // pkey et qid sont lus ICI, avant le premier await : seules les valeurs lues avant sont suivies. Lire qid plus loin laissait le Ballon d'Or du joueur précédent à l'écran.
    const key = pkey, id = qid;
    const titles: Title[] = [];
    if (app.has.winner) {
      const rows = await q(`SELECT w.competition, w.season_start, s.club FROM squad s
          JOIN winner w ON w.club = s.club AND w.season_start = CAST(left(s.season, 4) AS INTEGER)
          WHERE COALESCE(s.player_qid, 'name:' || s.player) = ? AND COALESCE(s.stint, '') NOT IN ('loan_out', 'left_mid')
          GROUP BY ALL ORDER BY w.competition, w.season_start DESC`, [key]);
      const by = new Map<string, Title>();
      for (const r of rows) {
        const g = by.get(r.competition) ?? { competition: r.competition as string, years: [], clubs: [] };
        if (!g.years.includes(r.season_start)) g.years.push(r.season_start as number);
        if (!g.clubs.includes(r.club)) g.clubs.push(r.club as string);
        by.set(r.competition, g);
      }
      titles.push(...by.values());
    }
    // Titres en équipe nationale : par QID, ou par nom quand le joueur n'a pas d'élément Wikidata.
    const national = app.has.national_title
      ? await q(`SELECT competition, year, team FROM national_title WHERE ${id ? "player_qid = ?" : "player_qid IS NULL AND player_name = ?"} ORDER BY year DESC`, [id ?? key.replace(/^name:/, "")])
      : [];
    const awards = id && app.has.award ? await q(`SELECT year, rank, club_name, points FROM award WHERE player_qid = ? ORDER BY year`, [id]) : [];
    return { titles, awards, national };
  });
  const NAT_ORDER = ["WORLD_CUP", "EURO", "COPA_AMERICA", "AFCON", "ASIAN_CUP", "GOLD_CUP", "CONFEDERATIONS_CUP"];
  const NAT_NAME: Record<string, [string, string]> = {
    WORLD_CUP: ["Coupe du monde", "World Cup"], EURO: ["Championnat d'Europe", "European Championship"], COPA_AMERICA: ["Copa América", "Copa América"],
    AFCON: ["Coupe d'Afrique des nations", "Africa Cup of Nations"], ASIAN_CUP: ["Coupe d'Asie des nations", "AFC Asian Cup"], GOLD_CUP: ["Gold Cup", "Gold Cup"],
    CONFEDERATIONS_CUP: ["Coupe des confédérations", "Confederations Cup"],
  };
  const nationalGroups = $derived.by(() => {
    const by = new Map<string, { code: string; rows: { year: number; team: string }[] }>();
    for (const r of data.data?.national ?? []) {
      const g = by.get(r.competition) ?? { code: r.competition as string, rows: [] };
      g.rows.push({ year: r.year as number, team: r.team as string });
      by.set(r.competition, g);
    }
    return [...by.values()].sort((a, b) => NAT_ORDER.indexOf(a.code) - NAT_ORDER.indexOf(b.code));
  });
  const nationalTotal = $derived(nationalGroups.reduce((n, g) => n + g.rows.length, 0));
  const natName = (c: string) => NAT_NAME[c]?.[app.lang === "fr" ? 0 : 1] ?? c;
  // Compétitions continentales d'abord, puis par niveau, puis par nombre de titres.
  const sorted = $derived.by(() => {
    const lvl = (c: string) => (app.comps.get(c)?.country_code === "EUR" || !app.comps.get(c)?.country_code ? 0 : 1);
    return [...(data.data?.titles ?? [])].sort((a, b) => lvl(a.competition) - lvl(b.competition) || (app.comps.get(a.competition)?.level ?? 9) - (app.comps.get(b.competition)?.level ?? 9) || b.years.length - a.years.length);
  });
  const total = $derived(sorted.reduce((n, g) => n + g.years.length, 0));
  const wins = $derived((data.data?.awards ?? []).filter((a) => a.rank === 1));
  const podium = $derived((data.data?.awards ?? []).filter((a) => a.rank === 2 || a.rank === 3));
  const winYears = $derived(wins.map((a) => a.year as number).sort((x, y) => y - x));
  const more = $derived(winYears.length > 4 || (wins.length > 0 && podium.length > 0));
  const KINDS = ["league", "cup", "intl"] as const;
  const ord = (n: number) => (app.lang === "fr" ? `${n}e` : n === 2 ? "2nd" : "3rd");
  const season = (y: number) => `${y}/${String(y + 1).slice(2)}`;
  const show = $derived(!!data.data && !data.loading && !!(total || nationalTotal || data.data.awards.length));
  $effect(() => { has = show; });
</script>

<!-- pas de palmarès d'un autre joueur pendant le chargement : la ressource garde l'ancien résultat tant que le nouveau n'est pas arrivé -->
{#if show && data.data}
  <section class="card mt-6 overflow-hidden" aria-labelledby="player-honours">
    <div class="flex items-center gap-2 px-5 pt-4"><Trophy size={20} /><h2 id="player-honours" class="text-lg font-bold">{t("honours")}</h2></div>

    {#if nationalTotal}
      <div class="mt-4 px-5">
        <div class="flex items-baseline gap-2"><span class="display text-3xl font-extrabold leading-none tabular-nums text-accent">{nationalTotal}</span><span class="font-semibold">{nationalTotal > 1 ? t("titlesN") : t("titleN")} {t("withNational")}</span></div>
      </div>
      <ul class="mt-2 divide-y divide-line/60 px-5">
        {#each nationalGroups as g (g.code)}
          <li class="flex items-center gap-3 py-2.5">
            <span class="display w-8 text-2xl font-bold tabular-nums">{g.rows.length}</span>
            <span class="min-w-0 flex-1">
              <span class="block truncate font-semibold">{natName(g.code)}</span>
              <span class="flex flex-wrap items-center gap-x-2 text-xs tabular-nums text-muted">
                {#each g.rows as r (r.year)}<span class="inline-flex items-center gap-1">{r.year}{#if nationalTeam(r.team).flag}<Flag code={nationalTeam(r.team).flag} label={r.team} size={13} />{/if}</span>{/each}
              </span>
            </span>
          </li>
        {/each}
      </ul>
    {/if}

    {#if data.data.awards.length}
      <h3 class="mt-4 px-5 text-xs font-semibold uppercase tracking-wide text-muted">{t("honoursIndividual")}</h3>
      <ul class="divide-y divide-line/60 px-5">
        <li class="py-2.5">
          <details class="group">
            <summary class="flex cursor-pointer list-none items-center gap-3 [&::-webkit-details-marker]:hidden">
              <span class="display w-8 text-2xl font-bold tabular-nums">{wins.length || ""}</span>
              <span class="grid size-8 shrink-0 place-items-center rounded-lg bg-surface-2 text-muted"><Trophy size={18} /></span>
              <span class="min-w-0 flex-1">
                <a class="block truncate font-semibold no-underline hover:text-accent" href={href("ballon-dor")}>{t("balloon")}</a>
                <span class="block truncate text-xs tabular-nums text-muted">{#if wins.length}{winYears.slice(0, 4).join(", ")}{winYears.length > 4 ? " …" : ""}{:else}{t("balloonRanked")} : {data.data.awards.map((a) => `${a.year} (${a.rank})`).join(", ")}{/if}</span>
              </span>
              {#if more}<span class="text-muted transition group-open:rotate-90" aria-hidden="true">›</span>{/if}
            </summary>
            {#if more}
              <p class="mt-1.5 pl-[4.75rem] text-sm leading-relaxed tabular-nums text-muted">
                {#if winYears.length > 4}<span class="block">{winYears.join(", ")}</span>{/if}
                {#if podium.length}<span class="block">{t("podium")} : {podium.map((a) => `${a.year} (${ord(a.rank)})`).join(", ")}</span>{/if}
              </p>
            {/if}
          </details>
        </li>
      </ul>
    {/if}

    {#if total}
      <div class="mt-4 px-5">
        <div class="flex items-baseline gap-2"><span class="display text-3xl font-extrabold leading-none tabular-nums">{total}</span><span class="font-semibold">{total > 1 ? t("titlesN") : t("titleN")} {t("withClubs")}</span></div>
      </div>
      {#each KINDS as kind (kind)}
        {@const rows = sorted.filter((g) => compKind(g.competition) === kind)}
        {#if rows.length}
          <h3 class="mt-3 flex items-baseline justify-between px-5 text-xs font-semibold uppercase tracking-wide text-muted"><span>{t("kind_" + kind)}</span><span class="tabular-nums">{rows.reduce((n, g) => n + g.years.length, 0)}</span></h3>
          <ul class="divide-y divide-line/60 px-5">
            {#each rows as g (g.competition)}
              <li class="py-2.5">
                <details class="group">
                  <summary class="flex cursor-pointer list-none items-center gap-3 [&::-webkit-details-marker]:hidden">
                    <span class="display w-8 text-2xl font-bold tabular-nums">{g.years.length}</span>
                    <CompLogo code={g.competition} size={32} />
                    <span class="min-w-0 flex-1">
                      <a class="block truncate font-semibold no-underline hover:text-accent" href={href("competition", g.competition)}>{compName(g.competition)}</a>
                      <span class="block truncate text-xs tabular-nums text-muted">{g.years.slice(0, 4).map((y) => titleYear(g.competition, y)).join(", ")}{g.years.length > 4 ? " …" : ""}</span>
                    </span>
                    {#if g.years.length > 4}<span class="text-muted transition group-open:rotate-90" aria-hidden="true">›</span>{/if}
                  </summary>
                  {#if g.years.length > 4}<p class="mt-1.5 pl-[4.75rem] text-sm leading-relaxed tabular-nums text-muted">{g.years.map((y) => titleYear(g.competition, y)).join(", ")}</p>{/if}
                </details>
              </li>
            {/each}
          </ul>
        {/if}
      {/each}
      <p class="border-t border-line px-5 py-3 text-xs text-muted">{t("honoursPlayerNote")}</p>
    {/if}
    {#if !total && nationalTotal}<p class="border-t border-line px-5 py-3 text-xs text-muted">{t("honoursNationalNote")}</p>{/if}
  </section>
{/if}
