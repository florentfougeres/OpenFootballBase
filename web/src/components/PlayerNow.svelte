<script lang="ts">
  // « Maintenant » d'un joueur : ses chiffres de la dernière saison (tableaux « Career statistics » de Wikipedia, toutes compétitions) et ses derniers matchs
  // enregistrés (compositions des données ouvertes OpenFootball, CC0). Un bloc sans donnée n'est pas affiché.
  import { app, enc, href, t, type Row } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { clubName, clubOf } from "../lib/format";
  import Logo from "./Logo.svelte";

  let { qid, statClub }: { qid: string | null; statClub: Row[] } = $props();

  const KEY: Record<string, string> = { League: "gLeague", "National cup": "gNationalCup", "League cup": "gLeagueCup", Continental: "gContinental", Europe: "gContinental", Other: "gOther" };
  const season = $derived.by(() => {
    if (!statClub.length) return null;
    const year = (r: Row) => parseInt(String(r.season), 10);          // « 2025–26 » ou « 2026 » : l'année de début
    const last = Math.max(...statClub.map(year).filter((y) => !Number.isNaN(y)));
    if (!Number.isFinite(last)) return null;
    const rows = statClub.filter((r) => year(r) === last);
    const sum = (k: string) => rows.reduce((n, r) => n + (r[k] ?? 0), 0);
    return { label: String(rows[0].season), apps: sum("apps"), goals: sum("goals"), assists: rows.some((r) => r.assists != null) ? sum("assists") : null,
      clubs: [...new Set(rows.map((r) => r.club as string))], rows };
  });

  type Played = { id: number; date: string; opp: Row; gf: number; ga: number; start: boolean; minute: string | null; goals: number };
  const recent = resource(async () => {
    const id = qid;
    if (!id || !app.has.match_lineup) return [] as Played[];
    const rows = await q(`SELECT m.match_id, CAST(m.match_date AS VARCHAR) AS d, m.home_club, m.away_club, m.home_name, m.away_name, m.ft_home, m.ft_away, m.et_home, m.et_away,
                                 l.side, l.role, l.minute,
                                 (SELECT count(*) FROM match_goal g WHERE g.match_id = m.match_id AND g.player_qid = l.player_qid AND g.kind <> 'own_goal') AS goals
                          FROM match_lineup l JOIN match m ON m.match_id = l.match_id
                          WHERE l.player_qid = ? AND m.ft_home IS NOT NULL ORDER BY m.match_date DESC LIMIT 6`, [id]);
    return rows.map((m) => {
      const home = m.side === "home", h = m.et_home ?? m.ft_home, a = m.et_away ?? m.ft_away;
      const c = home ? m.away_club : m.home_club, n = (home ? m.away_name : m.home_name) as string;
      return { id: m.match_id as number, date: String(m.d), opp: c ? clubOf(c as string) : { wikipedia_title: null, name_en: n, name_fr: n }, gf: home ? h : a, ga: home ? a : h,
        start: m.role === "start", minute: m.minute as string | null, goals: Number(m.goals ?? 0) };
    });
  });

  const fmt = (iso: string) => new Date(iso + "T12:00:00").toLocaleDateString(app.lang, { day: "numeric", month: "short", year: "numeric" });
  const res = (m: Played) => (m.gf > m.ga ? "w" : m.gf === m.ga ? "d" : "l");
  const word = (r: string) => t(r === "w" ? "resW" : r === "d" ? "resD" : "resL");
  const card = "card p-4 sm:p-5";
</script>

{#if season}
  <section class="{card} mt-4 sm:mt-6" aria-labelledby="pn-season">
    <h2 id="pn-season" class="mb-3 text-lg font-bold">{t("pnSeason")} <span class="text-sm font-semibold tabular-nums text-muted">{season.label}{season.clubs.length ? `, ${season.clubs.join(", ")}` : ""}</span></h2>
    <ul class="grid grid-cols-3 gap-2 text-center">
      <li class="rounded-xl bg-accent-soft px-2 py-2"><strong class="block text-2xl font-extrabold tabular-nums text-accent">{season.apps}</strong><span class="text-xs text-muted">{t("colApps")}</span></li>
      <li class="rounded-xl bg-accent-soft px-2 py-2"><strong class="block text-2xl font-extrabold tabular-nums text-accent">{season.goals}</strong><span class="text-xs text-muted">{t("colGoals")}</span></li>
      <li class="rounded-xl bg-accent-soft px-2 py-2"><strong class="block text-2xl font-extrabold tabular-nums text-accent">{season.assists ?? "-"}</strong><span class="text-xs text-muted">{t("colAssists")}</span></li>
    </ul>
    {#if season.rows.length > 1}
      <table class="tbl tbl-flush mt-3">
        <thead><tr><th><span class="sr-only">{t("gOther")}</span></th><th class="num px-2" title={t("colApps")}>{t("pnAppsS")}</th><th class="num px-2" title={t("colGoals")}>{t("pnGoalsS")}</th><th class="num px-2" title={t("colAssists")}>{t("pnAssistsS")}</th></tr></thead>
        <tbody>
          {#each season.rows as r, i (i)}
            <tr>
              <td>{t(KEY[r.competition_group as string] ?? "gOther")}{#if r.division && r.competition_group === "League"}{" "}<span class="text-muted">({r.division})</span>{/if}</td>
              <td class="num px-2 tabular-nums">{r.apps ?? "-"}</td>
              <td class="num px-2 tabular-nums">{r.goals ?? "-"}</td>
              <td class="num px-2 tabular-nums">{r.assists ?? "-"}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>
{/if}

{#if recent.data?.length}
  <section class="{card} mt-4 sm:mt-6" aria-labelledby="pn-recent">
    <h2 id="pn-recent" class="mb-3 text-lg font-bold">{t("pnRecent")}</h2>
    <ul class="divide-y divide-line/60">
      {#each recent.data as m (m.id)}
        <li class="grid min-h-12 grid-cols-[5.5rem_1fr_auto] items-center gap-3 py-1.5 text-sm">
          <span class="text-muted tabular-nums">{fmt(m.date)}</span>
          <span class="flex min-w-0 items-center gap-2">
            <Logo club={m.opp} size={20} />
            <span class="min-w-0">
              {#if m.opp.wikipedia_title}<a class="block truncate font-medium" href={href("club", enc(m.opp.wikipedia_title as string))}>{clubName(m.opp)}</a>{:else}<span class="block truncate font-medium">{clubName(m.opp)}</span>{/if}
              <span class="block text-xs text-muted">{m.start ? t("pnStart") : `${t("pnSub")}${m.minute ? ` ${m.minute}'` : ""}`}{#if m.goals}, {m.goals} {m.goals > 1 ? t("goalsLc") : t("goalLc")}{/if}</span>
            </span>
          </span>
          <span class="inline-flex items-center gap-2 font-bold tabular-nums">
            <span class="grid size-6 place-items-center rounded-md text-[0.6875rem] {res(m) === 'w' ? 'bg-accent text-accent-fg' : res(m) === 'd' ? 'bg-surface-2 text-muted' : 'bg-bad-soft text-bad'}" aria-hidden="true">{word(res(m))}</span>
            <span>{m.gf} – {m.ga}</span><span class="sr-only">{word(res(m))}</span>
          </span>
        </li>
      {/each}
    </ul>
    <p class="mt-3 text-xs text-muted">{t("resSource")}</p>
  </section>
{/if}
