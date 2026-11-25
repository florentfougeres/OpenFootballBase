<script lang="ts">
  // Aperçu d'un club, d'après la table `match` (données ouvertes OpenFootball, CC0) : forme, prochain match, classement du championnat,
  // buteurs du club et bilan de chaque entraîneur. Tout est calculé ici, rien n'est inventé : sans match enregistré, un bloc disparaît.
  import type { Snippet } from "svelte";
  import { app, enc, href, seasonSlug, t, type Row } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { clubName, clubOf } from "../lib/format";
  import FormPills from "./FormPills.svelte";
  import Logo from "./Logo.svelte";

  let { club, season, comp, children }: { club: string; season: string | null; comp: string | null; children?: Snippet } = $props();

  type Played = { id: number; date: string; opp: Row; home: boolean; gf: number; ga: number; res: "w" | "d" | "l" };
  type Line = { key: string; club: Row; p: number; w: number; d: number; l: number; gf: number; ga: number; pts: number };
  const res = resource(async () => {
    const title = club, sea = season, code = comp;
    const rows = await q(`SELECT match_id, competition, CAST(match_date AS VARCHAR) AS d, kickoff, home_club, away_club, home_name, away_name, ft_home, ft_away, et_home, et_away
                          FROM match WHERE (home_club = ? OR away_club = ?) AND match_date IS NOT NULL ORDER BY match_date, kickoff`, [title, title]);
    const today = new Date().toISOString().slice(0, 10);
    const opp = (m: Row, home: boolean): Row => {
      const c = home ? m.away_club : m.home_club, n = (home ? m.away_name : m.home_name) as string;
      return c ? clubOf(c as string) : { wikipedia_title: null, name_en: n, name_fr: n };
    };
    const played: Played[] = [];
    let next: (Row & { home: boolean; opp: Row }) | null = null;
    for (const m of rows) {
      const home = m.home_club === title, h = m.et_home ?? m.ft_home, a = m.et_away ?? m.ft_away;
      if (h == null || a == null) { if (!next && m.d && String(m.d) >= today) next = { ...m, home, opp: opp(m, home) }; continue; }
      const gf = home ? h : a, ga = home ? a : h;
      played.push({ id: m.match_id as number, date: String(m.d ?? ""), opp: opp(m, home), home, gf, ga, res: gf > ga ? "w" : gf === ga ? "d" : "l" });
    }
    // Classement du championnat de la saison (3 points la victoire) : les équipes sont repérées par leur page de club, sinon par leur nom.
    let table: Line[] = [];
    if (code && sea) {
      const ms = await q(`SELECT home_club, away_club, home_name, away_name, ft_home, ft_away FROM match WHERE competition = ? AND season = ? AND ft_home IS NOT NULL AND ft_away IS NOT NULL`, [code, sea]);
      const by = new Map<string, Line>();
      const add = (c: unknown, n: unknown, gf: number, ga: number) => {
        const key = String(c ?? n);
        const l = by.get(key) ?? { key, club: c ? clubOf(c as string) : { wikipedia_title: null, name_en: n, name_fr: n }, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0 };
        l.p++; l.gf += gf; l.ga += ga;
        if (gf > ga) { l.w++; l.pts += 3; } else if (gf === ga) { l.d++; l.pts += 1; } else l.l++;
        by.set(key, l);
      };
      for (const m of ms) { add(m.home_club, m.home_name, m.ft_home as number, m.ft_away as number); add(m.away_club, m.away_name, m.ft_away as number, m.ft_home as number); }
      table = [...by.values()].sort((x, y) => y.pts - x.pts || y.gf - y.ga - (x.gf - x.ga) || y.gf - x.gf);
    }
    // Buteurs du club cette saison (tous matchs enregistrés, sans les buts contre son camp).
    const scorers = sea && app.has.match_goal
      ? await q(`SELECT any_value(g.player_name) AS name, any_value(g.player_qid) AS qid, count(*) AS n FROM match_goal g JOIN match m ON m.match_id = g.match_id
                 WHERE m.season = ? AND g.kind <> 'own_goal' AND ((g.side = 'home' AND m.home_club = ?) OR (g.side = 'away' AND m.away_club = ?))
                 GROUP BY COALESCE(g.player_qid, g.player_name) ORDER BY n DESC, name LIMIT 5`, [sea, title, title]) : [];
    // Bilan de chaque entraîneur : les matchs enregistrés pendant son mandat.
    const tenures = app.has.coach ? await q(`SELECT coach_qid, coach_name, CAST(start_date AS VARCHAR) AS s, CAST(end_date AS VARCHAR) AS e FROM coach WHERE club = ? AND start_date IS NOT NULL ORDER BY start_date DESC`, [title]) : [];
    const coaches = tenures.map((c) => {
      const from = String(c.s), to = c.e ? String(c.e) : "9999-12-31";
      const ms = played.filter((m) => m.date >= from && m.date <= to);
      const w = ms.filter((m) => m.res === "w").length, d = ms.filter((m) => m.res === "d").length;
      return { qid: c.coach_qid as string, name: c.coach_name as string, from: from.slice(0, 4), to: c.e ? String(c.e).slice(0, 4) : null, p: ms.length, w, pts: 3 * w + d };
    }).filter((c) => c.p >= 5).slice(0, 5);
    return { last: played.slice(-5).reverse(), next, table, scorers, coaches };
  });

  const d = $derived(res.data);
  /** Sept lignes autour du club (le haut du tableau quand il est dans les premiers). */
  const around = $derived.by(() => {
    const tb = d?.table ?? [], mine = tb.findIndex((l) => l.key === club);
    if (mine < 0) return [] as { rank: number; line: Line }[];
    const from = Math.max(0, Math.min(mine - 3, tb.length - 7));
    return tb.slice(from, from + 7).map((line, i) => ({ rank: from + i + 1, line }));
  });
  const fmt = (iso: string, opts: Intl.DateTimeFormatOptions) => new Date(iso + "T12:00:00").toLocaleDateString(app.lang, opts);
  const compName = (c: string) => app.comps.get(c)?.name_en ? (app.lang === "fr" ? app.comps.get(c)?.name_fr || app.comps.get(c)?.name_en : app.comps.get(c)?.name_en) : c;
  const word = (r: "w" | "d" | "l") => t(r === "w" ? "resW" : r === "d" ? "resD" : "resL");
  const wide = typeof matchMedia === "function" && matchMedia("(min-width: 640px)").matches;          // le détail des derniers matchs est ouvert d'office sur grand écran
  const card = "card p-4 sm:p-5 lg:mb-4 lg:break-inside-avoid";
  const head = "mb-3 text-lg font-bold";
</script>

{#if res.loading && !d}
  <div class="h-40 animate-pulse rounded-2xl bg-surface-2" aria-hidden="true"></div>
{:else if d}
  <div class="flex flex-col gap-4 lg:block lg:columns-2 lg:gap-x-4">
    {@render children?.()}
    {#if d.next}
      {@const n = d.next}
      <section class="{card}" aria-labelledby="ov-next">
        <h2 id="ov-next" class={head}>{t("ovNext")}</h2>
        <div class="flex items-center gap-4">
          <div class="grid min-w-0 flex-1 gap-1">
            <p class="flex items-center gap-2 text-lg font-bold"><Logo club={n.opp} size={32} /><span class="min-w-0 truncate">{clubName(n.opp)}</span></p>
            <p class="text-sm text-muted">{compName(n.competition as string)}, {n.home ? t("ovHome") : t("ovAway")}</p>
          </div>
          <p class="shrink-0 text-right">
            <span class="block font-bold">{fmt(String(n.d), { weekday: "short", day: "numeric", month: "short" })}</span>
            {#if n.kickoff}<span class="block text-sm tabular-nums text-muted">{n.kickoff}</span>{/if}
          </p>
        </div>
      </section>
    {/if}

    {#if around.length}
      <section class="{card}" aria-labelledby="ov-table">
        <h2 id="ov-table" class={head}>{t("resTable")} <span class="text-sm font-semibold text-muted">{season}</span></h2>
        <table class="tbl tbl-flush">
          <thead><tr><th class="w-8">#</th><th>{t("resTeam")}</th><th class="num" title={t("resPlayed")}>{t("resP")}</th><th class="num">{t("resGD")}</th><th class="num">{t("resPts")}</th></tr></thead>
          <tbody>
            {#each around as { rank, line } (line.key)}
              <tr class="{line.key === club ? 'bg-accent-soft font-bold' : ''}" aria-current={line.key === club ? "true" : undefined}>
                <td class="tabular-nums text-muted">{rank}</td>
                <td><span class="flex min-w-0 items-center gap-2"><Logo club={line.club} size={20} /><span class="min-w-0 truncate">{clubName(line.club)}</span></span></td>
                <td class="num tabular-nums">{line.p}</td>
                <td class="num tabular-nums">{line.gf - line.ga > 0 ? "+" : ""}{line.gf - line.ga}</td>
                <td class="num font-bold tabular-nums">{line.pts}</td>
              </tr>
            {/each}
          </tbody>
        </table>
        {#if comp && season}<p class="mt-3 text-sm"><a class="link" href={href("competition", comp, seasonSlug(season))}>{t("ovFullTable")} →</a></p>{/if}
      </section>
    {/if}

    {#if d.scorers.length}
      <section class="{card}" aria-labelledby="ov-scorers">
        <h2 id="ov-scorers" class={head}>{t("ovScorers")} <span class="text-sm font-semibold text-muted">{season}</span></h2>
        <ol class="divide-y divide-line/60">
          {#each d.scorers as s, i (s.qid ?? s.name)}
            <li class="grid min-h-11 grid-cols-[1.5rem_1fr_auto] items-center gap-3 text-sm">
              <span class="tabular-nums text-muted">{i + 1}</span>
              {#if s.qid}<a class="min-w-0 truncate font-medium" href={href("player", enc(s.qid as string))}>{s.name}</a>{:else}<span class="min-w-0 truncate font-medium">{s.name}</span>{/if}
              <span class="display text-2xl font-bold tabular-nums">{s.n}</span>
            </li>
          {/each}
        </ol>
      </section>
    {/if}

    {#if d.last.length}
      <!-- Téléphone : la forme en cinq pastilles et le détail replié, après le prochain match, le classement et les buteurs ; grand écran : la liste ouverte. -->
      <section class="{card}" aria-labelledby="ov-last">
        <div class="flex items-center justify-between gap-3 sm:mb-3">
          <h2 id="ov-last" class="text-lg font-bold">{t("ovLast")}</h2>
          <FormPills form={[...d.last].reverse().map((m) => m.res)} />
        </div>
        <details class="max-sm:mt-2 sm:contents" open={wide}>
          <summary class="min-h-11 cursor-pointer list-none py-2 text-sm font-semibold text-accent sm:hidden">{t("ovDetails")}</summary>
        <ul class="divide-y divide-line/60">
          {#each d.last as m (m.id)}
            <li class="grid min-h-11 grid-cols-[3.25rem_1fr_auto] items-center gap-3 py-1.5 text-sm">
              <span class="text-muted tabular-nums">{m.date ? fmt(m.date, { day: "numeric", month: "short" }) : ""}</span>
              <span class="flex min-w-0 items-center gap-2">
                <Logo club={m.opp} size={20} />
                {#if m.opp.wikipedia_title}<a class="min-w-0 truncate font-medium" href={href("club", enc(m.opp.wikipedia_title as string))}>{clubName(m.opp)}</a>{:else}<span class="min-w-0 truncate font-medium">{clubName(m.opp)}</span>{/if}
                <span class="shrink-0 text-xs text-muted">{m.home ? t("ovHome") : t("ovAway")}</span>
              </span>
              <span class="inline-flex items-center gap-2 font-bold tabular-nums">
                <span class="grid size-6 place-items-center rounded-md text-[0.6875rem] {m.res === 'w' ? 'bg-accent text-accent-fg' : m.res === 'd' ? 'bg-surface-2 text-muted' : 'bg-bad-soft text-bad'}" aria-hidden="true">{word(m.res)}</span>
                <span>{m.gf} – {m.ga}</span>
                <span class="sr-only">{word(m.res)}</span>
              </span>
            </li>
          {/each}
        </ul>
        </details>
      </section>
    {/if}

    {#if d.coaches.length}
      <section class="{card}" aria-labelledby="ov-coach">
        <h2 id="ov-coach" class={head}>{t("ovCoachRecord")}</h2>
        <table class="tbl tbl-flush">
          <thead><tr><th>{t("ovCoach")}</th><th class="num">{t("resP")}</th><th class="num">{t("ovWinPct")}</th><th class="num">{t("ovPpm")}</th></tr></thead>
          <tbody>
            {#each d.coaches as c (c.qid + c.from)}
              <tr>
                <td><a class="font-medium" href={href("coach", c.qid)}>{c.name}</a> <span class="text-muted">{c.from}–{c.to ?? t("ovToday")}</span></td>
                <td class="num tabular-nums">{c.p}</td>
                <td class="num font-bold tabular-nums">{Math.round((100 * c.w) / c.p)} %</td>
                <td class="num tabular-nums">{(c.pts / c.p).toLocaleString(app.lang, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </section>
    {/if}
  </div>
  {#if d.last.length || d.scorers.length || around.length || d.coaches.length}<p class="mt-3 text-xs text-muted">{t("resSource")}</p>{/if}
{/if}
