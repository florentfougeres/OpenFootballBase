<script lang="ts">
  import { app } from "../lib/app.svelte";
  import { clubOf } from "../lib/format";
  import type { Follow } from "../lib/follow.svelte";
  import Logo from "./Logo.svelte";

  // Vignette d'un suivi : l'écusson d'un club, le logo d'une compétition, les initiales d'un joueur.
  let { f, size = 40 }: { f: Follow; size?: number } = $props();
  // Les référentiels (clubs, compétitions) sont des Map non réactives : on lit `app.ready` pour recalculer une fois la base chargée.
  const comp = $derived.by(() => { app.ready; return f.kind === "comp" ? app.comps.get(f.id) : undefined; });
  const club = $derived.by(() => { app.ready; return f.kind === "club" ? clubOf(f.id) : undefined; });
  const initials = $derived(f.label.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase());
</script>

{#if club}
  <Logo {club} {size} />
{:else if f.kind === "comp" && comp?.logo_url}
  <span class="block shrink-0 overflow-hidden rounded-lg bg-white p-1" style:width="{size}px" style:height="{size}px"><img class="size-full object-contain" src={comp.logo_url} alt="" loading="lazy" /></span>
{:else}
  <span class="grid shrink-0 place-items-center rounded-full bg-surface-2 text-sm font-bold text-muted" style:width="{size}px" style:height="{size}px" aria-hidden="true">{f.kind === "comp" ? "★" : initials}</span>
{/if}
