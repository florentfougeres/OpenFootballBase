<script lang="ts">
  import { t } from "../lib/app.svelte";
  import { isFollowed, toggleFollow, type Follow } from "../lib/follow.svelte";
  import { notify } from "../lib/toast.svelte";

  let { item, compact = false }: { item: Follow; compact?: boolean } = $props();
  const on = $derived(isFollowed(item.kind, item.id));
  const click = () => notify(t(toggleFollow(item) ? "followAdded" : "followRemoved"));
</script>

<button type="button" aria-pressed={on} onclick={click} title={on ? t("followingBtn") : t("followBtn")}
  class="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border px-4 text-sm font-semibold transition active:scale-[0.97] {on ? 'border-accent bg-accent-soft text-accent' : 'border-line bg-surface hover:bg-surface-2'} {compact ? 'min-w-11 !px-0' : ''}">
  <svg viewBox="0 0 24 24" class="size-[18px]" fill={on ? "currentColor" : "none"} stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z" /></svg>
  {#if !compact}{on ? t("followingBtn") : t("followBtn")}{:else}<span class="sr-only">{on ? t("followingBtn") : t("followBtn")}</span>{/if}
</button>
