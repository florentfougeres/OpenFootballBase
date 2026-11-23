<script lang="ts">
  import { app } from "../lib/app.svelte";
  import { clubOf } from "../lib/format";
  import type { Follow } from "../lib/follow.svelte";
  import Logo from "./Logo.svelte";
  import CompLogo from "./CompLogo.svelte";

  // Vignette d'un suivi : l'écusson d'un club, le logo d'une compétition, les initiales d'un joueur.
  let { f, size = 40 }: { f: Follow; size?: number } = $props();
  // Les référentiels (clubs, compétitions) sont des Map non réactives : on lit `app.ready` pour recalculer une fois la base chargée.
  const club = $derived.by(() => { app.ready; return f.kind === "club" ? clubOf(f.id) : undefined; });
  const initials = $derived(f.label.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase());
</script>

{#if club}
  <Logo {club} {size} />
{:else if f.kind === "comp"}
  <!-- lit `app.comps` à l'affichage : le logo apparaît dès que la base est prête -->
  {#key app.ready}<CompLogo code={f.id} {size} />{/key}
{:else}
  <span class="grid shrink-0 place-items-center rounded-full bg-surface-2 text-sm font-bold text-muted" style:width="{size}px" style:height="{size}px" aria-hidden="true">{initials}</span>
{/if}
