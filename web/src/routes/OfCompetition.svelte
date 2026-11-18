<script lang="ts">
  // Page d'une compétition « OF:* » (sélections, Sudamericana, championnats du dépôt `world`…) : titre et vue Résultats. La liste est dans Competitions.
  import { app, href, t } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { NATIONAL, isNational } from "../lib/ofcomps";
  import Crumbs from "../components/Crumbs.svelte";
  import Icon from "../components/Icon.svelte";
  import Results from "../components/Results.svelte";
  import Spinner from "../components/Spinner.svelte";
  import WikiButton from "../components/WikiButton.svelte";
  import { wikiUrl } from "../lib/format";

  let { code }: { code: string } = $props();
  const meta = resource(async () => {
    const c = code;
    const named = app.has.match_competition;
    return (await q(`SELECT count(*) AS n, min(m.season) AS first, max(m.season) AS last${named ? ", any_value(c.name) AS name, any_value(c.logo_url) AS logo, any_value(c.wikipedia_title) AS wiki" : ""}
                     FROM match m ${named ? "LEFT JOIN match_competition c ON c.code = m.competition" : ""} WHERE m.competition = ?`, [c]))[0];
  });
  const national = $derived(isNational(code));
  const title = $derived(NATIONAL[code]?.[app.lang] ?? (meta.data?.name as string | undefined) ?? code.slice(3));
</script>

<Crumbs trail={[{ label: t("allComps"), to: href("competitions") }]} />
{#if meta.loading && !meta.data}
  <Spinner />
{:else if !meta.data || !meta.data.n}
  <p class="text-warn">{t("compNotFound")}</p>
{:else}
  <header class="flex items-center gap-4">
    {#if meta.data.logo}
      <span class="block size-16 shrink-0 overflow-hidden rounded-xl border border-line bg-white p-1.5 sm:size-20"><img class="size-full object-contain" src={meta.data.logo as string} alt="" /></span>
    {:else}
      <span class="grid size-16 shrink-0 place-items-center rounded-xl border border-line bg-accent-soft text-accent sm:size-20"><Icon name={NATIONAL[code]?.icon ?? "list"} size={34} /></span>
    {/if}
    <div class="min-w-0">
      <h1 class="text-3xl font-extrabold leading-none tracking-tight text-balance sm:text-4xl lg:text-5xl">{title}</h1>
      <p class="mt-2 text-sm text-muted">{meta.data.first}{meta.data.first !== meta.data.last ? ` – ${meta.data.last}` : ""} · {(meta.data.n as number).toLocaleString(app.lang)} {t("matchesN")}</p>
    </div>
  </header>
  {#if meta.data.wiki}<div class="mt-4"><WikiButton urls={{ en: wikiUrl("en", meta.data.wiki as string) }} kind="wikiPlayer" /></div>{/if}
  <Results {code} {national} />
{/if}
