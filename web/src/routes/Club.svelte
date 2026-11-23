<script lang="ts">
  import { app, countryOf, href, enc, route, seasonSlug, t, type Row } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { downloadCsv, RELEASES_URL } from "../lib/download";
  import { compKind, titleYear, clubName, clubOf, commonsLogo, compName, countryName, fmtFounded, hostLang, seasonAge, wikiUrl } from "../lib/format";
  import Trophy from "../components/Trophy.svelte";
  import CompLogo from "../components/CompLogo.svelte";
  import Badge from "../components/Badge.svelte";
  import Crumbs from "../components/Crumbs.svelte";
  import FollowButton from "../components/FollowButton.svelte";
  import Segmented from "../components/Segmented.svelte";
  import PlayerPreview from "../components/PlayerPreview.svelte";
  import Sheet from "../components/Sheet.svelte";
  import Flag from "../components/Flag.svelte";
  import Logo from "../components/Logo.svelte";
  import Spinner from "../components/Spinner.svelte";
  import WikiButton from "../components/WikiButton.svelte";
  import ClubMap from "../components/ClubMap.svelte";
  import ErrorBox from "../components/ErrorBox.svelte";

  // Une seule page pour le club et son effectif : sans `slug`, la saison la plus récente qui a un effectif ; avec, celle de l'adresse.
  let { key, slug }: { key: string; slug?: string } = $props();

  const res = resource(async () => {
    const qid = /^Q\d+$/.test(key) ? key : app.clubs.get(key)?.wikidata_qid || null;
    const ours = (qid && app.clubByQid.get(qid)) || app.clubs.get(key) || null;
    const w = qid ? (await q(`SELECT * FROM club WHERE wikidata_qid = ?`, [qid]))[0] ?? null : null;
    if (!ours && !w) return null;
    let seasons: any[] = [];
    if (ours) seasons = await q(`SELECT season, competition, players, known_gap_reason FROM club_season WHERE club = ? ORDER BY season DESC`, [ours.wikipedia_title]);
    const urls: Record<string, string> = {};
    if (qid && app.has.entity_wiki) for (const r of await q(`SELECT lang, title FROM entity_wiki WHERE qid = ?`, [qid])) urls[r.lang] = wikiUrl(r.lang, r.title);
    if (w) {
      if (w.wikipedia_en_url && !urls.en) urls.en = w.wikipedia_en_url;
      const hl = hostLang(w.wikipedia_local_url);
      if (hl && !urls[hl]) urls[hl] = w.wikipedia_local_url;
    }
    return { ours, w, seasons, urls };
  });

  const d = $derived(res.data);
  const KINDS = ["league", "cup", "intl"] as const;

  // Titres : les compétitions que le club a gagnées (palmarès Wikidata), regroupées par compétition.
  const honours = resource(async () => {
    const tt = title;
    if (!tt || !app.has.winner) return [] as { code: string; years: number[] }[];
    const rows = await q(`SELECT competition, season_start FROM winner WHERE club = ? ORDER BY competition, season_start DESC`, [tt]);
    const by = new Map<string, number[]>();
    for (const r of rows) by.set(r.competition, [...(by.get(r.competition) ?? []), r.season_start as number]);
    return [...by.entries()].map(([code, years]) => ({ code, years })).sort((a, b) => b.years.length - a.years.length);
  });
  // Entraîneurs : les mandats publiés (Wikidata), le plus récent d'abord ; un entraîneur qui a aussi été joueur dans notre base mène à sa fiche.
  const coaches = resource(async () => {
    const tt = title;
    if (!tt || !app.has.coach) return [] as { qid: string; name: string; from: number; to: number | null; player: boolean; flag: string | null }[];
    // `flag` (drapeau du pays de l'entraîneur) n'existe que dans les releases récentes : on lit toutes les colonnes sans la nommer.
    const rows = await q(`SELECT *, CAST(start_date AS VARCHAR) AS s, CAST(end_date AS VARCHAR) AS e FROM coach WHERE club = ? ORDER BY start_date DESC`, [tt]);
    // Wikidata ne liste pas tous les entraîneurs sur la page d'un club (Manchester City : Pellegrini manquait) : on complète avec les carrières d'infobox
    // (« Teams managed ») des entraîneurs qui citent ce club, adjoints exclus, pour ceux que Wikidata ne donne pas déjà pour ce club.
    const known = new Set(rows.map((r) => r.coach_qid as string));
    const extra = app.has.coach_career ? await q(`SELECT c.coach_qid, c.start_year, c.end_year, n.name, n.flag FROM coach_career c
        JOIN (SELECT coach_qid, any_value(coach_name) AS name, any_value(flag) AS flag FROM coach GROUP BY coach_qid) n ON n.coach_qid = c.coach_qid
        WHERE c.team_link = ? AND c.start_year IS NOT NULL AND COALESCE(c.assistant, false) = false`, [tt]) : [];
    const more = extra.filter((r) => !known.has(r.coach_qid as string));
    const ids = [...new Set([...rows.map((r) => r.coach_qid as string), ...more.map((r) => r.coach_qid as string)])];
    const players = ids.length && app.has.career ? new Set((await q(`SELECT DISTINCT player_qid FROM career WHERE player_qid IN (${ids.map(() => "?").join(",")})`, ids)).map((r) => r.player_qid as string)) : new Set<string>();
    const all = [
      ...rows.map((r) => ({ qid: r.coach_qid as string, name: r.coach_name as string, from: Number(String(r.s).slice(0, 4)), to: r.e ? Number(String(r.e).slice(0, 4)) : null, player: players.has(r.coach_qid as string), flag: (r.flag as string | null) ?? null })),
      ...more.map((r) => ({ qid: r.coach_qid as string, name: r.name as string, from: Number(r.start_year), to: r.end_year != null ? Number(r.end_year) : null, player: players.has(r.coach_qid as string), flag: (r.flag as string | null) ?? null })),
    ];
    return all.sort((a, b) => b.from - a.from || (b.to ?? 9999) - (a.to ?? 9999));
  });
  const title = $derived(d?.ours?.wikipedia_title as string | undefined);
  const iso = $derived(d?.w?.country_iso ? String(d.w.country_iso).toLowerCase() : null);
  const flag = $derived(d?.ours ? countryOf(d.ours.country_code).flag : iso);
  const country = $derived(d?.ours ? countryOf(d.ours.country_code).name : d?.w?.country_iso ? countryName(d.w.country_iso) : "");
  const name = $derived(d ? (d.ours ? clubName(d.ours) : app.lang === "fr" ? d.w?.name_local : d.w?.name_en || d.w?.name_local) : "");
  const sub = $derived(d?.w && d.w.name_en && d.w.name_en !== name ? d.w.name_en : d?.w && d.w.name_local !== name ? d.w.name_local : "");
  const logo = $derived({ logo_url: d?.ours?.logo_url || d?.w?.logo_url || commonsLogo(d?.w?.logo_commons_url),
    colors_hex: d?.ours?.colors_hex || d?.w?.colors_hex, name_en: d?.ours?.name_en || d?.w?.name_en, name_local: d?.w?.name_local, wikipedia_title: d?.ours?.wikipedia_title });
  const kit = $derived((String(logo.colors_hex ?? "").split(/\s*\|\s*/)).filter((c: string) => /^#[0-9a-fA-F]{6}$/.test(c)));

  // Saison affichée : celle de l'adresse, sinon la plus récente qui a un effectif (à défaut la plus récente).
  const seasonList = $derived((d?.seasons ?? []) as Row[]);
  const label = $derived.by(() => {
    if (!seasonList.length) return undefined;
    const fromUrl = slug ? Object.keys(app.manifest.seasons).find((s) => seasonSlug(s) === slug) : undefined;
    return fromUrl ?? (seasonList.find((r) => r.players) ?? seasonList[0]).season;
  });
  const current = $derived(seasonList.find((r) => r.season === label));
  const idx = $derived(seasonList.findIndex((s) => s.season === label));
  const older = $derived(idx >= 0 ? seasonList[idx + 1] : undefined);       // liste triée de la plus récente à la plus ancienne
  const newer = $derived(idx > 0 ? seasonList[idx - 1] : undefined);
  const to = (s: string) => href("club", enc(title ?? key), seasonSlug(s));
  const level = (r: Row) => app.comps.get(r.competition)?.level as number | undefined;

  // Autres compétitions de la saison (Ligue des champions) en plus du championnat du club-saison.
  const extra = resource(async () => {
    if (!label || !title || !app.has.competition_club) return [] as string[];
    return (await q(`SELECT competition FROM competition_club WHERE club = ? AND season = ?`, [title, label])).map((r) => r.competition as string);
  });

  const sq = resource(async () => {
    const lbl = label, tt = title;
    if (!lbl || !tt) return null;
    const rows = await q(`SELECT s.player, COALESCE(s.player_qid, 'name:' || s.player) AS key, s.shirt_number, s.position, s.nationality, s.nat_flag, s.stint, s.confidence,
        ${app.squadHasMoves ? "s.stint_date, s.stint_window, s.stint_other_club" : "NULL AS stint_date, NULL AS stint_window, NULL AS stint_other_club"},
        ${app.has.birth ? "b.birth_date, b.precision" : "NULL AS birth_date, NULL AS precision"}
      FROM squad s ${app.has.birth ? "LEFT JOIN birth b ON b.player_qid = s.player_qid" : ""}
      WHERE s.club = ? AND s.season = ? ORDER BY s.shirt_number NULLS LAST, s.player`, [tt, lbl]);
    const [cs] = await q(`SELECT source_lang, source_title, known_gap_reason FROM club_season WHERE club = ? AND season = ?`, [tt, lbl]);
    const sources = app.has.squad_source
      ? await q(`SELECT rank, source_lang, source_title, players_read, players_added FROM squad_source WHERE club = ? AND season = ? ORDER BY rank`, [tt, lbl])
      : [];
    return { rows, cs, sources };
  });
  const squad = $derived(sq.data);
  /** Effectif déduit (carrières, saison précédente + transferts) et non lu sur une page : à signaler, il peut être incomplet. */
  const partial = $derived(!!squad?.rows.length && squad.rows.filter((r: Row) => r.confidence === "inferred").length * 2 > squad.rows.length);

  // Mouvements : on compare l'effectif de la saison à celui de la précédente (aucun tableau de transferts requis).
  // Cinq vues : Aperçu (la fiche du club), Effectif et Mouvements (une saison, arrivées et départs), Entraîneurs et Palmarès. L'onglet est dans l'adresse (`?tab=`) : partageable, et le retour du navigateur le restitue.
  // Sans `?tab=` : l'effectif quand l'adresse porte une saison (on vient d'un classement ou d'une liste de la saison), sinon l'aperçu (on vient voir le club).
  type Tab = "overview" | "squad" | "moves" | "coaches" | "honours";
  const tabs = $derived<Tab[]>(["overview", ...(d?.ours ? (["squad", "moves"] as Tab[]) : []), ...(coaches.loading || coaches.data?.length ? (["coaches"] as Tab[]) : []), ...(honours.loading || honours.data?.length ? (["honours"] as Tab[]) : [])]);
  const tab = $derived.by<Tab>(() => {
    const want = route.query.get("tab") as Tab | null;
    if (want && tabs.includes(want)) return want;
    return d?.ours && slug ? "squad" : "overview";
  });
  const setTab = (v: Tab) => {
    const qs = new URLSearchParams(route.query);
    qs.set("tab", v);
    location.hash = `#/${route.lang}/${route.parts.map(encodeURIComponent).join("/")}?${qs}`;
  };
  let selected = $state<string | null>(null);                 // grand écran : le joueur dont l'aperçu est ouvert à côté de la liste
  $effect(() => { key; label; selected = null; });
  const pickRow = (e: MouseEvent, r: Row) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0 || !matchMedia("(min-width: 1280px)").matches) return;
    e.preventDefault(); selected = r.key;
  };
  const view = $derived<"squad" | "moves">(tab === "moves" ? "moves" : "squad");          // Effectif (les joueurs) ou Mouvements (arrivées et départs)
  let seasonSheet = $state(false), filterSheet = $state(false);
  const moves = resource(async () => {
    const tt = title, lbl = label, prev = older;
    if (view !== "moves" || !tt || !lbl || !prev?.players || !squad) return null;
    const keyOf = `COALESCE(player_qid, 'name:' || player)`;
    const before = await q(`SELECT ${keyOf} AS key, player, nationality, nat_flag, position FROM squad WHERE club = ? AND season = ?`, [tt, prev.season]);
    const nowKeys = new Set(squad.rows.map((r: Row) => r.key));
    const beforeKeys = new Set(before.map((r: Row) => r.key));
    const arrivals = squad.rows.filter((r: Row) => !beforeKeys.has(r.key));
    const departures = before.filter((r: Row) => !nowKeys.has(r.key));
    const kept = squad.rows.length - arrivals.length;
    // D'où viennent les arrivées (leur club la saison précédente), où vont les départs (leur club cette saison), quand nous les connaissons.
    const where = async (keys: string[], season: string) => {
      if (!keys.length) return new Map<string, Row>();
      const rows = await q(`SELECT ${keyOf} AS key, club, competition FROM squad WHERE season = ? AND club <> ? AND ${keyOf} IN (${keys.map(() => "?").join(",")})`, [season, tt, ...keys]);
      return new Map(rows.map((r: Row) => [r.key as string, r]));
    };
    const from = await where(arrivals.map((r: Row) => r.key), prev.season);
    const dest = await where(departures.map((r: Row) => r.key as string), lbl);
    return { prev: prev.season, arrivals, departures, kept, from, dest };
  });
  const mv = $derived(moves.data);

  // Filtres de l'effectif (remis à zéro quand on change de saison).
  const POS = ["GK", "DF", "MF", "FW", null] as const;
  let fNat = $state("");
  let fLoan = $state(false);
  const nFilters = $derived((fNat ? 1 : 0) + (fLoan ? 1 : 0));
  $effect(() => { label; fNat = ""; fLoan = false; });

  const rows = $derived((squad?.rows ?? []) as Row[]);
  const ageOf = (r: Row) => (label ? seasonAge(r.birth_date, r.precision, label) : null);
  const stats = $derived.by(() => {
    const ages = rows.map(ageOf).filter((a): a is number => a != null);
    const home = d?.ours ? countryOf(d.ours.country_code).flag : null;
    const known = rows.filter((r) => r.nat_flag);
    const foreign = home ? known.filter((r) => r.nat_flag !== home).length : 0;
    return {
      n: rows.length,
      age: ages.length ? ages.reduce((a, b) => a + b, 0) / ages.length : null,
      foreignPct: home && known.length ? Math.round((100 * foreign) / known.length) : null,
      nats: new Set(known.map((r) => r.nat_flag)).size,
    };
  });
  const natOptions = $derived.by(() => {
    const m = new Map<string, { label: string; n: number }>();
    for (const r of rows) if (r.nationality) m.set(r.nationality, { label: r.nationality, n: (m.get(r.nationality)?.n ?? 0) + 1 });
    return [...m.values()].sort((a, b) => b.n - a.n || a.label.localeCompare(b.label, app.lang));
  });
  const shown = $derived(rows.filter((r) => (!fNat || r.nationality === fNat) && (!fLoan || r.stint === "loan_in")));
  const hasLoans = $derived(rows.some((r) => r.stint === "loan_in"));
  const filtered = $derived(Boolean(fNat || fLoan));

  // Mode d'affichage : liste (par défaut) ou cartes, mémorisé dans le navigateur du visiteur.
  const MODE_KEY = "openfootballbase.squadView";
  let mode: "list" | "cards" = $state((() => { try { return localStorage.getItem(MODE_KEY) === "cards" ? "cards" : "list"; } catch { return "list"; } })());
  const setMode = (m: "list" | "cards") => { mode = m; try { localStorage.setItem(MODE_KEY, m); } catch { /* stockage indisponible */ } };
  const exportCsv = () => downloadCsv(`${seasonSlug(label ?? "")}-${(title ?? key).replace(/[^\w]+/g, "-")}.csv`,
    ["season", "club", "shirt_number", "player", "player_qid", "position", "nationality", "age"],
    shown.map((r) => [label, title, r.shirt_number, r.player, String(r.key).startsWith("name:") ? "" : r.key, r.position, r.nationality, ageOf(r)]));
  /** Page Wikipedia à créer ou compléter quand la saison n'a pas d'effectif : la recherche de la page de la saison du club. */
  const fillUrl = $derived(label && title ? `https://en.wikipedia.org/w/index.php?search=${encodeURIComponent(`${label.replace("/", "–")} ${title.replace(/ F\.C\.$/, "")} season`)}` : null);

  // Championnat de la fiche : cliquable quand on le couvre (même nom qu'une de nos compétitions, sinon celle de sa saison la plus récente).
  const normName = (x: unknown) => String(x ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  const leagueCode = $derived.by(() => {
    const w = d?.w;
    if (!w?.league) return null;
    const n = normName(w.league);
    const byName = [...app.comps.values()].find((c) => normName(c.name_en) === n || normName(c.name_fr) === n);
    if (byName) return byName.code as string;
    // Wikidata nomme la ligue autrement (« championnat de France de football ») : on prend la compétition de sa saison la plus récente.
    return d?.seasons[0]?.competition && app.comps.has(d.seasons[0].competition) ? (d.seasons[0].competition as string) : null;
  });
  const info = $derived.by(() => {
    const w = d?.w;
    if (!w) return [] as { label: string; value: string; href?: string; to?: string }[];
    const items: { label: string; value: string; href?: string; to?: string }[] = [];
    const add = (label: string, value: string | null | undefined, href?: string, to?: string) => { if (value) items.push({ label, value, href, to }); };
    add(t("nickname"), w.nickname);
    add(t("city"), w.city);
    add(t("founded"), fmtFounded(w.founded));
    add(t("stadium"), w.stadium ? w.stadium + (w.stadium_capacity ? ` · ${Number(w.stadium_capacity).toLocaleString(app.lang)} ${t("capacity")}` : "") : "");
    add(t("league"), w.league ? w.league + (w.division ? ` · ${t("division")} ${w.division}` : "") : "", undefined, leagueCode ? href("competition", leagueCode) : undefined);
    add(t("website"), w.website ? String(w.website).replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "") : "", w.website);
    if (w.lat != null && w.lon != null)
      add("GPS", `${t("map")} · ${w.lat.toFixed(3)}, ${w.lon.toFixed(3)}`, `https://www.openstreetmap.org/?mlat=${w.lat}&mlon=${w.lon}#map=14/${w.lat}/${w.lon}`);
    return items;
  });
  const external = $derived(d?.w ? [
    d.w.transfermarkt_id && ["Transfermarkt", `https://www.transfermarkt.com/-/startseite/verein/${enc(d.w.transfermarkt_id)}`],
    d.w.fbref_id && ["FBref", `https://fbref.com/en/squads/${enc(d.w.fbref_id)}/`],
    d.w.worldfootball_id && ["WorldFootball", `https://www.worldfootball.net/teams/${enc(d.w.worldfootball_id)}/`],
  ].filter(Boolean) as [string, string][] : []);
</script>

<Crumbs trail={d?.ours?.country_code ? [{ label: country, to: href("country", d.ours.country_code) }] : []} />
{#if res.loading && !d}
  <Spinner />
{:else if res.error}
  <ErrorBox message={res.error} />
{:else if !d}
  <p class="text-warn">{t("clubNotFound")}</p>
{:else}
  <!-- Mobile : une carte compacte (logo et nom côte à côte, palmarès sur une ligne qui défile) sur fond neutre avec la bande de couleur du club ; la teinte pleine revient dès « sm ». -->
  <header class="card overflow-hidden sm:[background:var(--tint)]" style:--tint={kit[0] ? `color-mix(in oklab, ${kit[0]} 11%, var(--surface))` : "var(--surface)"}>
    {#if kit[0]}<div class="flex h-1.5" aria-hidden="true"><span class="flex-1" style:background={kit[0]}></span>{#if kit[1]}<span class="w-1/3" style:background={kit[1]}></span>{/if}</div>{/if}
    <div class="grid grid-cols-[auto_minmax(0,1fr)] items-center gap-x-3 gap-y-3 p-4 sm:flex sm:flex-row sm:items-center sm:gap-4 sm:p-6">
      <div class="row-span-2 grid size-14 shrink-0 place-items-center rounded-lg bg-surface/80 p-1.5 max-sm:[&_img]:!size-11 max-sm:[&_svg]:!size-11 sm:row-span-1 sm:size-24 sm:rounded-xl sm:p-2"><Logo club={logo} size={72} /></div>
      <div class="contents min-w-0 sm:block">
        <h1 class="text-3xl font-extrabold leading-tight tracking-tight text-balance sm:text-6xl sm:leading-none">{name}</h1>
        {#if sub}<p class="mt-1 hidden text-muted sm:block">{sub}</p>{/if}
        <p class="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-sm text-muted sm:mt-2 sm:gap-x-4 sm:gap-y-1">
          <span class="flex items-center gap-1.5 font-medium text-fg"><Flag code={flag} label={country} /> {country}</span>
          {#if current}<a class="link" href={href("competition", current.competition, seasonSlug(current.season))}>{compName(current.competition)}</a>{/if}
          {#each (extra.data ?? []).filter((c) => c !== current?.competition) as c}<a class="link max-sm:hidden" href={href("competition", c, seasonSlug(label ?? ""))}>{compName(c)}</a>{/each}
        </p>
      </div>
      <div class="col-span-2 sm:col-span-1 sm:ml-auto sm:self-start"><FollowButton item={{ kind: "club", id: key, label: name, sub: country, path: `club/${enc(key)}` }} /></div>
    </div>
  </header>

  <!-- Une seule barre collante : les onglets, puis (Effectif, Mouvements) la saison et, pour les joueurs, les filtres et l'affichage. -->
  <div class="sticky top-[calc(3.5rem+env(safe-area-inset-top))] z-20 -mx-4 mt-3 border-b border-line/60 bg-bg/95 px-4 py-2 backdrop-blur lg:top-0 lg:mx-0 lg:px-0">
    {#if tabs.length > 1}
      <Segmented label={t("clubViews")} idPrefix="ctab" value={tab} onselect={setTab}
        items={tabs.map((v) => ({ key: v, label: t(v === "overview" ? "clubOverview" : v === "squad" ? "sqTab" : v === "moves" ? "mvTab" : v === "coaches" ? "coaches" : "honours") }))} />
    {/if}
    {#if (tab === "squad" || tab === "moves") && d.ours && seasonList.length}
      <div class="mt-2 flex items-center gap-2">
        <div class="flex shrink-0 items-center gap-1" role="group" aria-label={t("changeSeason")}>
          {#if older}<a class="grid size-10 place-items-center rounded-xl border border-line bg-surface text-muted no-underline transition hover:bg-surface-2 hover:text-fg max-sm:hidden sm:size-9" href={to(older.season)} aria-label="{t('prevSeason')} {older.season}">‹</a>
          {:else}<span class="grid size-10 place-items-center rounded-xl border border-line/60 text-muted/40 max-sm:hidden sm:size-9" aria-hidden="true">‹</span>{/if}
          <button type="button" class="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-surface px-3.5 text-sm font-semibold tabular-nums transition hover:bg-surface-2 sm:h-9" aria-haspopup="dialog" onclick={() => (seasonSheet = true)}>
            {label}{#if level(current ?? {})}<span class="text-[0.6875rem] font-bold text-accent">D{level(current ?? {})}</span>{/if}
            <svg viewBox="0 0 24 24" class="size-4 text-muted" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
          </button>
          {#if newer}<a class="grid size-10 place-items-center rounded-xl border border-line bg-surface text-muted no-underline transition hover:bg-surface-2 hover:text-fg max-sm:hidden sm:size-9" href={to(newer.season)} aria-label="{t('nextSeason')} {newer.season}">›</a>
          {:else}<span class="grid size-10 place-items-center rounded-xl border border-line/60 text-muted/40 max-sm:hidden sm:size-9" aria-hidden="true">›</span>{/if}
        </div>
        {#if tab === "squad"}
          <div class="ml-auto flex min-w-0 items-center gap-2">
            {#if natOptions.length > 1}
              <select class="h-9 min-w-0 rounded-xl border border-line bg-surface px-3 text-sm max-sm:hidden" bind:value={fNat} aria-label={t("sqFilterNat")}>
                <option value="">{t("sqAllNats")}</option>
                {#each natOptions as n (n.label)}<option value={n.label}>{n.label} ({n.n})</option>{/each}
              </select>
            {/if}
            {#if hasLoans}
              <button type="button" class="h-9 shrink-0 whitespace-nowrap rounded-xl border px-3 text-sm font-medium transition max-sm:hidden {fLoan ? 'border-accent bg-accent text-accent-fg' : 'border-line bg-surface text-fg hover:bg-surface-2'}" aria-pressed={fLoan} onclick={() => (fLoan = !fLoan)}>{t("sqLoanOnly")}</button>
            {/if}
            {#if natOptions.length > 1 || hasLoans}
              <button type="button" class="relative grid size-10 shrink-0 place-items-center rounded-xl border border-line bg-surface text-muted transition hover:text-fg sm:hidden" aria-haspopup="dialog" aria-label={t("filters")} onclick={() => (filterSheet = true)}>
                <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h10M18 7h2M4 17h2M10 17h10" /><circle cx="16" cy="7" r="2" /><circle cx="8" cy="17" r="2" /></svg>
                {#if nFilters}<span class="absolute -right-1 -top-1 grid size-4 place-items-center rounded-full bg-accent text-[0.625rem] font-bold text-accent-fg">{nFilters}</span>{/if}
              </button>
            {/if}
            <div class="inline-flex shrink-0 rounded-xl border border-line bg-surface p-0.5" role="group" aria-label={t("viewMode")}>
              {#each [["list", "viewList"], ["cards", "viewCards"]] as [m, k]}
                <button type="button" class="grid size-9 place-items-center rounded-[0.6rem] transition sm:size-8 {mode === m ? 'bg-accent text-accent-fg' : 'text-muted hover:text-fg'}" aria-pressed={mode === m} aria-label={t(k)} title={t(k)}
                  onclick={() => setMode(m as "list" | "cards")}>
                  <svg viewBox="0 0 24 24" class="size-[18px]" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    {#if m === "list"}<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01" />{:else}<rect x="4" y="4" width="6.5" height="6.5" rx="1.2" /><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.2" /><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.2" /><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.2" />{/if}
                  </svg>
                </button>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <Sheet open={seasonSheet} onclose={() => (seasonSheet = false)} title={t("seasonTab")}>
    <ul>
      {#each seasonList as s (s.season)}
        <li><a class="flex min-h-12 items-center gap-3 rounded-xl px-3 no-underline transition hover:bg-surface-2 {s.season === label ? 'bg-accent-soft text-accent' : ''}" href={to(s.season)} aria-current={s.season === label ? "true" : undefined} onclick={() => (seasonSheet = false)}>
          <span class="display w-20 text-lg font-semibold tabular-nums">{s.season}</span>
          <span class="min-w-0 flex-1 truncate text-sm text-muted">{compName(s.competition)}</span>
          <span class="shrink-0 text-xs font-bold {level(s) === 1 ? 'text-accent' : 'text-muted'}">{level(s) ? `D${level(s)}` : "·"}{#if !s.players} <span aria-label={t("unresolved")}>∅</span>{/if}</span>
        </a></li>
      {/each}
    </ul>
  </Sheet>
  <Sheet open={filterSheet} onclose={() => (filterSheet = false)} title={t("filters")}>
    <div class="grid gap-3 px-3 pb-2">
      {#if natOptions.length > 1}
        <label class="grid gap-1.5 text-sm font-semibold">{t("sqFilterNat")}
          <select class="h-11 rounded-xl border border-line bg-bg px-3 text-base font-normal" bind:value={fNat}>
            <option value="">{t("sqAllNats")}</option>
            {#each natOptions as n (n.label)}<option value={n.label}>{n.label} ({n.n})</option>{/each}
          </select>
        </label>
      {/if}
      {#if hasLoans}
        <button type="button" class="flex min-h-11 items-center justify-between rounded-xl border px-4 text-left text-base font-medium {fLoan ? 'border-accent bg-accent-soft text-accent' : 'border-line'}" aria-pressed={fLoan} onclick={() => (fLoan = !fLoan)}>{t("sqLoanOnly")}<span aria-hidden="true">{fLoan ? "✓" : ""}</span></button>
      {/if}
      <div class="mt-1 flex gap-2">
        <button type="button" class="btn-ghost min-h-11 flex-1 justify-center" onclick={() => { fNat = ""; fLoan = false; }}>{t("sqReset")}</button>
        <button type="button" class="btn min-h-11 flex-1 justify-center" onclick={() => (filterSheet = false)}>{shown.length} {t("srcPlayers")}</button>
      </div>
    </div>
  </Sheet>

  <div class="mt-6">
    {#if tab === "squad" || tab === "moves"}
    <div class="min-w-0">
      {#if !d.ours}
        <p class="card border-info/30 bg-info-soft p-4 text-info">{t("noSquadsHere")}</p>
      {:else if sq.loading && !squad}
        <Spinner />
      {:else if sq.error}
        <ErrorBox message={sq.error} />
      {:else if squad && !rows.length}
        <div class="card border-info/30 bg-info-soft p-4 text-info">
          <p>{t("noSquad")}{squad.cs?.known_gap_reason ? ` — ${t("gapReason")} : ${squad.cs.known_gap_reason}` : ""}</p>
          {#if fillUrl}<p class="mt-2 text-sm">{t("fillIntro")} <a class="link" href={fillUrl} target="_blank" rel="noopener">{t("fillCta")}</a></p>{/if}
        </div>
      {:else if squad}
        {#snippet stint(r: Row)}
          {#if r.stint === "loan_in"}<Badge kind="info">{t("loan_in")}</Badge>{/if}
        {/snippet}



        {#if view === "moves"}
          {#if !older?.players}
            <p class="card p-4 text-muted">{t("mvNoPrev")}</p>
          {:else if moves.loading && !mv}
            <Spinner />
          {:else if mv}
            {#snippet person(r: Row, other: Row | undefined, rel: string)}
              <li class="grid grid-cols-[1fr_auto] items-center gap-3 py-1.5">
                <span class="flex min-w-0 items-center gap-2">
                  <Flag code={r.nat_flag} label={r.nationality} />
                  <a class="truncate font-medium hover:text-accent hover:underline" href={href("player", enc(r.key))}>{r.player}</a>
                  {#if r.position}<span class="shrink-0 text-xs text-muted">{r.position}</span>{/if}
                </span>
                {#if other}
                  <span class="flex min-w-0 items-center gap-1.5 text-sm text-muted"><span class="hidden sm:inline">{rel}</span><Logo club={clubOf(other.club)} size={18} />
                    <a class="truncate hover:text-accent hover:underline" href={href("club", enc(other.club), seasonSlug(rel === t("mvFrom") ? mv.prev : label ?? ""))}>{clubName(clubOf(other.club))}</a></span>
                {/if}
              </li>
            {/snippet}
            <p class="text-sm text-muted">{mv.prev} → {label} · <strong class="text-fg">{mv.kept}</strong> {t("mvKept")}</p>
            <div class="mt-3 grid gap-4 xl:grid-cols-2">
              <section class="card p-4" aria-labelledby="mv-in">
                <h2 id="mv-in" class="mb-1 flex items-baseline gap-2 border-b border-line pb-1 text-lg font-bold text-accent">{t("mvArrivals")} <span class="display text-base font-semibold">{mv.arrivals.length}</span></h2>
                {#if mv.arrivals.length}<ul class="divide-y divide-line/60">{#each mv.arrivals as r (r.key)}{@render person(r, mv.from.get(r.key), t("mvFrom"))}{/each}</ul>
                {:else}<p class="py-2 text-sm text-muted">{t("mvNone")}</p>{/if}
              </section>
              <section class="card p-4" aria-labelledby="mv-out">
                <h2 id="mv-out" class="mb-1 flex items-baseline gap-2 border-b border-line pb-1 text-lg font-bold text-warn">{t("mvDepartures")} <span class="display text-base font-semibold">{mv.departures.length}</span></h2>
                {#if mv.departures.length}<ul class="divide-y divide-line/60">{#each mv.departures as r (r.key)}{@render person(r, mv.dest.get(r.key), t("mvTo"))}{/each}</ul>
                {:else}<p class="py-2 text-sm text-muted">{t("mvNone")}</p>{/if}
              </section>
            </div>
            <p class="mt-3 text-sm text-muted">{t("mvNote")}</p>
          {/if}
        {:else}
        {#if partial}
          <p class="mb-4 rounded-lg border border-line bg-surface-2 px-4 py-3 text-sm" role="note"><strong>{t("partialTitle")}</strong> {t("partialBody")}</p>
        {/if}
        <!-- Chiffres de l'effectif : une ligne de résumé -->
        <p class="flex flex-wrap items-baseline gap-x-4 gap-y-0.5 text-sm text-muted">
          <span><strong class="font-semibold tabular-nums text-fg">{stats.n}</strong> {t("srcPlayers")}</span>
          {#if stats.age != null}<span><strong class="font-semibold tabular-nums text-fg">{stats.age.toLocaleString(app.lang, { maximumFractionDigits: 1 })}</strong> {t("sqAge")}</span>{/if}
          {#if stats.foreignPct != null}<span title={t("sqForeignTip")}><strong class="font-semibold tabular-nums text-fg">{stats.foreignPct} %</strong> {t("sqForeign")}</span>{/if}
          {#if stats.nats}<span class="max-sm:hidden"><strong class="font-semibold tabular-nums text-fg">{stats.nats}</strong> {t("sqNats")}</span>{/if}
          {#if filtered}<span class="tabular-nums" aria-live="polite">· {shown.length} / {rows.length} {t("srcPlayers")}</span>
            <button type="button" class="underline hover:text-fg" onclick={() => { fNat = ""; fLoan = false; }}>{t("sqReset")}</button>{/if}
        </p>

        {#if !shown.length}
          <p class="card mt-4 p-4 text-muted">{t("sqNoMatch")}</p>
        {:else if mode === "list"}
          {@const sel = selected ? shown.find((r) => r.key === selected) : null}
          <div class="mt-4 grid items-start gap-4 {sel ? 'xl:grid-cols-[minmax(0,1fr)_22rem]' : ''}">
          <div class="card gap-x-8 p-4 sm:p-5 {sel ? '' : 'xl:columns-2'}">
            {#each POS as pos}
              {@const group = shown.filter((r) => (r.position || null) === pos)}
              {#if group.length}
                <section class="mb-5 break-inside-avoid last:mb-0">
                  <h2 class="mb-1 flex items-baseline gap-2 border-b border-line pb-1 text-lg font-bold">
                    {pos ? t(pos) : t("unknownPos")} <span class="display text-base font-semibold text-muted">{group.length}</span>
                  </h2>
                  <ul class="divide-y divide-line/60">
                    {#each group as r (r.key + r.shirt_number)}
                      {@const age = ageOf(r)}
                      <li class="grid grid-cols-[2.25rem_1fr_auto] items-center gap-3 py-1.5 hover:bg-surface-2">
                        <span class="display text-right text-2xl font-bold text-muted">{r.shirt_number ?? ""}</span>
                        <span class="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
                          <Flag code={r.nat_flag} label={r.nationality} />
                          <a class="font-medium hover:text-accent hover:underline {selected === r.key ? 'text-accent' : ''}" href={href("player", enc(r.key))} aria-current={selected === r.key ? "true" : undefined} onclick={(e) => pickRow(e, r)}>{r.player}</a>
                          {@render stint(r)}
                        </span>
                        <span class="text-sm text-muted tabular-nums" title={t("ageTip")}>{age != null ? `${age} ${t("ageYears")}` : ""}</span>
                      </li>
                    {/each}
                  </ul>
                </section>
              {/if}
            {/each}
          </div>
          {#if sel}<PlayerPreview row={sel} onclose={() => (selected = null)} />{:else}<p class="card hidden p-4 text-sm text-muted xl:block xl:self-start">{t("pvHint")}</p>{/if}
          </div>
        {:else}
          <div class="mt-4 space-y-6">
            {#each POS as pos}
              {@const group = shown.filter((r) => (r.position || null) === pos)}
              {#if group.length}
                <section>
                  <h2 class="mb-2 flex items-baseline gap-2 text-xl font-bold">{pos ? t(pos) : t("unknownPos")} <span class="display text-base font-semibold text-muted">{group.length}</span></h2>
                  <ul class="grid grid-cols-[repeat(auto-fill,minmax(9.5rem,1fr))] gap-2">
                    {#each group as r (r.key + r.shirt_number)}
                      {@const age = ageOf(r)}
                      <li class="card relative min-h-20 overflow-hidden p-3 hover:bg-surface-2">
                        <span class="display pointer-events-none absolute -top-2 right-2 text-6xl font-bold leading-none text-surface-2" aria-hidden="true">{r.shirt_number ?? ""}</span>
                        <a class="relative mt-4 block font-medium after:absolute after:inset-[-0.75rem] hover:text-accent hover:underline" href={href("player", enc(r.key))}>{r.player}</a>
                        <span class="relative mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted">
                          <Flag code={r.nat_flag} label={r.nationality} />
                          {#if age != null}<span class="tabular-nums" title={t("ageTip")}>{age} {t("ageYears")}</span>{/if}
                          {@render stint(r)}
                        </span>
                      </li>
                    {/each}
                  </ul>
                </section>
              {/if}
            {/each}
          </div>
        {/if}

        {/if}

        <p class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          <button type="button" class="link" onclick={exportCsv}>{t("dlCsv")} ({shown.length})</button>
          <a class="link" href={RELEASES_URL} target="_blank" rel="noopener">{t("dlAll")}</a>
        </p>

        <!-- Sources de cet effectif -->
        {#if squad.sources.length || squad.cs?.source_lang}
          <p class="mt-4 text-sm text-muted">
            {#if squad.sources.length}
              {t(squad.sources.length > 1 ? "sourcesLabel" : "sourceLabel")} :
              {#each squad.sources as src, i}{#if i}{", "}{/if}<a class="link" href={wikiUrl(src.source_lang, src.source_title)} hreflang={src.source_lang} target="_blank" rel="noopener">{src.source_lang.toUpperCase()}</a>
                <span class="text-xs">({src.players_read} {t("srcPlayers")}{#if i && src.players_added}, +{src.players_added} {t("srcAdded")}{/if})</span>{/each}
            {:else}
              {t("sourceLabel")} : <a class="link" href={wikiUrl(squad.cs.source_lang, squad.cs.source_title)} hreflang={squad.cs.source_lang} target="_blank" rel="noopener">{squad.cs.source_title}</a> ({squad.cs.source_lang.toUpperCase()})
            {/if}
          </p>
        {/if}
      {/if}
    </div>
    {/if}

    <!-- Palmarès et fiche du club : deux onglets, plus une colonne latérale -->
    {#if tab === "honours"}
      <div class="min-w-0 max-w-3xl">
      {#if honours.loading && !honours.data}<Spinner />{/if}
      {#if honours.data?.length}
        {@const total = honours.data.reduce((n, h) => n + h.years.length, 0)}
        <h2 id="honours-section" class="mb-2 flex scroll-mt-20 items-center gap-2 text-xl font-bold"><Trophy size={20} />{t("honours")}</h2>
        <div class="card mb-6 px-4 py-3">
          <div class="flex items-baseline gap-2 border-b border-line pb-2"><span class="display text-3xl font-extrabold leading-none tabular-nums text-accent">{total}</span><span class="font-semibold">{total > 1 ? t("titlesN") : t("titleN")}</span></div>
          {#each KINDS as kind (kind)}
            {@const rows = honours.data.filter((h) => compKind(h.code) === kind)}
            {#if rows.length}
              <h3 class="mt-3 flex items-baseline justify-between text-xs font-semibold uppercase tracking-wide text-muted"><span>{t("kind_" + kind)}</span><span class="tabular-nums">{rows.reduce((n, h) => n + h.years.length, 0)}</span></h3>
              <ul class="divide-y divide-line/60">
                {#each rows as h (h.code)}
                  <li class="py-2.5">
                    <details class="group">
                      <summary class="flex cursor-pointer list-none items-center gap-3 [&::-webkit-details-marker]:hidden">
                        <span class="display w-8 text-2xl font-bold tabular-nums">{h.years.length}</span>
                        <CompLogo code={h.code} size={32} />
                        <span class="min-w-0 flex-1">
                          <a class="line-clamp-2 font-semibold leading-snug no-underline hover:text-accent" href={href("competition", h.code)}>{compName(h.code)}</a>
                          <span class="block truncate text-xs tabular-nums text-muted">{h.years.slice(0, 4).map((y) => titleYear(h.code, y)).join(" · ")}{h.years.length > 4 ? " …" : ""}</span>
                        </span>
                        {#if h.years.length > 4}<span class="text-muted transition group-open:rotate-90" aria-hidden="true">›</span>{/if}
                      </summary>
                      {#if h.years.length > 4}<p class="mt-1.5 pl-[4.75rem] text-sm leading-relaxed tabular-nums text-muted">{h.years.map((y) => titleYear(h.code, y)).join(" · ")}</p>{/if}
                    </details>
                  </li>
                {/each}
              </ul>
            {/if}
          {/each}
          <p class="max-w-[70ch] border-t border-line pt-2 text-xs text-muted">{t("honoursClubNote")}</p>
        </div>
      {/if}
      
      </div>
    {:else if tab === "coaches"}
      {#if coaches.data?.length}
      <div class="max-w-2xl">
        <h2 class="mb-2 text-xl font-bold">{t("coaches")}</h2>
        <div class="card mb-6 px-4 py-3">
          <ul class="divide-y divide-line/60">
            {#each coaches.data as k, i (i)}          <!-- clé = rang : un même entraîneur peut avoir deux mandats qui commencent la même année -->

              <li class="flex items-center gap-3 py-2">
                {#if k.flag}<Flag code={k.flag} size={16} />{/if}
                <a class="min-w-0 flex-1 truncate font-medium hover:text-accent hover:underline" href={href("coach", enc(k.qid))}>{k.name}</a>
                <span class="shrink-0 text-sm tabular-nums text-muted">{k.to === k.from ? k.from : `${k.from}–${k.to ?? ""}`}{#if k.to === null}<span class="sr-only"> {t("coachesNow")}</span>{/if}</span>
              </li>
            {/each}
          </ul>
          <p class="border-t border-line pt-2 text-xs text-muted">{t("coachesNote")}</p>
        </div>
      </div>
      {:else}<Spinner />{/if}
    {:else if tab === "overview"}
      <div class="grid gap-8 lg:grid-cols-2 lg:items-start">
        <div class="min-w-0">
          {#if d.ours && label}
            <a class="tile mb-6 max-w-xl" href={to(label)}>
              <span class="min-w-0 flex-1"><span class="block font-semibold">{t("seeSquad")} {label}</span>{#if current}<span class="block text-sm text-muted">{compName(current.competition)}</span>{/if}</span>
              <span class="text-muted" aria-hidden="true">›</span>
            </a>
          {/if}
          <h2 id="about-club" class="mb-3 text-xl font-bold">{t("about_club")}</h2>
      {#if info.length || external.length}
        <dl class="space-y-3 text-sm">
          {#each info as it}
            <div><dt class="eyebrow">{it.label}</dt>
              <dd class="mt-0.5 font-medium">{#if it.to}<a class="link" href={it.to}>{it.value}</a>{:else if it.href}<a class="link break-all" href={it.href} target="_blank" rel="noopener">{it.value}</a>{:else}{it.value}{/if}</dd></div>
          {/each}
          {#if external.length}
            <div><dt class="eyebrow">{t("externalIds")}</dt>
              <dd class="mt-0.5 flex flex-wrap gap-x-4 gap-y-1 font-medium">{#each external as [label, url]}<a class="link" href={url} target="_blank" rel="noopener">{label}</a>{/each}</dd></div>
          {/if}
        </dl>
      {/if}
      <div class="mt-4"><WikiButton urls={d.urls} kind="wikiClub" fallbackKey="wikiLocalOnly" /></div>
    
        </div>
        <div class="min-w-0">
          {#if d.w?.lat != null && d.w?.lon != null}
        <div><ClubMap lat={d.w.lat} lon={d.w.lon} name={name} logo={d.w.logo_url} color={d.w.colors_hex} /></div>
      {/if}
      
        </div>
      </div>
    {/if}
  
  </div>
{/if}
