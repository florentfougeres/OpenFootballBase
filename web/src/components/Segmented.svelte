<script lang="ts" generics="K extends string">
  // Contrôle d'onglets / de segments : un seul composant pour le club, le joueur et « Explorer ».
  // `tabs` : onglets (flèches gauche/droite, Début, Fin) ; sinon boutons à bascule (aria-pressed).
  let { items, value, onselect, label, tabs = true, idPrefix = "seg", class: cls = "" }:
    { items: { key: K; label: string; short?: string }[]; value: K; onselect: (k: K) => void; label: string; tabs?: boolean; idPrefix?: string; class?: string } = $props();

  // Trop d'onglets pour la largeur d'un téléphone : la barre défile, et l'onglet actif reste visible.
  $effect(() => { value; document.getElementById(`${idPrefix}-${value}`)?.scrollIntoView({ inline: "nearest", block: "nearest" }); });

  function onKey(e: KeyboardEvent) {
    if (!tabs) return;
    const i = items.findIndex((x) => x.key === value);
    const n = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : e.key === "Home" ? 0 : e.key === "End" ? items.length - 1 : -1;
    if (n < 0) return;
    e.preventDefault();
    const k = items[(n + items.length) % items.length].key;
    onselect(k);
    setTimeout(() => document.getElementById(`${idPrefix}-${k}`)?.focus(), 0);
  }
</script>

<div class="flex w-full overflow-x-auto rounded-xl border border-line bg-surface p-0.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:inline-flex sm:w-auto {cls}" role={tabs ? "tablist" : "group"} aria-label={label}>
  {#each items as it (it.key)}
    <button type="button" id="{idPrefix}-{it.key}" role={tabs ? "tab" : undefined} aria-selected={tabs ? value === it.key : undefined} aria-pressed={tabs ? undefined : value === it.key}
      tabindex={tabs && value !== it.key ? -1 : 0} onkeydown={onKey}
      class="min-h-10 min-w-fit flex-1 whitespace-nowrap rounded-[0.6rem] px-1.5 text-sm font-semibold transition sm:min-h-9 sm:flex-none sm:px-4 {value === it.key ? 'bg-accent text-accent-fg' : 'text-muted hover:text-fg active:bg-surface-2'}"
      onclick={() => onselect(it.key)}>{#if it.short}<span class="sm:hidden">{it.short}</span><span class="max-sm:hidden">{it.label}</span>{:else}{it.label}{/if}</button>
  {/each}
</div>
