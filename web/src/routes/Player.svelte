<script lang="ts">
  import { app, href, enc, page, route, t } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { ageAt, clubName, clubOf, isOngoing, natLabel as libNatLabel, nationalTeam, wikiUrl } from "../lib/format";
  import { fold } from "../lib/fold";
  import Badge from "../components/Badge.svelte";
  import Crumbs from "../components/Crumbs.svelte";
  import ErrorBox from "../components/ErrorBox.svelte";
  import Flag from "../components/Flag.svelte";
  import FollowButton from "../components/FollowButton.svelte";
  import Segmented from "../components/Segmented.svelte";
  import Logo from "../components/Logo.svelte";
  import PlayerHonours from "../components/PlayerHonours.svelte";
  import CareerList from "../components/CareerList.svelte";
  import PlayerNow from "../components/PlayerNow.svelte";
  import PlayerStats from "../components/PlayerStats.svelte";
  import Spinner from "../components/Spinner.svelte";
  import WikiButton from "../components/WikiButton.svelte";

  let { key }: { key: string } = $props();
  // Une photo supprimée de Wikimedia depuis la publication des données ne s'affiche pas : on la retire plutôt que d'afficher une image cassée et sa légende.
  let photoFailed = $state(false);
  $effect(() => { key; photoFailed = false; });

  const res = resource(async () => {
    const [p] = await q(`SELECT any_value(player) AS name, any_value(player_qid) AS qid, any_value(link_title) AS link_title,
        arg_max(nat_flag, season) AS flag, arg_max(nationality, season) AS nat,
        arg_max(club, season) AS club, max(season) AS last, arg_max(position, season) AS pos, arg_max(shirt_number, season) AS num, (SELECT max(season) FROM squad) AS latest FROM squad WHERE COALESCE(player_qid, 'name:' || player) = ?`, [key]);
    if (!p || !p.name) return null;
    let birth: any = null;
    if (p.qid && app.has.birth) birth = (await q(`SELECT birth_date, precision FROM birth WHERE player_qid = ?`, [p.qid]))[0] ?? null;
    const career = app.has.career ? await q(`SELECT c.seq, c.start_year, c.end_year, c.years_raw, c.club_name, c.club_link, c.loan, c.apps, c.goals, c.source_title, w.wikidata_qid AS club_qid, w.logo_url AS club_logo, w.colors_hex AS club_colors
        FROM career c LEFT JOIN club w ON ${app.careerHasClubQid ? "w.wikidata_qid = c.club_qid" : "w.wikipedia_title = c.club_link"} WHERE COALESCE(c.player_qid, 'name:' || c.player) = ? ORDER BY c.seq`, [key]) : [];
    let profile: any = app.has.player_profile
      ? (await q(`SELECT full_name, birth_place, height_cm, photo_caption, photo_url, photo_page, photo_license, photo_author FROM player_profile
          WHERE COALESCE(player_qid, 'name:' || player) = ?`, [key]))[0] ?? null : null;
    if (p.qid && app.has.player_openfootball) {                    // taille et lieu de naissance que Wikipedia n'a pas (OpenFootball, relié par nom + date de naissance)
      const o = (await q(`SELECT height_cm, birth_place FROM player_openfootball WHERE player_qid = ?`, [p.qid]))[0];
      if (o) profile = { ...(profile ?? {}), birth_place: profile?.birth_place ?? o.birth_place, height_cm: profile?.height_cm ?? o.height_cm };
    }
    const national = app.has.national ? await q(`SELECT years_raw, team_name, team_link, caps, goals FROM national
        WHERE COALESCE(player_qid, 'name:' || player) = ? ORDER BY seq`, [key]) : [];
    const statClub = app.has.stat_club ? await q(`SELECT c.seq, c.club, c.club_link, c.club_qid, w.logo_url AS club_logo, w.colors_hex AS club_colors, c.season, c.division,
        c.competition_group, c.apps, c.goals, c.assists FROM stat_club c LEFT JOIN club w ON w.wikidata_qid = c.club_qid
        WHERE COALESCE(c.player_qid, 'name:' || c.player) = ? ORDER BY c.seq`, [key]) : [];
    const statNat = app.has.stat_national ? await q(`SELECT seq, team, team_link, year, competition_group, apps, goals FROM stat_national
        WHERE COALESCE(player_qid, 'name:' || player) = ? ORDER BY seq`, [key]) : [];
    const statSource = statClub.length && app.has.stat_source ? (await q(`SELECT source_title FROM stat_source WHERE COALESCE(player_qid, 'name:' || player) = ?`, [key]))[0]?.source_title : undefined;
    const urls: Record<string, string> = {};
    if (p.qid && app.has.entity_wiki) for (const r of await q(`SELECT lang, title FROM entity_wiki WHERE qid = ?`, [p.qid])) urls[r.lang] = wikiUrl(r.lang, r.title);
    if (!urls.en && p.link_title) urls.en = wikiUrl("en", p.link_title);
    return { p, birth, profile, career, national, statClub, statNat, statSource, urls };
  });
  const d = $derived(res.data);
  $effect(() => { page.name = d?.p?.name ?? null; return () => { page.name = null; }; });         // titre de l'onglet : le nom du joueur
  $effect(() => { d?.profile?.photo_url; tallPhoto = false; });       // chaque photo est mesurée à son chargement : pas d'héritage de la fiche précédente
  let tallPhoto = $state(false);        // photo d'infobox en pied : plus haute que 1,45 fois sa largeur (le cadre est à 1,25)

  // Nationalité : nom du pays dans la langue de l'app quand le drapeau est un code ISO (sinon le texte publié).
  const natLabel = $derived(d?.p.flag ? libNatLabel(d.p.flag, d.p.nat ?? "") : d?.p.nat ?? "");
  const born = $derived.by(() => {
    const b = d?.birth;
    if (!b) return "";
    const day = new Date(b.birth_date + "T00:00:00");
    if (b.precision >= 11) {
      const n = new Date();
      const age = ageAt(b.birth_date, n.getFullYear(), n.getMonth() + 1, n.getDate());
      return `${t("born")} ${day.toLocaleDateString(app.lang, { day: "numeric", month: "long", year: "numeric" })}, ${age} ${t("yearsOld")}`;
    }
    return `${t("bornIn")} ${day.getFullYear()}`;
  });
  // Téléphone : l'âge seul (« 39 ans »), ou l'année quand le jour n'est pas connu ; la date complète reste sur grand écran.
  const bornShort = $derived.by(() => {
    const b = d?.birth;
    if (!b) return "";
    if (b.precision < 11) return `${t("bornIn")} ${new Date(b.birth_date + "T00:00:00").getFullYear()}`;
    const n = new Date();
    return `${ageAt(b.birth_date, n.getFullYear(), n.getMonth() + 1, n.getDate())} ${t("yearsOld")}`;
  });
  const heightText = $derived(d?.profile?.height_cm ? `${(d.profile.height_cm / 100).toLocaleString(app.lang, { minimumFractionDigits: 2 })} m` : "");
  // Les faits d'un coup d'œil sous l'en-tête : pays, âge, taille, numéro et poste (ceux de la dernière saison listée, donnés comme actuels seulement s'ils le sont), lieu de naissance.
  const facts = $derived.by(() => {
    if (!d) return [] as { k: string; label: string; value: string; sub?: string; flag?: string | null; accent?: boolean }[];
    const out: { k: string; label: string; value: string; sub?: string; flag?: string | null; accent?: boolean }[] = [];
    if (d.p.flag || d.p.nat) out.push({ k: "nat", label: t("country"), value: natLabel, flag: d.p.flag ?? null });
    const b = d.birth;
    if (b) {
      const day = new Date(b.birth_date + "T00:00:00");
      if (b.precision >= 11) out.push({ k: "age", label: `${t("born")} ${day.toLocaleDateString(app.lang, { day: "numeric", month: "long", year: "numeric" })}`, value: bornShort });
      else out.push({ k: "age", label: t("factAge"), value: bornShort });
    }
    if (d.profile?.height_cm) out.push({ k: "h", label: t("heightLabel"), value: heightText });
    const now = d.p.last === d.p.latest;
    if (now && d.p.num) out.push({ k: "num", label: t("factNumber"), value: String(d.p.num) });
    if (d.p.pos) out.push({ k: "pos", label: t("position"), value: t("pos1_" + d.p.pos) });
    if (d.profile?.birth_place) out.push({ k: "bp", label: t("birthPlace"), value: d.profile.birth_place });
    if (totals) { out.unshift({ k: "goals", label: t("sumGoals"), value: String(totals.goals), accent: true }); out.unshift({ k: "apps", label: t("sumApps"), value: String(totals.apps), accent: true }); }
    return out;
  });
  const kit = $derived((String(d?.p.club ? clubOf(d.p.club).colors_hex ?? "" : "").split(/\s*\|\s*/)).filter((c: string) => /^#[0-9a-fA-F]{6}$/.test(c)));
  const isPhone = $derived(typeof matchMedia === "function" && matchMedia("(max-width: 639px)").matches);
  // Sélection A uniquement (les équipes de jeunes ont leurs propres lignes dans le tableau).
  const senior = $derived(d?.national.find((r) => !/\bU\d{2}\b|under/i.test(r.team_name)) ?? null);
  // Frise : une barre par passage, positionnée sur l'axe des années ; les passages simultanés (prêt, équipe réserve) passent sur une autre ligne.
  const timeline = $derived.by(() => {
    // Les années de l'infobox sont des années de calendrier : « 2018–2024 » = de l'été 2018 à l'été 2024, soit 6 ans ; un passage d'une seule année vaut 1 an.
    const spells = (d?.career ?? []).filter((r: any) => r.start_year != null).map((r: any) => ({ ...r, dur: Math.max(1, (r.end_year ?? new Date().getFullYear()) - r.start_year) }));
    if (spells.length < 2) return null;
    const min = Math.min(...spells.map((r: any) => r.start_year)), max = Math.max(...spells.map((r: any) => r.start_year + r.dur));
    const span = Math.max(1, max - min);
    const lanes: number[] = [];                                   // fin du dernier passage de chaque ligne
    const bars = [...spells].sort((a: any, b: any) => a.start_year - b.start_year || a.dur - b.dur).map((r: any) => {
      let lane = lanes.findIndex((e) => e <= r.start_year);
      if (lane < 0) { lane = lanes.length; lanes.push(0); }
      lanes[lane] = r.start_year + r.dur;
      return { ...r, lane, left: (100 * (r.start_year - min)) / span, width: Math.max(3, (100 * r.dur) / span) };
    });
    const step = span > 14 ? 5 : span > 8 ? 2 : 1;
    const ticks = Array.from({ length: Math.ceil(span / step) + 1 }, (_, i) => min + i * step).filter((y) => y <= max).map((y) => ({ y, left: (100 * (y - min)) / span }));
    return { bars, lanes: lanes.length, ticks };
  });
  // Vue du parcours : tableau (par défaut) ou frise, au choix du visiteur, mémorisée dans son navigateur.
  const VIEW_KEY = "openfootballbase.careerView";
  let careerView: "table" | "timeline" = $state((() => { try { return localStorage.getItem(VIEW_KEY) === "timeline" ? "timeline" : "table"; } catch { return "table"; } })());
  const setCareerView = (v: "table" | "timeline") => { careerView = v; try { localStorage.setItem(VIEW_KEY, v); } catch { /* stockage indisponible */ } };
  const sum = (rows: any[], k: "apps" | "goals") => rows.reduce((n, r) => n + (r[k] ?? 0), 0);
  // Résumé de carrière : clubs (toutes les lignes de l'infobox, prêts compris) + sélection A. Pas de passes : Wikipedia ne les publie pas.
  const totals = $derived.by(() => {
    if (!d || (!d.career.length && !senior && !d.statClub.length)) return null;
    // Le tableau « Career statistics » (toutes compétitions) prime sur l'infobox (championnat seulement) quand il existe.
    const useStats = d.statClub.length > 0;
    const clubApps = sum(useStats ? d.statClub : d.career, "apps"), clubGoals = sum(useStats ? d.statClub : d.career, "goals");
    const natApps = senior?.caps ?? 0, natGoals = senior?.goals ?? 0;
    return { apps: clubApps + natApps, goals: clubGoals + natGoals, clubApps, clubGoals, natApps, natGoals, hasNat: !!senior };
  });

  // Trois vues : Parcours (clubs puis sélections), Stats et Palmarès. L'onglet est dans l'adresse (`?tab=`) : partageable, et le retour du navigateur le restitue.
  // Une vue sans donnée n'a pas d'onglet ; le palmarès se charge à part (PlayerHonours) et signale par `honoursHas` s'il a quelque chose à montrer.
  type Tab = "path" | "stats" | "honours";
  let honoursHas = $state(false);
  $effect(() => { key; honoursHas = false; });
  const tabs = $derived<Tab[]>(["path", ...(d?.statClub.length ? (["stats"] as Tab[]) : []), ...(honoursHas ? (["honours"] as Tab[]) : [])]);
  const tab = $derived.by<Tab>(() => {
    const want = route.query.get("tab") as Tab | null;
    return want && tabs.includes(want) ? want : "path";
  });
  const setTab = (v: Tab) => {
    const qs = new URLSearchParams(route.query);
    qs.set("tab", v);
    location.hash = `#/${route.lang}/${route.parts.map(encodeURIComponent).join("/")}?${qs}`;
  };
</script>

<div class="max-sm:hidden"><Crumbs /></div>
{#if res.loading && !d}
  <Spinner />
{:else if res.error}
  <ErrorBox message={res.error} />
{:else if !d}
  <p class="text-warn">{t("noResult")}</p>
{:else}
  <!-- Un seul bandeau, sur le modèle de la fiche club : la couleur du club en liseré, l'identité (photo, nom, club) puis les faits en valeur d'abord, libellé dessous. -->
  <header class="card overflow-hidden">
    {#if kit[0]}<div class="flex h-1.5" aria-hidden="true"><span class="flex-1" style:background={kit[0]}></span>{#if kit[1]}<span class="w-1/3" style:background={kit[1]}></span>{/if}</div>{/if}
    <div class="flex flex-wrap items-center gap-x-5 gap-y-3 p-4 sm:p-6" style:background={kit[0] ? `color-mix(in oklab, ${kit[0]} 9%, var(--surface))` : "var(--surface)"}>
      {#if d.profile?.photo_url && !photoFailed}
        <!-- Cadre carré calé sur le haut : le visage est presque toujours en haut de l'image. -->
        <img class="size-20 shrink-0 rounded-2xl border border-line bg-surface-2 object-cover sm:size-28" style:object-position="50% 12%" src={d.profile.photo_url} alt={d.profile.photo_caption || d.p.name} loading="lazy" width="112" height="112"
          onerror={() => (photoFailed = true)} />
      {/if}
      <div class="min-w-0 flex-1">
        <h1 class="text-2xl font-extrabold leading-tight tracking-tight sm:text-4xl">{d.p.name}</h1>
        {#if d.p.club}
          {@const c = clubOf(d.p.club)}
          <p class="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm sm:text-base">
            <a class="inline-flex min-h-8 items-center gap-2 font-semibold no-underline hover:underline" href={href("club", c.wikidata_qid || enc(d.p.club))}><Logo club={c} size={22} />{clubName(c)}</a>
            {#if d.p.last !== d.p.latest}<span class="text-muted">{t("lastClub")} ({d.p.last})</span>{/if}
          </p>
        {/if}
        {#if d.profile?.full_name && fold(d.profile.full_name) !== fold(d.p.name)}<p class="mt-0.5 text-sm text-muted max-sm:truncate">{d.profile.full_name}</p>{/if}
      </div>
      <!-- Téléphone : deux icônes de 44 px (Suivre, Wikipédia) ; grand écran : boutons avec libellé. -->
      <div class="flex items-center gap-2 max-sm:w-full sm:self-start"><FollowButton compact={isPhone} item={{ kind: "player", id: key, label: d.p.name, sub: natLabel, path: `player/${enc(key)}` }} /><WikiButton compact={isPhone} urls={d.urls} kind="wikiPlayer" /></div>
    </div>
    {#if facts.length}
      <dl class="grid grid-cols-2 gap-x-6 gap-y-5 border-t border-line/60 px-4 py-5 sm:grid-cols-[repeat(auto-fit,minmax(9rem,1fr))] sm:px-6">
        {#each facts as f (f.k)}
          <div class="flex min-w-0 flex-col-reverse justify-end gap-0.5 {f.k === 'bp' ? 'col-span-2' : ''}">
            <dt class="text-sm text-muted">{f.label}</dt>
            <dd class="flex items-center gap-2 text-lg font-semibold leading-tight {f.accent ? 'text-accent' : ''}">{#if f.flag}<Flag code={f.flag} label={f.value} />{/if}<span class="min-w-0 text-balance">{f.value}</span></dd>
            {#if f.sub}<dd class="text-xs tabular-nums text-muted order-first">{f.sub}</dd>{/if}
          </div>
        {/each}
      </dl>
    {/if}
    {#if d.profile?.photo_url && !photoFailed}
      <p class="border-t border-line/60 px-4 py-2 text-[0.7rem] text-muted sm:px-6"><a class="link" href={d.profile.photo_page} target="_blank" rel="noopener">{t("photoBy")} : {d.profile.photo_author || "Wikipedia / Commons"}{d.profile.photo_license ? `, ${d.profile.photo_license}` : ""}</a></p>
    {/if}
  </header>

  {#if tabs.length > 1}
    <!-- Collante sous la barre du haut (mobile) : on change de vue sans remonter. Fond plein, pas de flou. -->
    <div class="sticky top-[calc(3.5rem+env(safe-area-inset-top))] z-20 -mx-4 mt-3 bg-bg px-4 py-2 sm:mx-0 sm:px-0 lg:top-0">
      <Segmented label={t("plViews")} idPrefix="ptab" value={tab} onselect={setTab}
        items={tabs.map((v) => ({ key: v, label: t(v === "path" ? "tlTitle" : v === "stats" ? "tabStats" : "honours") }))} />
    </div>
  {/if}

  {#if tab === "path"}
  <div role="tabpanel" id="ppanel-path" aria-labelledby={tabs.length > 1 ? "ptab-path" : undefined}>
  <!-- Grand écran : la carrière et les sélections à gauche (c'est ce qu'on vient voir), la saison et les derniers matchs à droite. -->
  <div class="lg:grid lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:items-start lg:gap-x-6">
  <div class="min-w-0">
  {#if d.career.length || d.national.length}
    {@const asTimeline = timeline && careerView === "timeline" && d.career.length > 0}
    <section class="card mt-4 overflow-hidden sm:mt-6">
      <div class="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
        <h2 class="text-lg font-bold">{t("carTitle")}</h2>
        {#if timeline}
          <div class="inline-flex rounded-lg border border-line bg-surface p-0.5" role="group" aria-label={t("viewMode")}>
            {#each [["table", "tlTable"], ["timeline", "tlTimeline"]] as [v, k]}
              <button type="button" class="rounded-md px-3 py-1 text-sm font-medium transition {careerView === v ? 'bg-accent text-accent-fg' : 'text-muted hover:text-fg'}"
                aria-pressed={careerView === v} onclick={() => setCareerView(v as "table" | "timeline")}>{t(k)}</button>
            {/each}
          </div>
        {/if}
      </div>
      <div class="border-t border-line/60">
      {#if asTimeline}
        <div class="px-5 pb-3 pt-4">
        <div class="relative" style:height="{timeline.lanes * 2.75 + 1.5}rem" role="list">
        {#each timeline.ticks as tk}<span class="absolute top-0 h-full border-l border-dashed border-line" style:left="{tk.left}%" aria-hidden="true"></span>{/each}
        {#each timeline.bars as b (b.seq)}
          <div role="listitem" class="absolute flex h-10 items-center gap-1.5 overflow-hidden rounded-lg border px-1.5 text-sm font-medium {b.loan ? 'border-dashed border-info bg-info-soft' : 'border-accent/50 bg-accent-soft'}"
            style:left="{b.left}%" style:width="{b.width}%" style:top="{b.lane * 2.75}rem" title="{b.club_name}, {b.years_raw}{b.loan ? ' (' + t('tlLoan') + ')' : ''}">
            <Logo club={{ logo_url: b.club_logo, colors_hex: b.club_colors, club_name: b.club_name }} size={22} />
            <span class="truncate">{b.club_name}</span>
          </div>
        {/each}
      </div>
      <div class="relative mt-1 h-5 text-xs text-muted tabular-nums" aria-hidden="true">
        {#each timeline.ticks as tk}<span class="absolute -translate-x-1/2" style:left="{tk.left}%">{tk.y}</span>{/each}
      </div>
        </div>
      {/if}
      <CareerList career={asTimeline ? [] : d.career} national={d.national} />
      </div>
      {#if d.career.length}
      <p class="border-t border-line/60 px-5 py-3 text-xs text-muted">{t("careerFullNote")}
        <a class="link" href={wikiUrl("en", d.career[0].source_title)} hreflang="en" target="_blank" rel="noopener">{t("careerSrc")}</a></p>
      {/if}
    </section>
  {:else}
    <p class="mt-6 text-muted">{t("noCareer")}</p>
  {/if}
  </div>
  <div class="min-w-0"><PlayerNow qid={d.p.qid ?? null} statClub={d.statClub} /></div>
  </div>
  </div>
  {/if}

  {#if tab === "stats" && d.statClub.length}
    <div role="tabpanel" id="ppanel-stats" aria-labelledby="ptab-stats">
      <PlayerStats club={d.statClub} national={d.statNat} source={d.statSource} />
    </div>
  {/if}

  <!-- Toujours monté (une fois la fiche chargée) pour que l'onglet Palmarès sache s'il a du contenu ; `d` reste celui du joueur précédent tant que le chargement dure -->
  {#if !res.loading}
    <div role="tabpanel" id="ppanel-honours" aria-labelledby="ptab-honours" class={tab === "honours" ? "" : "hidden"}>
      <PlayerHonours pkey={key} qid={d.p.qid ?? null} bind:has={honoursHas} />
    </div>
  {/if}

  {#if d.profile?.photo_url && !photoFailed}
    <!-- Crédit de la photo : sous la photo sur grand écran, ici sur téléphone (la vignette de l'en-tête est trop petite pour le porter). -->
    <p class="mt-4 text-[0.7rem] leading-snug text-muted sm:hidden">
      <a class="link" href={d.profile.photo_page} target="_blank" rel="noopener">{t("photoBy")} : {d.profile.photo_author || "Wikipedia / Commons"}{d.profile.photo_license ? `, ${d.profile.photo_license}` : ""}</a>
    </p>
  {/if}
{/if}
