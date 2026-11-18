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

  // Un classement n'a de sens que pour un championnat : des journées numérotées (« Matchday 12 », « 23. Round », « Apertura, Matchday 5 »).
  // Les championnats à deux phases (Apertura / Clausura, saison régulière / poule finale) ont un classement PAR phase.
  type RoundInfo = { phase: string; no: number };
  /** La phase n'est montrée que si elle apprend quelque chose (« Clausura », « Championship ») : « Group » ne fait que répéter les titres de groupes. */
  const phaseName = (ph: string) => (ph === "Group" ? "" : ph);
  const parseRound = (r: string): RoundInfo | null => {
    let m = /^(.+?), Matchday (\d+)$/.exec(r);
    if (m) return { phase: m[1], no: Number(m[2]) };
    m = /^[▪•]?\s*Matchday (\d+)$/.exec(r) ?? /^(\d+)\. Round$/.exec(r);
    return m ? { phase: "", no: Number(m[1]) } : null;
  };
  /** « Round 3 » est aussi le tour d'une coupe : on ne le prend pour une journée que si chaque tour réunit à peu près autant de matchs (un tableau à élimination se réduit de tour en tour). */
  const looksLikeLeagueRounds = (names: string[]) => {
    if (names.length < 4) return false;
    const size = names.map((r) => (matches.data ?? []).filter((m) => m.round === r).length);
    return Math.min(...size) >= 0.6 * Math.max(...size);
  };
  const info = $derived.by(() => {
    const out = new Map<string, RoundInfo>();
    for (const r of rounds) { const i = parseRound(r); if (i) out.set(r, i); }
    const plain = rounds.filter((r) => /^Round \d+$/.test(r));
    if (!out.size && looksLikeLeagueRounds(plain)) for (const r of plain) out.set(r, { phase: "", no: Number(r.slice(6)) });
    return out;
  });
  const isLeague = $derived.by(() => {
    if (info.size < 4) return false;
    const played = (matches.data ?? []).filter((m) => info.has((m.round as string) ?? "—")).length;
    return played >= 0.7 * (matches.data ?? []).length;                  // le reste (finales, barrages) ne compte pas dans le classement
  });
  const phases = $derived([...new Set([...info.values()].map((i) => i.phase))]);
  /** La phase du classement : celle de la journée affichée ; sur une journée sans numéro (finale, barrage), la phase la plus récente. */
  const lastPhase = $derived.by(() => { let ph = phases[0] ?? ""; for (const m of matches.data ?? []) { const i = info.get((m.round as string) ?? "—"); if (i && m.ft_home != null) ph = i.phase; } return ph; });
  const tablePhase = $derived(info.get(round)?.phase ?? lastPhase);
  const upto = $derived.by(() => {
    const i = info.get(round);
    if (i) return i.no;
    return Math.max(0, ...[...info.values()].filter((x) => x.phase === tablePhase).map((x) => x.no));
  });
  /** « Matchday 12 » devient « Journée 12 » (« Matchday 12 » en anglais), précédé de la phase s'il y en a ; les autres tours gardent le nom de la source. */
  const roundLabel = (r: string) => { const i = isLeague ? info.get(r) : undefined; return i ? `${phaseName(i.phase) ? phaseName(i.phase) + " · " : ""}${t("resRound")} ${i.no}` : r; };
  type Line = { key: string; club: string | null; name: string; p: number; w: number; d: number; l: number; gf: number; ga: number; pts: number; form: ("w" | "d" | "l")[] };
  /** Un classement par groupe : dans une phase de groupes, les équipes qui se rencontrent forment des ensembles disjoints (la source n'en donne pas toujours le nom). Un championnat est un seul groupe. */
  const tables = $derived.by(() => {
    if (!isLeague) return [] as { title: string; lines: Line[] }[];
    const inPhase = (matches.data ?? []).filter((m) => info.get((m.round as string) ?? "—")?.phase === tablePhase);
    const team = (club: string | null, name: string) => club ?? name;
    const parent = new Map<string, string>();
    const find = (x: string): string => { let r = x; while ((parent.get(r) ?? r) !== r) r = parent.get(r)!; parent.set(x, r); return r; };
    for (const m of inPhase) {
      const h = team(m.home_club, m.home_name), a = team(m.away_club, m.away_name);
      if (!parent.has(h)) parent.set(h, h);
      if (!parent.has(a)) parent.set(a, a);
      parent.set(find(h), find(a));
    }
    const groups = new Map<string, { title: string; by: Map<string, Line> }>();
    for (const m of inPhase) {                                         // dans l'ordre du calendrier : la forme est donc la fin de la liste
      const g = groups.get(find(team(m.home_club, m.home_name))) ?? { title: "", by: new Map<string, Line>() };
      if (!g.title && m.group_name) g.title = m.group_name as string;
      groups.set(find(team(m.home_club, m.home_name)), g);
      if (m.ft_home == null || (info.get((m.round as string) ?? "—")?.no ?? Infinity) > upto) continue;
      const add = (club: string | null, name: string, gf: number, ga: number) => {
        const key = team(club, name);
        const l = g.by.get(key) ?? { key, club, name, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0, form: [] };
        l.p++; l.gf += gf; l.ga += ga;
        if (gf > ga) { l.w++; l.pts += 3; l.form.push("w"); } else if (gf === ga) { l.d++; l.pts += 1; l.form.push("d"); } else { l.l++; l.form.push("l"); }
        g.by.set(key, l);
      };
      add(m.home_club, m.home_name, m.ft_home, m.ft_away);
      add(m.away_club, m.away_name, m.ft_away, m.ft_home);
    }
    const many = groups.size > 1;
    return [...groups.values()].map((g, i) => ({
      title: many ? g.title || `${t("resGroup")} ${i + 1}` : "",
      lines: [...g.by.values()].sort((x, y) => y.pts - x.pts || y.gf - y.ga - (x.gf - x.ga) || y.gf - x.gf || x.name.localeCompare(y.name)),
    })).filter((g) => g.lines.length);
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

{#snippet standing(table: Line[])}
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
            <td class="max-w-[10rem] font-medium sm:max-w-[13rem]">{@render team(l.club, l.name)}</td>
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
{/snippet}

{#snippet roundNav()}
  <div class="inline-flex items-center rounded-lg border border-line bg-surface p-0.5">
    <button type="button" class="grid size-8 place-items-center rounded-md text-lg text-muted transition hover:text-fg disabled:opacity-30" aria-label={t("resPrev")}
      disabled={roundIdx <= 0} onclick={() => (roundPick = rounds[roundIdx - 1])}>‹</button>
    <select class="max-w-[11rem] cursor-pointer appearance-none bg-transparent px-2 text-center text-sm font-semibold" aria-label={t("resRound")} value={round} onchange={(e) => (roundPick = e.currentTarget.value)}>
      {#each rounds as r}<option value={r}>{roundLabel(r)}</option>{/each}
    </select>
    <button type="button" class="grid size-8 place-items-center rounded-md text-lg text-muted transition hover:text-fg disabled:opacity-30" aria-label={t("resNext")}
      disabled={roundIdx >= rounds.length - 1} onclick={() => (roundPick = rounds[roundIdx + 1])}>›</button>
  </div>
{/snippet}

{#if seasons.loading && !seasons.data}
  <Spinner />
{:else if !seasons.data?.length}
  <p class="mt-6 text-muted">{t("resNone")}</p>
{:else}
  <h2 class="mt-7 text-lg font-bold">{t("allSeasons")}</h2>
  <div class="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-2 [scrollbar-width:none] md:mx-0 md:flex-wrap md:overflow-visible md:px-0 [&::-webkit-scrollbar]:hidden" role="tablist" aria-label={t("allSeasons")}>
    {#each seasons.data as s}
      <button type="button" role="tab" aria-selected={s === season} onclick={() => { picked = s; roundPick = null; }}
        class="shrink-0 rounded-full border px-4 py-1.5 text-sm font-semibold tabular-nums transition {s === season ? 'border-accent bg-accent text-accent-fg' : 'border-line bg-surface hover:bg-surface-2'}">{s}</button>
    {/each}
  </div>

  {#if matches.loading && !matches.data}
    <Spinner />
  {:else}
    {#if isLeague}
      <div class="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2">
        {@render roundNav()}
        <span class="text-xs text-muted">{t("resNavHint")}</span>
      </div>
    {/if}
    <div class="mt-4 grid grid-cols-[minmax(0,1fr)] items-start gap-6 {tables.length ? 'xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] max-w-4xl xl:max-w-none' : 'max-w-3xl'}">
      {#if tables.length}
        <section aria-labelledby="res-table">
          <h2 id="res-table" class="mb-2 text-xl font-bold">{t("resTable")} <span class="font-semibold tabular-nums text-muted">{season}{#if isLeague}{#if phases.length > 1 && phaseName(tablePhase)}{" · "}{tablePhase}{/if}{" · "}{t("resAfterRound")} {upto}{/if}</span></h2>
          <div class="grid gap-5">
            {#each tables as tb (tb.title)}
              <div>
                {#if tb.title}<h3 class="mb-1.5 text-sm font-semibold text-muted">{tb.title}</h3>{/if}
                {@render standing(tb.lines)}
              </div>
            {/each}
          </div>
          <p class="mt-2 text-xs text-muted">{t("resTableNote")}</p>
        </section>
      {/if}

      <section aria-labelledby="res-matches">
        <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
          <h2 id="res-matches" class="text-xl font-bold">{t("resMatches")}</h2>
          {#if !isLeague}{@render roundNav()}{/if}
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
