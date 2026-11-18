<script lang="ts">
  // Résultats et classement d'une compétition, d'après la table `match` (données ouvertes OpenFootball, CC0).
  import { app, enc, href, t, type Row } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { clubName, clubOf, nationalTeam } from "../lib/format";
  import Flag from "./Flag.svelte";
  import Icon from "./Icon.svelte";
  import Logo from "./Logo.svelte";
  import Spinner from "./Spinner.svelte";

  let { code, national = false }: { code: string; national?: boolean } = $props();

  const seasons = resource(async () =>
    (await q(`SELECT DISTINCT season FROM match WHERE competition = ? ORDER BY season DESC`, [code])).map((r) => r.season as string));
  let picked = $state<string | null>(null);
  let roundPick = $state<string | null>(null);
  $effect(() => { code; picked = null; roundPick = null; });
  const season = $derived(picked ?? seasons.data?.[0]);

  const matches = resource(async () => {
    const s = season;
    if (!s) return [] as Row[];
    return await q(`SELECT match_id, round, group_name, match_date, kickoff, home_name, away_name, home_club, away_club, ft_home, ft_away, ht_home, ht_away,
                           et_home, et_away, pen_home, pen_away, ground, attendance, result_source
                    FROM match WHERE competition = ? AND season = ? ORDER BY match_date NULLS LAST, kickoff, home_name`, [code, s]);
  });

  /** Journées dans l'ordre du calendrier (première date de chacune). */
  const rounds = $derived.by(() => {
    const seen: string[] = [];
    for (const m of matches.data ?? []) { const r = (m.round as string) ?? "—"; if (!seen.includes(r)) seen.push(r); }
    return seen;
  });
  /** Par défaut : la dernière journée dont un match est joué (sinon la première). */
  const round = $derived.by(() => {
    if (roundPick && rounds.includes(roundPick)) return roundPick;
    let last = rounds[0];
    for (const m of matches.data ?? []) if (m.ft_home != null) last = (m.round as string) ?? "—";
    return last;
  });
  const roundIdx = $derived(rounds.indexOf(round));
  const ofRound = $derived((matches.data ?? []).filter((m) => ((m.round as string) ?? "—") === round));
  /** Les matchs de la journée regroupés par jour (le calendrier se lit par jour). */
  const days = $derived.by(() => {
    const by = new Map<string, Row[]>();
    for (const m of ofRound) { const k = (m.match_date as string | null) ?? ""; by.set(k, [...(by.get(k) ?? []), m]); }
    return [...by.entries()].map(([day, items]) => ({ day, items }));
  });

  // Buteurs de la journée affichée, quand la source les donne.
  const goals = resource(async () => {
    const ids = ofRound.map((m) => Number(m.match_id)).filter(Number.isFinite);
    if (!ids.length || !app.has.match_goal) return new Map<number, Row[]>();
    const rows = await q(`SELECT match_id, side, player_name, minute, kind FROM match_goal WHERE match_id IN (${ids.join(",")}) ORDER BY match_id, seq`);
    const by = new Map<number, Row[]>();
    for (const r of rows) by.set(r.match_id as number, [...(by.get(r.match_id as number) ?? []), r]);
    return by;
  });
  /** « MOHAMED SALAH » et « Hugo EKITIKE » : la source écrit la casse comme elle veut. */
  const nice = (n: string) => n.split(" ").map((w) => (w.length > 1 && w === w.toUpperCase() ? w[0] + w.slice(1).toLowerCase() : w)).join(" ");
  const scorers = (id: number, side: string) => (goals.data?.get(id) ?? []).filter((g) => g.side === side)
    .map((g) => `${nice(g.player_name as string)} ${g.minute ?? ""}'${g.kind === "penalty" ? ` (${t("resPenAbbr")})` : g.kind === "own_goal" ? ` (${t("resOgAbbr")})` : ""}`);

  // Un classement n'a de sens que pour un championnat : toutes les journées s'appellent « Matchday N ».
  const isLeague = $derived(rounds.length > 0 && rounds.every((r) => /^Matchday \d+$/.test(r)));
  type Line = { key: string; club: string | null; name: string; p: number; w: number; d: number; l: number; gf: number; ga: number; pts: number; form: ("w" | "d" | "l")[] };
  const table = $derived.by(() => {
    if (!isLeague) return [] as Line[];
    const by = new Map<string, Line>();
    const add = (club: string | null, name: string, gf: number, ga: number) => {
      const key = club ?? name;
      const l = by.get(key) ?? { key, club, name, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0, form: [] };
      l.p++; l.gf += gf; l.ga += ga;
      if (gf > ga) { l.w++; l.pts += 3; l.form.push("w"); } else if (gf === ga) { l.d++; l.pts += 1; l.form.push("d"); } else { l.l++; l.form.push("l"); }
      by.set(key, l);
    };
    for (const m of matches.data ?? []) {                              // dans l'ordre du calendrier : la forme est donc la fin de la liste
      if (m.ft_home == null) continue;
      add(m.home_club, m.home_name, m.ft_home, m.ft_away);
      add(m.away_club, m.away_name, m.ft_away, m.ft_home);
    }
    return [...by.values()].sort((a, b) => b.pts - a.pts || b.gf - b.ga - (a.gf - a.ga) || b.gf - a.gf || a.name.localeCompare(b.name));
  });
  const FORM_LABEL = { w: "resW", d: "resD", l: "resL" } as const;

  const extra = (m: Row) => [
    m.et_home != null ? `${t("resExtra")} ${m.et_home}–${m.et_away}` : "",
    m.pen_home != null ? `${t("resPens")} ${m.pen_home}–${m.pen_away}` : "",
    m.ht_home != null ? `${t("resHalf")} ${m.ht_home}–${m.ht_away}` : ""].filter(Boolean).join(" · ");
  const dayLabel = (d: string) => (d ? new Date(d).toLocaleDateString(app.lang, { weekday: "long", day: "numeric", month: "long", year: "numeric" }) : t("resNoDate"));
  const won = (m: Row, side: "home" | "away") => m.ft_home != null && (side === "home" ? m.ft_home > m.ft_away : m.ft_away > m.ft_home);
</script>

{#snippet team(club: string | null, name: string, size = 22)}
  {#if club}
    <a class="flex min-w-0 items-center gap-2.5 no-underline hover:text-accent" href={href("club", enc(club))}><Logo club={clubOf(club)} size={size} /><span class="truncate">{clubName(clubOf(club))}</span></a>
  {:else if national}
    {@const nt = nationalTeam(name)}
    <span class="flex min-w-0 items-center gap-2.5"><Flag code={nt.flag} label={nt.name} size={size - 2} /><span class="truncate">{nt.name}</span></span>
  {:else}
    <span class="flex min-w-0 items-center gap-2.5"><span class="grid shrink-0 place-items-center rounded-md bg-surface-2 text-[0.6rem] font-bold text-muted" style="width:{size}px;height:{size}px" aria-hidden="true">{name.slice(0, 2).toUpperCase()}</span><span class="truncate">{name}</span></span>
  {/if}
{/snippet}

{#if seasons.loading && !seasons.data}
  <Spinner />
{:else if !seasons.data?.length}
  <p class="mt-6 text-muted">{t("resNone")}</p>
{:else}
  <h2 class="mt-7 text-lg font-bold">{t("allSeasons")}</h2>
  <div class="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-2 [scrollbar-width:none] md:mx-0 md:px-0 [&::-webkit-scrollbar]:hidden" role="tablist" aria-label={t("allSeasons")}>
    {#each seasons.data as s}
      <button type="button" role="tab" aria-selected={s === season} onclick={() => { picked = s; roundPick = null; }}
        class="shrink-0 rounded-full border px-4 py-1.5 text-sm font-semibold tabular-nums transition {s === season ? 'border-accent bg-accent text-accent-fg' : 'border-line bg-surface hover:bg-surface-2'}">{s}</button>
    {/each}
  </div>

  {#if matches.loading && !matches.data}
    <Spinner />
  {:else}
    <div class="mt-6 grid grid-cols-[minmax(0,1fr)] items-start gap-6 {table.length ? 'xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] max-w-4xl xl:max-w-none' : 'max-w-3xl'}">
      {#if table.length}
        <section aria-labelledby="res-table">
          <h2 id="res-table" class="mb-2 text-xl font-bold">{t("resTable")} <span class="font-semibold tabular-nums text-muted">{season}</span></h2>
          <div class="card overflow-x-auto">
            <table class="tbl">
              <thead>
                <tr>
                  <th class="w-9 !pr-0">#</th><th>{t("resTeam")}</th>
                  <th class="num" title={t("resPlayed")}>{t("resP")}</th>
                  <th class="num max-sm:hidden">{t("resW")}</th><th class="num max-sm:hidden">{t("resD")}</th><th class="num max-sm:hidden">{t("resL")}</th>
                  <th class="num max-md:hidden">{t("resGF")}</th><th class="num max-md:hidden">{t("resGA")}</th>
                  <th class="num">{t("resGD")}</th><th class="num">{t("resPts")}</th>
                  <th class="max-2xl:hidden">{t("resForm")}</th>
                </tr>
              </thead>
              <tbody>
                {#each table as l, i (l.key)}
                  <tr>
                    <td class="!pr-0 tabular-nums"><span class="inline-grid size-6 place-items-center rounded-md text-xs font-bold {i === 0 ? 'bg-accent text-accent-fg' : 'text-muted'}">{i + 1}</span></td>
                    <td class="max-w-[13rem] font-medium">{@render team(l.club, l.name)}</td>
                    <td class="num">{l.p}</td>
                    <td class="num max-sm:hidden">{l.w}</td><td class="num max-sm:hidden">{l.d}</td><td class="num max-sm:hidden">{l.l}</td>
                    <td class="num max-md:hidden">{l.gf}</td><td class="num max-md:hidden">{l.ga}</td>
                    <td class="num">{l.gf - l.ga > 0 ? "+" : ""}{l.gf - l.ga}</td>
                    <td class="num display text-base font-bold">{l.pts}</td>
                    <td class="max-2xl:hidden">
                      <span class="flex gap-1" role="img" aria-label={l.form.slice(-5).map((f) => t(FORM_LABEL[f])).join(" ")}>
                        {#each l.form.slice(-5) as f}
                          <span class="grid size-5 place-items-center rounded text-[0.65rem] font-bold {f === 'w' ? 'bg-accent text-accent-fg' : f === 'd' ? 'bg-surface-2 text-muted' : 'bg-warn-soft text-warn'}" aria-hidden="true">{t(FORM_LABEL[f])}</span>
                        {/each}
                      </span>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
          <p class="mt-2 text-xs text-muted">{t("resTableNote")}</p>
        </section>
      {/if}

      <section aria-labelledby="res-matches">
        <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
          <h2 id="res-matches" class="text-xl font-bold">{t("resMatches")}</h2>
          <div class="inline-flex items-center rounded-lg border border-line bg-surface p-0.5">
            <button type="button" class="grid size-8 place-items-center rounded-md text-lg text-muted transition hover:text-fg disabled:opacity-30" aria-label={t("resPrev")}
              disabled={roundIdx <= 0} onclick={() => (roundPick = rounds[roundIdx - 1])}>‹</button>
            <select class="max-w-[11rem] cursor-pointer appearance-none bg-transparent px-2 text-center text-sm font-semibold" aria-label={t("resRound")} value={round} onchange={(e) => (roundPick = e.currentTarget.value)}>
              {#each rounds as r}<option value={r}>{r}</option>{/each}
            </select>
            <button type="button" class="grid size-8 place-items-center rounded-md text-lg text-muted transition hover:text-fg disabled:opacity-30" aria-label={t("resNext")}
              disabled={roundIdx >= rounds.length - 1} onclick={() => (roundPick = rounds[roundIdx + 1])}>›</button>
          </div>
        </div>
        <div class="card px-4 py-1">
          {#each days as d (d.day)}
            <h3 class="mt-3 text-xs font-semibold uppercase tracking-wide text-muted first:mt-2">{dayLabel(d.day)}</h3>
            <ul class="divide-y divide-line/60">
              {#each d.items as m (m.match_id)}
                {@const home = scorers(m.match_id as number, "home")}
                {@const away = scorers(m.match_id as number, "away")}
                <li class="py-2.5">
                  <div class="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1.5">
                    <span class="min-w-0 {won(m, 'home') ? 'font-bold' : ''}">{@render team(m.home_club, m.home_name)}</span>
                    {#if m.ft_home != null}
                      <span class="display w-6 text-right text-lg tabular-nums {won(m, 'home') ? 'font-extrabold' : 'text-muted'}">{m.ft_home}</span>
                    {:else}
                      <span class="row-span-2 self-center text-sm font-semibold tabular-nums text-muted">{m.kickoff ?? "–"}</span>
                    {/if}
                    <span class="min-w-0 {won(m, 'away') ? 'font-bold' : ''}">{@render team(m.away_club, m.away_name)}</span>
                    {#if m.ft_home != null}<span class="display w-6 text-right text-lg tabular-nums {won(m, 'away') ? 'font-extrabold' : 'text-muted'}">{m.ft_away}</span>{/if}
                  </div>
                  {#if extra(m) || home.length || away.length}
                    <p class="mt-1.5 text-xs leading-relaxed text-muted">
                      {#if home.length || away.length}<span class="inline-flex items-start gap-1"><Icon name="ball" size={12} /><span>{[...home, ...away].join(" · ")}</span></span>{/if}
                      {#if extra(m)}<span class="block">{extra(m)}</span>{/if}
                    </p>
                  {/if}
                </li>
              {/each}
            </ul>
          {/each}
        </div>
      </section>
    </div>
    <p class="mt-4 text-xs text-muted">{t("resSource")}{#if (matches.data ?? []).some((m) => m.result_source)} {t("resWikiNote")}{/if}</p>
  {/if}
{/if}
