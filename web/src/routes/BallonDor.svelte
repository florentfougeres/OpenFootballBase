<script lang="ts">
  import { app, href, enc, t, type Row } from "../lib/app.svelte";
  import { q } from "../lib/db";
  import { resource } from "../lib/resource.svelte";
  import { clubName, clubOf } from "../lib/format";
  import Crumbs from "../components/Crumbs.svelte";
  import Flag from "../components/Flag.svelte";
  import Logo from "../components/Logo.svelte";
  import Spinner from "../components/Spinner.svelte";
  import Trophy from "../components/Trophy.svelte";

  // Ballon d'Or : le classement de chaque édition depuis 2000 (pages Wikipedia), avec le palmarès des joueurs.
  const data = resource(async () => {
    if (!app.has.award) return null;
    const rows = await q(`SELECT year, rank, player_name, player_qid, club_name, club, points FROM award WHERE award = 'BALLON_DOR' ORDER BY year DESC, rank`);
    const qids = [...new Set(rows.map((r) => r.player_qid).filter(Boolean))] as string[];
    const flags = new Map<string, string>();
    const known = new Set<string>();
    if (qids.length) {
      const list = qids.map((x) => `'${x.replace(/'/g, "''")}'`).join(",");
      for (const r of await q(`SELECT player_qid, arg_max(nat_flag, season) AS flag FROM squad WHERE player_qid IN (${list}) GROUP BY 1`)) { known.add(r.player_qid); if (r.flag) flags.set(r.player_qid, r.flag); }
    }
    return { rows, flags, known };
  });
  const editions = $derived.by(() => {
    const by = new Map<number, Row[]>();
    for (const r of data.data?.rows ?? []) by.set(r.year, [...(by.get(r.year) ?? []), r]);
    return [...by.entries()].sort((a, b) => b[0] - a[0]);
  });
  /** Joueurs classés au podium : victoires, 2es et 3es places. */
  const board = $derived.by(() => {
    const by = new Map<string, { key: string; name: string; qid: string | null; w: number[]; s: number; t: number }>();
    for (const r of data.data?.rows ?? []) {
      if (r.rank > 3) continue;
      const key = r.player_qid ?? r.player_name;
      const g = by.get(key) ?? { key, name: r.player_name, qid: r.player_qid, w: [] as number[], s: 0, t: 0 };
      if (r.rank === 1) g.w.push(r.year); else if (r.rank === 2) g.s++; else g.t++;
      by.set(key, g);
    }
    return [...by.values()].filter((g) => g.w.length).sort((a, b) => b.w.length - a.w.length || (b.s + b.t) - (a.s + a.t) || Math.max(...b.w) - Math.max(...a.w));
  });
  const ord = (n: number) => (app.lang === "fr" ? `${n}e` : n === 2 ? "2nd" : "3rd");
  const link = (r: { player_qid?: string | null }) => (r.player_qid && data.data?.known.has(r.player_qid) ? href("player", enc(r.player_qid)) : null);
  const flagOf = (qid?: string | null) => (qid ? data.data?.flags.get(qid) ?? null : null);
</script>

<Crumbs trail={[]} />
<h1 class="flex items-center gap-3 text-3xl font-extrabold tracking-tight sm:text-4xl"><Trophy size={32} />{t("balloon")}</h1>
<p class="mt-2 max-w-2xl text-muted">{t("balloonLead")}</p>

{#if data.loading && !data.data}
  <Spinner />
{:else if !data.data || !editions.length}
  <p class="card mt-6 px-4 py-6 text-muted">{t("noResult")}</p>
{:else}
  <section class="mt-6" aria-labelledby="bd-board">
    <h2 id="bd-board" class="mb-2 text-xl font-bold">{t("balloonBoard")}</h2>
    <ol class="card divide-y divide-line/60 px-4">
      {#each board as g, i (g.key)}
        <li class="flex items-center gap-3 py-2.5">
          <span class="w-5 text-right text-sm tabular-nums text-muted">{i + 1}</span>
          <Flag code={flagOf(g.qid)} size={20} />
          <span class="min-w-0 flex-1">
            {#if g.qid && data.data.known.has(g.qid)}<a class="block truncate font-semibold no-underline hover:text-accent" href={href("player", enc(g.qid))}>{g.name}</a>{:else}<span class="block truncate font-semibold">{g.name}</span>{/if}
            <span class="block truncate text-xs tabular-nums text-muted">{g.w.length ? g.w.sort().join(" · ") : "—"}{#if g.s || g.t} · {t("podium")} : {[g.s ? `${g.s}×${ord(2)}` : "", g.t ? `${g.t}×${ord(3)}` : ""].filter(Boolean).join(", ")}{/if}</span>
          </span>
          <span class="display text-2xl font-bold tabular-nums text-accent">{g.w.length}</span>
        </li>
      {/each}
    </ol>
  </section>

  <section class="mt-8" aria-labelledby="bd-editions">
    <h2 id="bd-editions" class="mb-2 text-xl font-bold">{t("balloonEditions")}</h2>
    <ul class="card divide-y divide-line/60">
      {#each editions as [year, ranks] (year)}
        {@const w = ranks[0]}
        <li>
          <details class="group">
            <summary class="flex cursor-pointer list-none items-center gap-3 px-4 py-3 hover:bg-surface-2 [&::-webkit-details-marker]:hidden">
              <span class="display w-14 shrink-0 text-2xl font-bold tabular-nums">{year}</span>
              <Flag code={flagOf(w.player_qid)} size={20} />
              <span class="min-w-0 flex-1">
                <span class="block truncate font-semibold">{#if link(w)}<a class="no-underline hover:text-accent" href={link(w)} onclick={(e) => e.stopPropagation()}>{w.player_name}</a>{:else}{w.player_name}{/if}</span>
                <span class="block truncate text-xs text-muted">{w.club ? clubName(clubOf(w.club)) : w.club_name ?? ""}{#if w.points} · {w.points} {t("points")}{/if}</span>
              </span>
              {#if w.club}<Logo club={clubOf(w.club)} size={30} />{/if}
              <span class="text-muted transition group-open:rotate-90" aria-hidden="true">›</span>
            </summary>
            <ol class="bg-surface-2/40 px-4 py-2">
              {#each ranks.slice(0, 10) as r (r.rank + r.player_name)}
                <li class="flex items-center gap-3 py-1.5 text-sm {r.rank === 1 ? 'font-semibold' : ''}">
                  <span class="w-5 text-right tabular-nums text-muted">{r.rank}</span>
                  <span class="min-w-0 flex-1 truncate">{#if link(r)}<a class="no-underline hover:text-accent" href={link(r)}>{r.player_name}</a>{:else}{r.player_name}{/if}</span>
                  <span class="hidden min-w-0 max-w-[40%] truncate text-xs text-muted sm:block">{r.club ? clubName(clubOf(r.club)) : r.club_name ?? ""}</span>
                  <span class="w-14 text-right tabular-nums text-muted">{r.points ?? ""}</span>
                </li>
              {/each}
            </ol>
          </details>
        </li>
      {/each}
    </ul>
    <p class="mt-2 text-xs text-muted">{t("balloonSource")}</p>
  </section>
{/if}
