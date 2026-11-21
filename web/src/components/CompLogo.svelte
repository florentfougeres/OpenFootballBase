<script lang="ts">
  import { app } from "../lib/app.svelte";
  import Trophy from "./Trophy.svelte";

  // Logo d'une compétition (infobox Wikipedia) sur fond blanc, pour rester lisible en thème sombre ; une compétition sans logo garde une coupe dessinée.
  let { code, size = 28 }: { code: string; size?: number } = $props();
  const url = $derived((app.comps.get(code)?.logo_url as string | null | undefined) ?? null);
  let broken = $state(false);                       // logo supprimé de Wikimedia depuis la publication : la coupe dessinée prend le relais
  $effect(() => { url; broken = false; });
  const shown = $derived(url && !broken);
</script>

<span class="grid shrink-0 place-items-center overflow-hidden rounded-md {shown ? 'bg-white p-0.5' : 'bg-surface-2 text-muted'}" style="width:{size}px;height:{size}px" aria-hidden="true">
  {#if shown}<img class="size-full object-contain" src={url} alt="" loading="lazy" onerror={() => (broken = true)} />{:else}<Trophy size={Math.round(size * 0.6)} />{/if}
</span>
