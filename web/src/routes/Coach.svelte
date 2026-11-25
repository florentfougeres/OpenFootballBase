<script lang="ts">
  import { app, enc, href, page, t } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { clubName, clubOf, nationalTeam, wikiUrl } from "../lib/format";
  import Crumbs from "../components/Crumbs.svelte";
  import ErrorBox from "../components/ErrorBox.svelte";
  import Flag from "../components/Flag.svelte";
  import Logo from "../components/Logo.svelte";
  import Spinner from "../components/Spinner.svelte";
  import WikiButton from "../components/WikiButton.svelte";

  // Fiche d'un entraîneur : ses mandats (table `coach`), sa carrière de joueur s'il en a une dans nos données, et une infobox (nom, pays, naissance, pages Wikipedia).
  let { qid }: { qid: string } = $props();

  const res = resource(async () => {
    const id = qid;
    if (!app.has.coach) return null;
    const tenures = await q(`SELECT *, CAST(start_date AS VARCHAR) AS s, CAST(end_date AS VARCHAR) AS e FROM coach WHERE coach_qid = ? ORDER BY start_date DESC`, [id]);
    if (!tenures.length) return null;
    // Carrière d'entraîneur de l'infobox Wikipedia (clubs ET sélections, adjoint compris) ; à défaut, seulement les mandats Wikidata des clubs de notre base.
    const infobox = app.has.coach_career ? await q(`SELECT c.seq, c.years_raw, c.start_year, c.end_year, c.team_name, c.team_link, w.logo_url AS team_logo, w.colors_hex AS team_colors
        FROM coach_career c LEFT JOIN club w ON w.wikipedia_title = c.team_link WHERE c.coach_qid = ? ORDER BY c.seq`, [id]) : [];
    // Profil (table `coach_profile`, releases récentes) : naissance et pages Wikipedia de l'entraîneur.
    const profile = app.has.coach_profile ? (await q(`SELECT * FROM coach_profile WHERE coach_qid = ?`, [id]))[0] ?? null : null;
    // Il a aussi joué dans nos données : sa fiche joueur est la même personne (même QID).
    const career = app.has.career ? await q(`SELECT c.seq, c.start_year, c.end_year, c.years_raw, c.club_name, c.club_link, c.loan, c.apps, c.goals, w.logo_url AS club_logo, w.colors_hex AS club_colors
        FROM career c LEFT JOIN club w ON ${app.careerHasClubQid ? "w.wikidata_qid = c.club_qid" : "w.wikipedia_title = c.club_link"} WHERE c.player_qid = ? ORDER BY c.seq`, [id]) : [];
    const birth = career.length && app.has.birth ? (await q(`SELECT birth_date, precision FROM birth WHERE player_qid = ?`, [id]))[0] ?? null : null;
    const urls: Record<string, string> = {};
    if (app.has.entity_wiki) for (const r of await q(`SELECT lang, title FROM entity_wiki WHERE qid = ?`, [id])) urls[r.lang] = wikiUrl(r.lang, r.title);
    if (profile?.wikipedia_en && !urls.en) urls.en = wikiUrl("en", profile.wikipedia_en);
    if (profile?.wikipedia_fr && !urls.fr) urls.fr = wikiUrl("fr", profile.wikipedia_fr);
    return { tenures, infobox, profile, career, birth, urls };
  });
  const d = $derived(res.data);
  const name = $derived(d?.tenures[0]?.coach_name as string | undefined);
  const flag = $derived((d?.tenures.find((r: any) => r.flag)?.flag as string | undefined) ?? null);
  $effect(() => { page.name = name ?? null; return () => { page.name = null; }; });

  const years = (r: any) => {
    const a = Number(String(r.s).slice(0, 4)), b = r.e ? Number(String(r.e).slice(0, 4)) : null;
    return b === null ? `${a}–` : b === a ? String(a) : `${a}–${b}`;
  };
  const teamsN = $derived(d?.infobox.length ? new Set(d.infobox.map((r: any) => r.team_name)).size : new Set((d?.tenures ?? []).map((r: any) => r.club)).size);
  const first = $derived.by(() => {
    if (!d) return 0;
    const ys = d.infobox.map((r: any) => r.start_year).filter((y: any) => y != null);
    return ys.length ? Math.min(...ys) : Number(String(d.tenures[d.tenures.length - 1].s).slice(0, 4));
  });
  const birthText = $derived.by(() => {
    const b = d?.birth ?? (d?.profile?.birth_date ? { birth_date: d.profile.birth_date, precision: "day" } : null);
    if (!b?.birth_date) return d?.profile?.birth_year ? String(d.profile.birth_year) : null;
    // `coach_profile.birth_date` est une DATE (nombre de ms pour DuckDB-WASM) ; `birth.birth_date` un texte AAAA-MM-JJ.
    const raw = b.birth_date;
    const date = typeof raw === "number" || raw instanceof Date ? new Date(raw) : new Date(String(raw).slice(0, 10) + "T00:00:00");
    if (Number.isNaN(date.getTime())) return d?.profile?.birth_year ? String(d.profile.birth_year) : null;
    return b.precision === "year" ? String(date.getFullYear()) : date.toLocaleDateString(app.lang, { day: "numeric", month: "long", year: "numeric", timeZone: typeof raw === "number" || raw instanceof Date ? "UTC" : undefined });
  });
  const place = $derived((d?.profile?.birth_place as string | undefined) ?? null);
</script>

<Crumbs trail={[]} />
{#if res.loading && !d}
  <Spinner />
{:else if res.error}
  <ErrorBox message={res.error} />
{:else if !d}
  <p class="text-warn">{t("coachNotFound")}</p>
{:else}
  <header class="card mt-3 p-5 sm:p-6">
    <p class="eyebrow">{t("coachRole")}</p>
    <h1 class="mt-1 flex items-center gap-3 text-3xl font-extrabold leading-tight tracking-tight sm:text-4xl">
      {#if flag}<Flag code={flag} size={28} />{/if}<span class="min-w-0">{name}</span>
    </h1>
    <dl class="mt-4 grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
      <div><dt class="eyebrow">{t("coachTenures")}</dt><dd class="mt-0.5 font-medium tabular-nums">{d.infobox.length || d.tenures.length}, {teamsN} {teamsN > 1 ? t("coachTeamsN") : t("coachTeamsN1")}</dd></div>
      <div><dt class="eyebrow">{t("coachSince")}</dt><dd class="mt-0.5 font-medium tabular-nums">{first}</dd></div>
      {#if birthText}<div><dt class="eyebrow">{t("coachBorn")}</dt><dd class="mt-0.5 font-medium">{birthText}{place ? `, ${place}` : ""}</dd></div>{/if}
      {#if d.career.length}<div><dt class="eyebrow">{t("coachAlsoPlayer")}</dt><dd class="mt-0.5 font-medium"><a class="link" href={href("player", enc(qid))}>{t("coachPlayerPage")}</a></dd></div>{/if}
    </dl>
    <div class="mt-4"><WikiButton urls={d.urls} kind="wikiPlayer" fallbackKey="wikiLocalOnly" /></div>
  </header>

  <div class="mt-8 grid gap-8 lg:grid-cols-2 lg:items-start">
    <section aria-labelledby="coach-tenures">
      <h2 id="coach-tenures" class="mb-2 text-xl font-bold">{t("coachCareer")}</h2>
      {#if d.infobox.length}
        <ul class="card divide-y divide-line/60 overflow-hidden">
          {#each d.infobox as r, i (i)}
            {@const nat = r.team_logo ? null : nationalTeam(r.team_name)}
            <li class="flex items-center gap-3 px-4 py-2.5 text-sm">
              <span class="grid size-8 shrink-0 place-items-center">
                {#if r.team_logo}<Logo club={{ logo_url: r.team_logo, colors_hex: r.team_colors, club_name: r.team_name }} size={28} />{:else if nat?.flag}<Flag code={nat.flag} size={22} />{/if}
              </span>
              <span class="min-w-0 flex-1 truncate font-semibold">{#if r.team_link && app.clubs.has(r.team_link)}<a class="hover:text-accent hover:underline" href={href("club", enc(r.team_link))}>{clubName(clubOf(r.team_link))}</a>{:else}{r.team_name}{/if}</span>
              <span class="shrink-0 tabular-nums text-muted">{r.years_raw}</span>
            </li>
          {/each}
        </ul>
        <p class="mt-2 text-xs text-muted">{t("coachInfoboxNote")}</p>
      {:else}
        <ul class="card divide-y divide-line/60 overflow-hidden">
          {#each d.tenures as r, i (i)}
            <li>
              <a class="row" href={href("club", enc(r.club))}>
                <Logo club={clubOf(r.club)} size={32} />
                <span class="min-w-0 flex-1 truncate font-semibold">{clubName(clubOf(r.club))}</span>
                <span class="shrink-0 text-sm tabular-nums text-muted">{years(r)}{#if !r.e}<span class="sr-only"> {t("coachesNow")}</span>{/if}</span>
                <span class="shrink-0 text-muted" aria-hidden="true">›</span>
              </a>
            </li>
          {/each}
        </ul>
        <p class="mt-2 text-xs text-muted">{t("coachesNote")}</p>
      {/if}
    </section>

    {#if d.career.length}
      <section aria-labelledby="coach-player">
        <h2 id="coach-player" class="mb-2 text-xl font-bold">{t("coachPlayingCareer")}</h2>
        <ul class="card divide-y divide-line/60 overflow-hidden">
          {#each d.career as r, i (i)}
            <li class="flex items-center gap-3 px-4 py-2.5 text-sm">
              <Logo club={{ logo_url: r.club_logo, colors_hex: r.club_colors, club_name: r.club_name }} size={24} />
              <span class="w-20 shrink-0 tabular-nums text-muted">{r.years_raw ?? r.start_year ?? ""}</span>
              <span class="min-w-0 flex-1 truncate font-medium">{#if r.club_link && app.clubs.has(r.club_link)}<a class="hover:text-accent hover:underline" href={href("club", enc(r.club_link))}>{r.club_name}</a>{:else}{r.club_name}{/if}{#if r.loan}<span class="ml-1.5 text-xs text-muted">({t("loanTag")})</span>{/if}</span>
              {#if r.apps != null}<span class="shrink-0 tabular-nums text-muted">{r.apps}{r.goals != null ? ` (${r.goals})` : ""}</span>{/if}
            </li>
          {/each}
        </ul>
        <a class="link mt-3 inline-flex min-h-11 items-center text-sm" href={href("player", enc(qid))}>{t("coachPlayerPage")} →</a>
      </section>
    {/if}
  </div>
{/if}
