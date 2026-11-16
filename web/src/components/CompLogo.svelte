<script lang="ts">
  import { app } from "../lib/app.svelte";
  import Trophy from "./Trophy.svelte";

  // Logo d'une compétition (infobox Wikipedia) sur fond blanc, pour rester lisible en thème sombre ; une compétition sans logo garde une coupe dessinée.
  let { code, size = 28 }: { code: string; size?: number } = $props();
  const url = $derived((app.comps.get(code)?.logo_url as string | null | undefined) ?? null);
</script>

<span class="grid shrink-0 place-items-center overflow-hidden rounded-md {url ? 'bg-white p-0.5' : 'bg-surface-2 text-muted'}" style="width:{size}px;height:{size}px" aria-hidden="true">
  {#if url}<img class="size-full object-contain" src={url} alt="" loading="lazy" />{:else}<Trophy size={Math.round(size * 0.6)} />{/if}
</span>
