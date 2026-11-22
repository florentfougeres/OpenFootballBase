<script lang="ts">
  import { t } from "../lib/app.svelte";

  // Forme d'une équipe : les derniers résultats en pastilles V / N / D (vert, gris, rouge) ; la lettre porte le sens, la couleur le renforce.
  let { form, n = 5 }: { form: ("w" | "d" | "l")[]; n?: number } = $props();
  const KEY = { w: "resW", d: "resD", l: "resL" } as const;
  const CLS = { w: "bg-accent text-accent-fg", d: "bg-surface-2 text-muted", l: "bg-bad-soft text-bad" } as const;
  const last = $derived(form.slice(-n));
</script>

{#if last.length}
  <span class="inline-flex gap-1" role="img" aria-label="{t('resForm')} : {last.map((f) => t(KEY[f])).join(' ')}">
    {#each last as f}<span class="grid size-5 place-items-center rounded-md text-[0.6875rem] font-bold {CLS[f]}" aria-hidden="true">{t(KEY[f])}</span>{/each}
  </span>
{/if}
