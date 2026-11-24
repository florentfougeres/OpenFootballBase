<script lang="ts">
  import { href, t } from "../lib/app.svelte";

  // « Plus » : l'onglet de la barre du bas sur mobile qui réunit ce qui n'a pas sa place dans les quatre autres (composition, suivis, pages du site, réglages).
  const row = "flex min-h-14 w-full items-center gap-3 px-4 py-2 text-left no-underline transition hover:bg-surface-2 active:bg-surface-2";
  const items = $derived([
    { label: t("lineupTitle"), to: href("lineup"), d: "M4 4h16v16H4zM4 12h16M12 4v16" },
    { label: t("follows"), to: href("follows"), d: "M6.5 3.5h11v17L12 16.8l-5.5 3.7z" },
    { label: t("balloon"), to: href("ballon-dor"), d: "M8 4h8v5a4 4 0 0 1-8 0zM8 6H5.5a2 2 0 0 0 0 4H8M16 6h2.5a2 2 0 0 1 0 4H16M12 13v4M8.5 20h7M10 17h4" },
    { label: t("coverage"), to: href("coverage"), d: "M4 20V10M10 20V4M16 20v-7M22 20H2" },
    { label: t("about"), to: href("about"), d: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 8h.01" },
    { label: t("settings"), to: href("settings"), d: "M4 7h10M18 7h2M4 17h2M10 17h10M16 7m-2 0a2 2 0 1 0 4 0 2 2 0 1 0-4 0M8 17m-2 0a2 2 0 1 0 4 0 2 2 0 1 0-4 0" },
  ]);
</script>

<h1 class="text-4xl font-extrabold leading-none tracking-tight sm:text-5xl">{t("more")}</h1>
<p class="mt-3 text-muted">{t("moreLead")}</p>

<ul class="card mt-5 max-w-3xl divide-y divide-line/60 overflow-hidden">
  {#each items as it (it.to)}
    <li>
      <a class={row} href={it.to}>
        <svg viewBox="0 0 24 24" class="size-5 shrink-0 text-muted" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d={it.d} /></svg>
        <span class="min-w-0 flex-1 font-semibold">{it.label}</span>
        <span class="text-muted" aria-hidden="true">›</span>
      </a>
    </li>
  {/each}
</ul>
