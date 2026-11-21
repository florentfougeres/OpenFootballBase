<script lang="ts">
  import { href, t } from "../lib/app.svelte";
  let { trail = [] }: { trail?: { label: string; to: string }[] } = $props();
</script>

<nav class="-mt-2 mb-2 flex flex-wrap items-center gap-x-1.5 text-sm text-muted sm:mt-0 sm:mb-4" aria-label="Fil d'Ariane">
  <a class="inline-flex min-h-11 items-center hover:text-fg hover:underline sm:min-h-0" href={href("")}>{t("home")}</a>
  {#each trail as c}
    <span aria-hidden="true">›</span>
    <a class="inline-flex min-h-11 items-center hover:text-fg hover:underline sm:min-h-0" href={c.to}>{c.label}</a>
  {/each}
</nav>
