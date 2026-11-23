<script lang="ts">
  import { app, href, t } from "../lib/app.svelte";
  import { theme, cycleTheme } from "../lib/theme.svelte";

  // Réglages : thème, langue, et les pages de service du site (couverture des données, à propos). Sur mobile, on y va par l'engrenage de la barre du haut.
  const other = $derived(app.lang === "fr" ? "en" : "fr");
  const themeLabel = $derived(theme.value === "dark" ? t("themeDark") : theme.value === "light" ? t("themeLight") : t("themeAuto"));
  const row = "flex min-h-14 w-full items-center justify-between gap-3 px-4 py-2 text-left no-underline transition hover:bg-surface-2 active:bg-surface-2";
</script>

<h1 class="text-4xl font-extrabold leading-none tracking-tight sm:text-5xl">{t("settings")}</h1>

<div class="mt-5 max-w-3xl">
  <ul class="card divide-y divide-line/60 overflow-hidden">
    <li><button type="button" class={row} onclick={cycleTheme}><span class="font-semibold">{t("theme")}</span><span class="text-sm text-muted">{themeLabel}</span></button></li>
    <li><a class={row} href={`#/${other}/settings`} hreflang={other} lang={other}><span class="font-semibold">{t("langLabel")}</span><span class="text-sm text-muted">{app.lang === "fr" ? "Français" : "English"} → {other.toUpperCase()}</span></a></li>
  </ul>
  <ul class="card mt-4 divide-y divide-line/60 overflow-hidden">
    <li><a class={row} href={href("coverage")}><span class="font-semibold">{t("coverage")}</span><span class="text-muted" aria-hidden="true">›</span></a></li>
    <li><a class={row} href={href("about")}><span class="font-semibold">{t("about")}</span><span class="text-muted" aria-hidden="true">›</span></a></li>
  </ul>
</div>
