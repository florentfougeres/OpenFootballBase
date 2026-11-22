<script lang="ts">
  import { app, enc, href, t } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import Flag from "./Flag.svelte";
  import FollowButton from "./FollowButton.svelte";
  import Logo from "./Logo.svelte";

  // Aperçu d'un joueur à côté de l'effectif (grand écran) : identité, totaux de carrière et derniers clubs, sans quitter la liste.
  let { row, onclose }: { row: Record<string, any>; onclose: () => void } = $props();
  const res = resource(async () => {
    const key = row.key as string;
    const career = app.has.career ? await q(`SELECT c.seq, c.start_year, c.years_raw, c.club_name, c.loan, c.apps, c.goals, w.logo_url AS club_logo, w.colors_hex AS club_colors
        FROM career c LEFT JOIN club w ON ${app.careerHasClubQid ? "w.wikidata_qid = c.club_qid" : "w.wikipedia_title = c.club_link"}
        WHERE COALESCE(c.player_qid, 'name:' || c.player) = ? ORDER BY c.seq DESC`, [key]) : [];
    return { career };
  });
  const sum = (k: "apps" | "goals") => (res.data?.career ?? []).reduce((n: number, r: any) => n + (r[k] ?? 0), 0);
</script>

<aside class="card sticky top-20 overflow-hidden" aria-label={row.player}>
  <div class="flex items-start gap-3 p-4">
    <div class="min-w-0 flex-1">
      <h2 class="text-2xl font-bold leading-tight">{row.player}</h2>
      <p class="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted">
        <Flag code={row.nat_flag} label={row.nationality} />{row.nationality}{#if row.position}<span>· {t(row.position)}</span>{/if}{#if row.shirt_number}<span class="tabular-nums">· #{row.shirt_number}</span>{/if}
      </p>
    </div>
    <button type="button" class="grid size-11 shrink-0 place-items-center rounded-xl text-muted transition hover:bg-surface-2 hover:text-fg" aria-label={t("pvClose")} onclick={onclose}>
      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg>
    </button>
  </div>
  {#if res.data?.career.length}
    <dl class="grid grid-cols-2 gap-2 px-4 pb-3">
      {#each [[sum("apps"), t("sumApps")], [sum("goals"), t("sumGoals")]] as [n, label]}
        <div class="rounded-xl bg-accent-soft px-3 py-2"><dd class="display text-2xl font-bold leading-none tabular-nums text-accent">{n}</dd><dt class="mt-1 text-xs text-muted">{label}</dt></div>
      {/each}
    </dl>
    <ul class="divide-y divide-line/60 border-t border-line">
      {#each res.data.career.slice(0, 6) as r (r.seq)}
        <li class="flex items-center gap-2.5 px-4 py-2 text-sm">
          <Logo club={{ logo_url: r.club_logo, colors_hex: r.club_colors, club_name: r.club_name }} size={22} />
          <span class="min-w-0 flex-1 truncate font-medium">{#if r.loan}<span class="text-muted">→ </span>{/if}{r.club_name}</span>
          <span class="shrink-0 text-xs tabular-nums text-muted">{r.years_raw ?? ""}</span>
        </li>
      {/each}
    </ul>
  {:else if res.loading}
    <p class="px-4 pb-4 text-sm text-muted">{t("loading")}</p>
  {/if}
  <div class="flex gap-2 border-t border-line p-3">
    <a class="btn flex-1 justify-center" href={href("player", enc(row.key))}>{t("pvFull")}</a>
    <FollowButton item={{ kind: "player", id: row.key, label: row.player, sub: row.nationality ?? "", path: `player/${enc(row.key)}` }} compact />
  </div>
</aside>
