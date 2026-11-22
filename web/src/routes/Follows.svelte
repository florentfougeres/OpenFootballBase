<script lang="ts">
  import { app, href, t } from "../lib/app.svelte";
  import { theme, cycleTheme } from "../lib/theme.svelte";
  import { follows, type Follow, type FollowKind } from "../lib/follow.svelte";
  import FollowButton from "../components/FollowButton.svelte";

  // Suivis (clubs, joueurs, compétitions épinglés sur cet appareil) et réglages : ce qui était derrière « Plus » sur mobile.
  const KINDS: { k: FollowKind; label: string }[] = [{ k: "club", label: "clubs" }, { k: "player", label: "players" }, { k: "comp", label: "allComps" }];
  const by = (k: FollowKind) => follows.items.filter((f) => f.kind === k);
  const other = $derived(app.lang === "fr" ? "en" : "fr");
  const themeLabel = $derived(theme.value === "dark" ? t("themeDark") : theme.value === "light" ? t("themeLight") : t("themeAuto"));
  const D = { club: "M12 3 5 5.5V11c0 4.2 2.8 7.4 7 9 4.2-1.6 7-4.8 7-9V5.5z", player: "M12 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM5 20c.7-3.6 3.3-5.5 7-5.5s6.3 1.9 7 5.5", comp: "M8 4h8v5a4 4 0 0 1-8 0zM12 13v4M8.5 20h7" };
  const row = "flex min-h-14 items-center gap-3 px-4 py-2 text-left no-underline transition hover:bg-surface-2 active:bg-surface-2";
</script>

<h1 class="text-4xl font-extrabold leading-none tracking-tight sm:text-5xl">{t("follows")}</h1>

<div class="mt-5 max-w-3xl">
  {#if !follows.items.length}
    <p class="card p-5 text-muted">{t("followsEmpty")}</p>
  {:else}
    {#each KINDS as g (g.k)}
      {#if by(g.k).length}
        <h2 class="mb-2 mt-6 px-1 text-xs font-semibold uppercase tracking-wide text-muted first:mt-0">{t(g.label)}</h2>
        <ul class="card divide-y divide-line/60 overflow-hidden">
          {#each by(g.k) as f (f.id)}
            <li class="flex items-center pr-2">
              <a class="{row} min-w-0 flex-1" href={`#/${app.lang}/${f.path}`}>
                <span class="grid size-9 shrink-0 place-items-center rounded-full bg-surface-2 text-muted"><svg viewBox="0 0 24 24" class="size-[18px]" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d={D[f.kind]} /></svg></span>
                <span class="min-w-0 flex-1"><span class="block truncate font-semibold">{f.label}</span>{#if f.sub}<span class="block truncate text-sm text-muted">{f.sub}</span>{/if}</span>
              </a>
              <FollowButton item={f} compact />
            </li>
          {/each}
        </ul>
      {/if}
    {/each}
  {/if}
  <p class="mt-3 px-1 text-sm text-muted">{t("followsNote")}</p>

  <h2 class="mb-2 mt-8 px-1 text-xs font-semibold uppercase tracking-wide text-muted">{t("settings")}</h2>
  <ul class="card divide-y divide-line/60 overflow-hidden">
    <li><button type="button" class="{row} w-full justify-between" onclick={cycleTheme}><span class="font-semibold">{t("theme")}</span><span class="text-sm text-muted">{themeLabel}</span></button></li>
    <li><a class="{row} justify-between" href={`#/${other}/follows`} hreflang={other} lang={other}><span class="font-semibold">{t("langLabel")}</span><span class="text-sm text-muted">{app.lang === "fr" ? "Français" : "English"} → {other.toUpperCase()}</span></a></li>
    <li><a class="{row} justify-between" href={href("ballon-dor")}><span class="font-semibold">{t("balloon")}</span><span class="text-muted" aria-hidden="true">›</span></a></li>
    <li><a class="{row} justify-between" href={href("coverage")}><span class="font-semibold">{t("coverage")}</span><span class="text-muted" aria-hidden="true">›</span></a></li>
    <li><a class="{row} justify-between" href={href("about")}><span class="font-semibold">{t("about")}</span><span class="text-muted" aria-hidden="true">›</span></a></li>
  </ul>
</div>
