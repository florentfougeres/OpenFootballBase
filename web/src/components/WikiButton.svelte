<script lang="ts">
  import { app, t } from "../lib/app.svelte";
  // urls : langue -> URL de la page Wikipedia ; langue de l'app, sinon anglais, sinon la première disponible.
  // `compact` : un bouton icône de 44 px (téléphone) ; le libellé reste lisible par les lecteurs d'écran.
  let { urls, kind, fallbackKey = "wikiFallback", compact = false }: { urls: Record<string, string>; kind: string; fallbackKey?: string; compact?: boolean } = $props();
  const lang = $derived(urls[app.lang] ? app.lang : urls.en ? "en" : Object.keys(urls)[0]);
</script>

{#if lang && compact}
  <a class="inline-flex min-h-11 min-w-11 items-center justify-center rounded-xl border border-line bg-surface transition hover:bg-surface-2 active:scale-[0.97]" href={urls[lang]} hreflang={lang}
    target="_blank" rel="noopener" title="{t(kind)}, {lang.toUpperCase()}">
    <svg viewBox="0 0 24 24" class="size-[18px]" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" /></svg>
    <span class="sr-only">{t(kind)}, {lang.toUpperCase()}{lang !== app.lang ? ` (${t(lang === "en" ? "wikiFallback" : fallbackKey)})` : ""}</span>
  </a>
{:else if lang}
  <a class="btn-ghost" href={urls[lang]} hreflang={lang} target="_blank" rel="noopener">
    {t(kind)} <span class="text-muted">({lang.toUpperCase()})</span>
  </a>
  {#if lang !== app.lang}<span class="text-xs text-muted">({t(lang === "en" ? "wikiFallback" : fallbackKey)})</span>{/if}
{/if}
