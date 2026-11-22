<script lang="ts">
  // Étiquette de poste (GK, DF, MF, FW) : le libellé porte l'information, la teinte n'est qu'un repère.
  let { pos, small = false }: { pos: string | null | undefined; small?: boolean } = $props();
  const CLS: Record<string, string> = { GK: "bg-warn-soft text-warn", DF: "bg-info-soft text-info", MF: "bg-accent-soft text-accent", FW: "bg-fg/10 text-fg" };
</script>

{#if pos}
  <span class="inline-block shrink-0 rounded-md text-center font-bold {small ? 'px-1 text-[0.6875rem]' : 'min-w-9 px-1.5 py-0.5 text-xs'} {CLS[pos] ?? 'bg-surface-2 text-muted'}">{pos}</span>
{/if}
