<script lang="ts">
  import { app, enc, href, route, t } from "../lib/app.svelte";
  import type { Row } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { clubName, clubOf } from "../lib/format";
  import { fold } from "../lib/fold";
  import { decodeLineup, type Line } from "../lib/lineup";
  import LineupBuilder from "../components/LineupBuilder.svelte";
  import Logo from "../components/Logo.svelte";
  import Segmented from "../components/Segmented.svelte";
  import Spinner from "../components/Spinner.svelte";

  // Composition : un onze à construire, soit avec l'effectif d'un club et d'une saison (le blason du club est posé sur le terrain), soit avec tous les joueurs de la base.
  // Tout est dans l'adresse (`?src=club&club=…&s=…&f=…&p=…`) : le lien d'une composition la restitue.
  const mode = $derived<"club" | "all">(route.query.get("src") === "club" ? "club" : "all");          // par défaut : tous les joueurs
  const clubTitle = $derived(route.query.get("club"));
  const season = $derived(route.query.get("s"));
  const club = $derived(clubTitle ? clubOf(clubTitle) : null);

  /** Couleurs du club (« #aa0000 | #ffffff ») : elles décident du style de départ des maillots. */
  const clubColors = (hex: unknown): string[] => (String(hex ?? "").match(/#[0-9a-f]{6}/gi) ?? []).map((c) => c.toLowerCase()).slice(0, 2);
  const go = (params: Record<string, string | null>) => {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v) qs.set(k, v);
    location.hash = `#/${route.lang}/lineup${qs.size ? `?${qs}` : ""}`;
  };

  // Club : recherche dans les clubs qui ont un effectif.
  let term = $state("");
  const matches = $derived.by(() => {
    const n = fold(term.trim());
    if (n.length < 2) return [] as Row[];
    return [...app.clubs.values()].filter((c) => app.squadClubs.has(c.wikipedia_title as string) && [c.name_en, c.name_fr, c.name_local].some((x) => fold(String(x ?? "")).includes(n))).slice(0, 8);
  });

  // Saisons du club choisi, puis l'effectif de la saison (la plus récente par défaut).
  const seasons = resource(async () => {
    const tt = clubTitle;
    if (mode !== "club" || !tt) return [] as string[];
    return (await q(`SELECT season FROM club_season WHERE club = ? AND players > 0 ORDER BY season DESC`, [tt])).map((r) => r.season as string);
  });
  const label = $derived(season && seasons.data?.includes(season) ? season : seasons.data?.[0] ?? null);
  const squad = resource(async () => {
    const tt = clubTitle, lbl = label;
    if (mode !== "club" || !tt || !lbl) return null;
    return await q(`SELECT COALESCE(player_qid, 'name:' || player) AS key, player, shirt_number, position, nat_flag FROM squad WHERE club = ? AND season = ? ORDER BY shirt_number NULLS LAST, player`, [tt, lbl]);
  });

  // Tous les joueurs : recherche par nom (les joueurs de la ligne du poste d'abord) ; ceux du lien ouvert sont relus par leur identifiant.
  const FIELDS = `any_value(player) AS player, COALESCE(player_qid, 'name:' || player) AS key, arg_max(position, season) AS position, arg_max(nat_flag, season) AS nat_flag, arg_max(club, season) AS club, max(season) AS last`;
  const find = async (term: string, line: Line) => q(`SELECT ${FIELDS} FROM squad WHERE strip_accents(player) ILIKE strip_accents(?) GROUP BY 2 ORDER BY (arg_max(position, season) = ?) DESC, max(season) DESC, any_value(player) LIMIT 30`, [`%${term}%`, line]);
  const seed = resource(async () => {
    if (mode !== "all") return [] as Row[];
    const keys = (decodeLineup(route.query)?.players.filter(Boolean) ?? []) as string[];
    if (!keys.length) return [] as Row[];
    return await q(`SELECT ${FIELDS} FROM squad WHERE COALESCE(player_qid, 'name:' || player) IN (${keys.map(() => "?").join(",")}) GROUP BY 2`, keys);
  });

  const base = $derived(mode === "all" ? `#/${route.lang}/lineup?src=all` : `#/${route.lang}/lineup?src=club&club=${enc(clubTitle ?? "")}&s=${enc(label ?? "")}`);
  const pickBtn = "flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left transition hover:bg-surface-2";
</script>

<!-- --lu-chrome : la hauteur de tout ce qui entoure le terrain sur téléphone (le mode « par club » a une ligne de plus) -->
<div class="mx-auto lg:max-w-[46rem]" style="--lu-chrome: {mode === 'all' ? '20.75rem' : '24.5rem'}">
<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
  <h1 class="text-3xl font-extrabold leading-none tracking-tight sm:text-4xl">{t("lineupTitle")}</h1>
  <Segmented class="sm:w-fit" tabs={false} label={t("lineupSource")} idPrefix="lsrc" value={mode}
  onselect={(k) => go(k === "club" ? { src: "club" } : {})}
  items={[{ key: "all", label: t("lineupAllPlayers") }, { key: "club", label: t("lineupByClub") }]} />
</div>

{#if mode === "club"}
  <div class="mt-3 sm:mt-4">
    {#if club && clubTitle}
      <div class="flex items-center gap-2 sm:flex-wrap sm:gap-3">
        <div class="flex min-w-0 flex-1 items-center gap-2.5 rounded-2xl border border-line bg-surface py-1.5 pl-2 pr-3 sm:flex-none sm:gap-3 sm:py-2 sm:pl-2.5 sm:pr-4">
          <Logo {club} size={32} />
          <span class="min-w-0 text-sm font-bold leading-tight sm:text-lg">{clubName(club)}</span>
        </div>
        {#if seasons.data?.length}
          <select class="h-10 rounded-xl border border-line bg-surface px-2 text-sm font-semibold tabular-nums sm:px-3" aria-label={t("seasonTab")} value={label} onchange={(e) => go({ src: "club", club: clubTitle, s: e.currentTarget.value })}>
            {#each seasons.data as s (s)}<option value={s}>{s}</option>{/each}
          </select>
        {/if}
        <button type="button" class="grid size-10 shrink-0 place-items-center rounded-xl border border-line bg-surface text-sm font-semibold transition hover:bg-surface-2 sm:inline-flex sm:w-auto sm:px-3.5" aria-label={t("lineupChangeClub")} onclick={() => go({ src: "club" })}>
          <svg viewBox="0 0 24 24" class="size-5 sm:hidden" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 7h12l-3-3M17 17H5l3 3" /></svg>
          <span class="hidden sm:inline">{t("lineupChangeClub")}</span>
        </button>
        <a class="link hidden text-sm sm:inline" href={href("club", enc(clubTitle))}>{t("lineupClubPage")} →</a>
      </div>
    {:else}
      <div class="max-w-xl">
        <label class="text-sm font-semibold text-muted" for="lineup-club">{t("lineupPickClub")}</label>
        <input id="lineup-club" type="search" class="mt-1.5 h-12 w-full rounded-xl border border-line bg-surface px-4 text-base" placeholder={t("lineupClubSearch")} bind:value={term} autocomplete="off" />
        {#if matches.length}
          <ul class="card mt-2 divide-y divide-line/40 overflow-hidden p-1">
            {#each matches as c (c.wikipedia_title)}
              <li><button type="button" class={pickBtn} onclick={() => go({ src: "club", club: c.wikipedia_title as string })}><Logo club={c} size={32} /><span class="min-w-0 flex-1 truncate font-semibold">{clubName(c)}</span></button></li>
            {/each}
          </ul>
        {:else if term.trim().length >= 2}
          <p class="mt-2 text-sm text-muted">{t("noResult")}</p>
        {/if}
      </div>
    {/if}
  </div>

  {#if clubTitle}
    {#if seasons.loading || squad.loading}
      <Spinner />
    {:else if squad.data?.length}
      {#key `${clubTitle}|${label}`}
        <LineupBuilder rows={squad.data} caption="{clubName(clubOf(clubTitle))} {label}" logo={clubOf(clubTitle).logo_url ?? null} colors={clubColors(clubOf(clubTitle).colors_hex)} {base} />
      {/key}
    {:else}
      <p class="card mt-4 p-4 text-muted">{t("noSquad")}</p>
    {/if}
  {/if}
{:else}
  {#if seed.loading}
    <Spinner />
  {:else}
    {#key route.query.get("p")}
      <LineupBuilder find={find} seed={seed.data ?? []} caption={t("lineupAllCaption")} {base} />
    {/key}
  {/if}
{/if}
</div>
