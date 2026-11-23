<script lang="ts">
  import { app, t } from "../lib/app.svelte";
  import { follows, type Follow, type FollowKind } from "../lib/follow.svelte";
  import FollowAvatar from "../components/FollowAvatar.svelte";
  import FollowButton from "../components/FollowButton.svelte";

  // Suivis : les clubs, joueurs et compétitions épinglés sur cet appareil. Les réglages sont dans leur propre page.
  const KINDS: { k: FollowKind; label: string }[] = [{ k: "club", label: "clubs" }, { k: "player", label: "players" }, { k: "comp", label: "allComps" }];
  const by = (k: FollowKind) => follows.items.filter((f) => f.kind === k);
  const row = "flex min-h-14 items-center gap-3 px-4 py-2 text-left no-underline transition hover:bg-surface-2 active:bg-surface-2";
</script>

<h1 class="text-4xl font-extrabold leading-none tracking-tight sm:text-5xl">{t("follows")}</h1>

<div class="mt-5 max-w-3xl">
  {#if !follows.items.length}
    <p class="card p-5 text-muted">{t("followsEmpty")}</p>
  {:else}
    {#each KINDS as g (g.k)}
      {#if by(g.k).length}
        <h2 class="mb-2 mt-6 px-1 text-xs font-semibold uppercase tracking-wide text-muted first:mt-0">{t(g.label)}</h2>
        <ul class="card divide-y divide-line/60 overflow-hidden">
          {#each by(g.k) as f (f.id)}
            <li class="flex items-center pr-2">
              <a class="{row} min-w-0 flex-1" href={`#/${app.lang}/${f.path}`}>
                <FollowAvatar {f} size={36} />
                <span class="min-w-0 flex-1"><span class="block truncate font-semibold">{f.label}</span>{#if f.sub}<span class="block truncate text-sm text-muted">{f.sub}</span>{/if}</span>
              </a>
              <FollowButton item={f} compact />
            </li>
          {/each}
        </ul>
      {/if}
    {/each}
  {/if}
  <p class="mt-3 px-1 text-sm text-muted">{t("followsNote")}</p>
</div>
