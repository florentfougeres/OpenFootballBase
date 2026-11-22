<script lang="ts">
  import FormPills from "./FormPills.svelte";
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
  let stagePick = $state<string | null>(null);
  let roundPick = $state<string | null>(null);
  let showAll = $state(false);
  let railEl = $state<HTMLElement | null>(null);
  // Sur petit écran le fil de phases défile : la phase choisie (ou ouverte par défaut) est ramenée au centre.
  $effect(() => {
    stage?.key;
    const on = railEl?.querySelector<HTMLElement>('[aria-selected="true"]');
    if (railEl && on) railEl.scrollTo({ left: on.getBoundingClientRect().left - railEl.getBoundingClientRect().left + railEl.scrollLeft - (railEl.clientWidth - on.offsetWidth) / 2 });
  });
  $effect(() => { code; picked = null; stagePick = null; roundPick = null; showAll = false; });
  const season = $derived(picked ?? seasons.data?.[0]);

  const matches = resource(async () => {
    const s = season;
    if (!s) return [] as Row[];
    return await q(`SELECT match_id, round, group_name, match_date, kickoff, home_name, away_name, home_club, away_club, ft_home, ft_away, ht_home, ht_away,
                           et_home, et_away, pen_home, pen_away, ground, attendance, result_source
                    FROM match WHERE competition = ? AND season = ? ORDER BY match_date NULLS LAST, kickoff, home_name`, [code, s]);
  });

  /** Tours dans l'ordre du calendrier (première date de chacun). */
  const rounds = $derived.by(() => {
    const seen: string[] = [];
    for (const m of matches.data ?? []) { const r = (m.round as string) ?? "—"; if (!seen.includes(r)) seen.push(r); }
    return seen;
  });

  // Une compétition est un PARCOURS de phases : phase de ligue, groupes, barrages, huitièmes… Chaque tour de la source (« League, Matchday 3 », « Finals, Quarterfinals »)
  // est rattaché à une phase ; une phase est soit un CLASSEMENT (championnat, groupes : beaucoup de matchs par équipe), soit des CONFRONTATIONS (aller-retour, match unique).
  type RoundInfo = { stage: string; no: number | null };
  const parseRound = (r: string): RoundInfo => {
    let m = /^(.+?), Matchday (\d+)$/.exec(r);
    if (m) return { stage: m[1], no: Number(m[2]) };
    m = /^[▪•]?\s*Matchday (\d+)$/.exec(r) ?? /^(\d+)\. Round$/.exec(r);
    if (m) return { stage: "", no: Number(m[1]) };
    if (/^Group [A-Z0-9]+$/.test(r)) return { stage: "Group", no: null };
    m = /^(?:Finals?|Knockout(?: stage)?|Final stage), (.+)$/.exec(r);
    return { stage: m ? m[1] : r, no: null };
  };
  /** « Round 3 » est aussi le tour d'une coupe : on ne le prend pour une journée que si tous les tours sont ainsi nommés et réunissent à peu près autant de matchs. */
  const allLeagueRounds = (names: string[]) => {
    if (names.length < 4 || names.length !== rounds.length || !names.every((r) => /^Round \d+$/.test(r))) return false;
    const size = names.map((r) => (matches.data ?? []).filter((m) => m.round === r).length);
    return Math.min(...size) >= 0.6 * Math.max(...size);
  };
  const info = $derived.by(() => {
    const league = allLeagueRounds(rounds);
    return new Map(rounds.map((r): [string, RoundInfo] => [r, league ? { stage: "", no: Number(r.slice(6)) } : parseRound(r)]));
  });
  type Stage = { key: string; rounds: string[]; matches: Row[]; table: boolean };
  const teamKey = (club: string | null, name: string) => club ?? name;
  /** Un classement quand chaque équipe joue en moyenne au moins 3 matchs dans la phase ; sinon des confrontations (2 pour un aller-retour, 1 pour une finale). */
  const isTable = (ms: Row[]) => {
    const teams = new Set<string>();
    for (const m of ms) { teams.add(teamKey(m.home_club, m.home_name)); teams.add(teamKey(m.away_club, m.away_name)); }
    return teams.size > 0 && (2 * ms.length) / teams.size >= 3;
  };
  const stages = $derived.by(() => {
    const by = new Map<string, Stage>();
    for (const m of matches.data ?? []) {
      const r = (m.round as string) ?? "—";
      const key = info.get(r)?.stage ?? r;
      const s = by.get(key) ?? { key, rounds: [], matches: [], table: false };
      if (!s.rounds.includes(r)) s.rounds.push(r);
      s.matches.push(m);
      by.set(key, s);
    }
    for (const s of by.values()) s.table = isTable(s.matches);
    return [...by.values()];
  });
  const STAGE_NAMES: [RegExp, string][] = [[/^league$/i, "stLeague"], [/^group( stage)?$/i, "stGroup"], [/^play-?offs?$/i, "stPlayoffs"], [/^round of 16$/i, "stR16"],
    [/^quarter-?finals?$/i, "stQF"], [/^semi-?finals?$/i, "stSF"], [/^final$/i, "stFinal"]];
  const stageLabel = (key: string) => { const hit = STAGE_NAMES.find(([re]) => re.test(key)); return hit ? t(hit[1]) : key; };

  /** Par défaut : la dernière phase dont un match est joué (sinon la première). */
  const stage = $derived.by(() => {
    const found = stagePick && stages.find((s) => s.key === stagePick);
    if (found) return found;
    let last = stages[0];
    for (const s of stages) if (s.matches.some((m) => m.ft_home != null)) last = s;
    return last;
  });
  const played = (s: Stage) => s.matches.some((m) => m.ft_home != null);

  // Dans une phase en classement, des journées numérotées se parcourent avec le sélecteur (8 journées, pas tous les tours de la coupe).
  const stageRounds = $derived((stage?.rounds ?? []).filter((r) => info.get(r)?.no != null));
  const stepped = $derived(Boolean(stage?.table) && stageRounds.length > 1);
  const round = $derived.by(() => {
    if (!stepped) return null;
    if (roundPick && stageRounds.includes(roundPick)) return roundPick;
    let last = stageRounds[0];
    for (const m of stage?.matches ?? []) if (m.ft_home != null && stageRounds.includes(m.round as string)) last = m.round as string;
    return last;
  });
  const roundIdx = $derived(round ? stageRounds.indexOf(round) : -1);
  const upto = $derived(round ? (info.get(round)?.no ?? Infinity) : Infinity);
  const roundLabel = (r: string) => `${t("resRound")} ${info.get(r)?.no ?? r}`;
  const LIST_CAP = 60;
  const shown = $derived.by(() => {
    if (!stage?.table) return [] as Row[];
    const all = stepped ? stage.matches.filter((m) => m.round === round) : stage.matches;
    return showAll || all.length <= LIST_CAP ? all : all.slice(-LIST_CAP);
  });
  const hiddenCount = $derived(stage?.table && !stepped ? stage.matches.length - shown.length : 0);
  /** Les matchs affichés regroupés par jour (le calendrier se lit par jour). */
  const days = $derived.by(() => {
    const by = new Map<string, Row[]>();
    for (const m of shown) { const k = (m.match_date as string | null) ?? ""; by.set(k, [...(by.get(k) ?? []), m]); }
    return [...by.entries()].map(([day, items]) => ({ day, items }));
  });

  // Buteurs des matchs affichés, quand la source les donne.
  const goals = resource(async () => {
    const ids = shown.map((m) => Number(m.match_id)).filter(Number.isFinite);
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

  type Line = { key: string; club: string | null; name: string; p: number; w: number; d: number; l: number; gf: number; ga: number; pts: number; form: ("w" | "d" | "l")[] };
  /** Un classement par groupe : dans une phase de groupes, les équipes qui se rencontrent forment des ensembles disjoints (la source n'en donne pas toujours le nom). Un championnat est un seul groupe. */
  const tables = $derived.by(() => {
    if (!stage?.table) return [] as { title: string; lines: Line[] }[];
    const parent = new Map<string, string>();
    const find = (x: string): string => { let r = x; while ((parent.get(r) ?? r) !== r) r = parent.get(r)!; parent.set(x, r); return r; };
    for (const m of stage.matches) {
      const h = teamKey(m.home_club, m.home_name), a = teamKey(m.away_club, m.away_name);
      if (!parent.has(h)) parent.set(h, h);
      if (!parent.has(a)) parent.set(a, a);
      parent.set(find(h), find(a));
    }
    const groups = new Map<string, { title: string; by: Map<string, Line> }>();
    for (const m of stage.matches) {                                    // dans l'ordre du calendrier : la forme est donc la fin de la liste
      const root = find(teamKey(m.home_club, m.home_name));
      const g = groups.get(root) ?? { title: "", by: new Map<string, Line>() };
      if (!g.title && m.group_name) g.title = m.group_name as string;
      groups.set(root, g);
      if (m.ft_home == null || (info.get((m.round as string) ?? "—")?.no ?? 0) > upto) continue;
      const add = (club: string | null, name: string, gf: number, ga: number) => {
        const key = teamKey(club, name);
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

  // Phase à élimination : les matchs d'une même paire d'équipes forment une confrontation (aller, retour), avec le score cumulé.
  type Side = { club: string | null; name: string; key: string };
  type Tie = { id: string; a: Side; b: Side; legs: Row[]; played: number; ga: number; gb: number; winner: "a" | "b" | null; note: string };
  const ties = $derived.by(() => {
    if (!stage || stage.table) return [] as Tie[];
    const by = new Map<string, Tie>();
    for (const m of stage.matches) {
      const h = teamKey(m.home_club, m.home_name), a = teamKey(m.away_club, m.away_name);
      const id = [h, a].sort().join("|");
      const tie: Tie = by.get(id) ?? { id, a: { club: m.home_club, name: m.home_name, key: h }, b: { club: m.away_club, name: m.away_name, key: a }, legs: [], played: 0, ga: 0, gb: 0, winner: null, note: "" };
      tie.legs.push(m);
      by.set(id, tie);
    }
    for (const tie of by.values()) {
      const score = (m: Row) => { const flip = teamKey(m.home_club, m.home_name) !== tie.a.key; const h = m.et_home ?? m.ft_home, aw = m.et_away ?? m.ft_away; return flip ? [aw, h] : [h, aw]; };
      const done = tie.legs.filter((m) => m.ft_home != null);
      tie.played = done.length;
      for (const m of done) { const [x, y] = score(m); tie.ga += x; tie.gb += y; }
      let pens = "";
      const last = [...done].reverse().find((m) => m.pen_home != null);
      if (last) { const flip = teamKey(last.home_club, last.home_name) !== tie.a.key; const [x, y] = flip ? [last.pen_away, last.pen_home] : [last.pen_home, last.pen_away]; pens = `${t("resPens")} ${x}–${y}`; if (tie.played === tie.legs.length) tie.winner = x > y ? "a" : y > x ? "b" : null; }
      if (!tie.winner && tie.played === tie.legs.length) tie.winner = tie.ga > tie.gb ? "a" : tie.gb > tie.ga ? "b" : null;
      const legScores = tie.legs.map((m) => (m.ft_home == null ? "–" : score(m).join("–")));
      const legs = tie.legs.length === 1 ? "" : tie.legs.length === 2 ? `${t("resLeg1")} ${legScores[0]} · ${t("resLeg2")} ${legScores[1]}` : legScores.join(" · ");
      tie.note = [legs, pens].filter(Boolean).join(" · ");
    }
    return [...by.values()];
  });
  const shortDate = (d: unknown) => (d ? new Date(String(d)).toLocaleDateString(app.lang, { day: "numeric", month: "short" }) : "–");

  const extra = (m: Row) => [
    m.et_home != null ? `${t("resExtra")} ${m.et_home}–${m.et_away}` : "",
    m.pen_home != null ? `${t("resPens")} ${m.pen_home}–${m.pen_away}` : "",
    m.ht_home != null ? `${t("resHalf")} ${m.ht_home}–${m.ht_away}` : ""].filter(Boolean).join(" · ");
  const dayLabel = (d: string) => (d ? new Date(d).toLocaleDateString(app.lang, { weekday: "long", day: "numeric", month: "long", year: "numeric" }) : t("resNoDate"));
  const won = (m: Row, side: "home" | "away") => m.ft_home != null && (side === "home" ? m.ft_home > m.ft_away : m.ft_away > m.ft_home);
</script>

{#snippet team(club: string | null, name: string, size = 22)}
  {#if club}
    <a class="flex min-w-0 items-center gap-2.5 no-underline hover:text-accent" href={href("club", enc(club))}><Logo club={clubOf(club)} size={size} /><span class="line-clamp-2 break-words leading-tight sm:line-clamp-1 sm:truncate">{clubName(clubOf(club))}</span></a>
  {:else if national}
    {@const nt = nationalTeam(name)}
    <span class="flex min-w-0 items-center gap-2.5"><Flag code={nt.flag} label={nt.name} size={size - 2} /><span class="truncate">{nt.name}</span></span>
  {:else}
    <span class="flex min-w-0 items-center gap-2.5"><span class="grid shrink-0 place-items-center rounded-md bg-surface-2 text-[0.6875rem] font-bold text-muted" style="width:{size}px;height:{size}px" aria-hidden="true">{name.slice(0, 2).toUpperCase()}</span><span class="truncate">{name}</span></span>
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
          <th class="max-sm:hidden">{t("resForm")}</th>
        </tr>
      </thead>
      <tbody>
        {#each table as l, i (l.key)}
          <tr>
            <td class="!pr-0 tabular-nums"><span class="inline-grid size-6 place-items-center rounded-md text-xs font-bold {i === 0 ? 'bg-accent text-accent-fg' : 'text-muted'}">{i + 1}</span></td>
            <td class="max-w-[10rem] font-medium sm:max-w-[13rem]">{@render team(l.club, l.name)}<span class="mt-1 block sm:hidden"><FormPills form={l.form} /></span></td>
            <td class="num">{l.p}</td>
            <td class="num max-sm:hidden">{l.w}</td><td class="num max-sm:hidden">{l.d}</td><td class="num max-sm:hidden">{l.l}</td>
            <td class="num max-md:hidden">{l.gf}</td><td class="num max-md:hidden">{l.ga}</td>
            <td class="num">{l.gf - l.ga > 0 ? "+" : ""}{l.gf - l.ga}</td>
            <td class="num display text-base font-bold">{l.pts}</td>
            <td class="max-sm:hidden">
              <FormPills form={l.form} />
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
      disabled={roundIdx <= 0} onclick={() => (roundPick = stageRounds[roundIdx - 1])}>‹</button>
    <select class="max-w-[11rem] cursor-pointer appearance-none bg-transparent px-2 text-center text-sm font-semibold" aria-label={t("resRound")} value={round ?? ""} onchange={(e) => (roundPick = e.currentTarget.value)}>
      {#each stageRounds as r}<option value={r}>{roundLabel(r)}</option>{/each}
    </select>
    <button type="button" class="grid size-8 place-items-center rounded-md text-lg text-muted transition hover:text-fg disabled:opacity-30" aria-label={t("resNext")}
      disabled={roundIdx >= stageRounds.length - 1} onclick={() => (roundPick = stageRounds[roundIdx + 1])}>›</button>
  </div>
{/snippet}

{#snippet matchRow(m: Row)}
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
{/snippet}

{#if seasons.loading && !seasons.data}
  <Spinner />
{:else if !seasons.data?.length}
  <p class="mt-6 text-muted">{t("resNone")}</p>
{:else}
  <h2 class="mt-7 text-lg font-bold">{t("allSeasons")}</h2>
  <div class="-mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-2 [scrollbar-width:none] md:mx-0 md:flex-wrap md:overflow-visible md:px-0 [&::-webkit-scrollbar]:hidden" role="tablist" aria-label={t("allSeasons")}>
    {#each seasons.data as s}
      <button type="button" role="tab" aria-selected={s === season} onclick={() => { picked = s; stagePick = null; roundPick = null; showAll = false; }}
        class="shrink-0 rounded-full border px-4 py-1.5 text-sm font-semibold tabular-nums transition {s === season ? 'border-accent bg-accent text-accent-fg' : 'border-line bg-surface hover:bg-surface-2'}">{s}</button>
    {/each}
  </div>

  {#if matches.loading && !matches.data}
    <Spinner />
  {:else if stage}
    <!-- Le parcours de la compétition : toutes les phases d'un coup, on arrive sur la dernière jouée. -->
    {#if stages.length > 1}
      <div class="mt-6 border-b border-line">
        <div class="-mx-4 -mb-px flex gap-1 overflow-x-auto px-4 [scrollbar-width:none] md:mx-0 md:flex-wrap md:overflow-visible md:px-0 [&::-webkit-scrollbar]:hidden" role="tablist" aria-label={t("resStages")} bind:this={railEl}>
          {#each stages as s (s.key)}
            <button type="button" role="tab" aria-selected={s.key === stage.key} onclick={() => { stagePick = s.key; roundPick = null; showAll = false; }}
              class="shrink-0 whitespace-nowrap border-b-2 px-3.5 py-2.5 text-sm font-semibold transition {s.key === stage.key ? 'border-accent text-fg' : 'border-transparent text-muted hover:text-fg'}">{stageLabel(s.key)}</button>
          {/each}
        </div>
      </div>
    {/if}
    {#if stepped}
      <div class="mt-5 flex flex-wrap items-center gap-x-3 gap-y-2">
        {@render roundNav()}
        <span class="text-xs text-muted">{t("resNavHint")}</span>
      </div>
    {/if}

    {#if stage.table}
      <div class="mt-5 grid grid-cols-[minmax(0,1fr)] items-start gap-6 {tables.length ? 'xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] max-w-4xl xl:max-w-none' : 'max-w-3xl'}">
        {#if tables.length}
          <section aria-labelledby="res-table">
            <h2 id="res-table" class="mb-2 text-xl font-bold">{t("resTable")} <span class="font-semibold tabular-nums text-muted">{season}{#if stages.length > 1}{" · "}{stageLabel(stage.key)}{/if}{#if stepped}{" · "}{t("resAfterRound")} {upto}{/if}</span></h2>
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
          <h2 id="res-matches" class="mb-2 text-xl font-bold">{t("resMatches")}{#if stepped && round}<span class="font-semibold text-muted"> · {roundLabel(round)}</span>{/if}</h2>
          <div class="card px-4 py-1">
            {#each days as d (d.day)}
              <h3 class="mt-3 text-xs font-semibold uppercase tracking-wide text-muted first:mt-2">{dayLabel(d.day)}</h3>
              <ul class="divide-y divide-line/60">
                {#each d.items as m (m.match_id)}{@render matchRow(m)}{/each}
              </ul>
            {/each}
          </div>
          {#if hiddenCount > 0}<button type="button" class="mt-3 text-sm font-semibold text-accent hover:underline" onclick={() => (showAll = true)}>{t("resShowAll")} ({stage.matches.length})</button>{/if}
        </section>
      </div>
    {:else}
      <section class="mt-5 max-w-3xl" aria-labelledby="res-ties">
        <h2 id="res-ties" class="mb-2 text-xl font-bold">{stageLabel(stage.key)} <span class="font-semibold tabular-nums text-muted">{season}</span></h2>
        <div class="card px-4 py-1">
          <ul class="divide-y divide-line/60">
            {#each ties as tie (tie.id)}
              <li class="py-3">
                <div class="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1.5">
                  <span class="min-w-0 {tie.winner === 'a' ? 'font-bold' : ''}">{@render team(tie.a.club, tie.a.name)}</span>
                  {#if tie.played}
                    <span class="display w-6 text-right text-lg tabular-nums {tie.winner === 'a' ? 'font-extrabold' : 'text-muted'}">{tie.ga}</span>
                  {:else}
                    <span class="row-span-2 self-center text-sm font-semibold tabular-nums text-muted">{shortDate(tie.legs[0].match_date)}</span>
                  {/if}
                  <span class="min-w-0 {tie.winner === 'b' ? 'font-bold' : ''}">{@render team(tie.b.club, tie.b.name)}</span>
                  {#if tie.played}<span class="display w-6 text-right text-lg tabular-nums {tie.winner === 'b' ? 'font-extrabold' : 'text-muted'}">{tie.gb}</span>{/if}
                </div>
                {#if tie.note}<p class="mt-1.5 text-xs leading-relaxed tabular-nums text-muted">{tie.note}</p>{/if}
              </li>
            {/each}
          </ul>
        </div>
      </section>
    {/if}
    <p class="mt-4 text-xs text-muted">{t("resSource")}{#if (matches.data ?? []).some((m) => m.result_source)} {t("resWikiNote")}{/if}</p>
  {/if}
{/if}
