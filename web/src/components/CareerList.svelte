<script lang="ts">
  // Carrière en liste épurée (une ligne par passage : écusson, club, dates, puis matchs et buts alignés à droite), en sections : clubs, équipe nationale, équipes de jeunes.
  import { href, t, type Row } from "../lib/app.svelte";
  import { isOngoing, nationalTeam, wikiUrl } from "../lib/format";
  import Badge from "./Badge.svelte";
  import Flag from "./Flag.svelte";
  import Icon from "./Icon.svelte";
  import Logo from "./Logo.svelte";

  let { career, national }: { career: Row[]; national: Row[] } = $props();

  const youth = (r: Row) => /\bU\d{2}\b|under/i.test(String(r.team_name));
  const senior = $derived(national.filter((r) => !youth(r)));
  const young = $derived(national.filter(youth));
  const dates = (r: Row) => (isOngoing(r.years_raw) ? `${String(r.years_raw).replace(/\s*[–-]\s*$/, "")} – ${t("ongoing")}` : String(r.years_raw ?? ""));
  const sections = $derived([
    { key: "club", title: t("carPro"), rows: career },
    { key: "nat", title: t("nationalTitle"), rows: senior },
    { key: "youth", title: t("carYouth"), rows: young },
  ].filter((s) => s.rows.length));
</script>

{#snippet pitch()}
  <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="1.5" /><path d="M12 5v14M3 10h3.5v4H3M21 10h-3.5v4H21" /></svg>
{/snippet}

{#each sections as s, i (s.key)}
  <div class="{i ? 'border-t border-line/60' : ''} px-5 py-3">
    <div class="grid grid-cols-[1fr_3rem_3rem] items-center text-muted">
      <h3 class="text-base font-semibold">{s.title}</h3>
      <span class="grid justify-items-end" title={t("colApps")}>{@render pitch()}<span class="sr-only">{t("colApps")}</span></span>
      <span class="grid justify-items-end" title={t("colGoals")}><Icon name="ball" size={16} /><span class="sr-only">{t("colGoals")}</span></span>
    </div>
    <ul>
      {#each s.rows as r, k (s.key + (r.seq ?? k))}
        {@const nt = s.key === "club" ? null : nationalTeam(r.team_name)}
        <li class="grid min-h-14 grid-cols-[2.25rem_1fr_3rem_3rem] items-center gap-x-2 py-2">
          <span class="grid place-items-center">
            {#if nt}{#if nt.flag}<Flag code={nt.flag} label={nt.name} size={24} />{/if}{:else}<Logo club={{ logo_url: r.club_logo, colors_hex: r.club_colors, club_name: r.club_name }} size={28} />{/if}
          </span>
          <span class="min-w-0">
            <span class="block font-medium leading-tight">
              {#if nt}
                {#if r.team_link}<a class="link" href={wikiUrl("en", r.team_link)} hreflang="en" target="_blank" rel="noopener">{nt.name}</a>{:else}{nt.name}{/if}
              {:else}
                {#if r.loan}<span class="text-muted">→ </span>{/if}{#if r.club_qid}<a class="link" href={href("club", r.club_qid)}>{r.club_name}</a>{:else if r.club_link}<a class="link" href={wikiUrl("en", r.club_link)} hreflang="en" target="_blank" rel="noopener">{r.club_name}</a>{:else}{r.club_name}{/if}
                {#if r.loan}{" "}<Badge kind="info">{t("loanTag")}</Badge>{/if}
              {/if}
            </span>
            <span class="block text-sm text-muted">{dates(r)}</span>
          </span>
          <span class="text-right font-semibold tabular-nums">{(nt ? r.caps : r.apps) ?? ""}</span>
          <span class="text-right font-semibold tabular-nums">{r.goals ?? ""}</span>
        </li>
      {/each}
    </ul>
  </div>
{/each}
{#if sections.length}
  <p class="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-line/60 px-5 py-3 text-xs text-muted">
    <span class="inline-flex items-center gap-1.5">{@render pitch()}{t("colApps")}</span>
    <span class="inline-flex items-center gap-1.5"><Icon name="ball" size={16} />{t("colGoals")}</span>
  </p>
{/if}
