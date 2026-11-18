<script lang="ts" module>
  export type IconName = "shield" | "flag" | "globe" | "trophy" | "target" | "ball" | "list";
</script>

<script lang="ts">
  // Icônes au trait (24 × 24, une seule épaisseur), pour les rubriques : même dessin que `Trophy`.
  let { name, size = 18 }: { name: IconName; size?: number } = $props();
  const PATHS: Record<IconName, string[]> = {
    shield: ["M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"],
    flag: ["M6 21V4", "M6 5h11l-2 4 2 4H6"],
    globe: ["M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z", "M3 12h18", "M12 3c2.5 2.5 3.5 5.5 3.5 9s-1 6.5-3.5 9c-2.5-2.5-3.5-5.5-3.5-9s1-6.5 3.5-9z"],
    trophy: ["M8 4h8v5a4 4 0 0 1-8 0z", "M8 6H5.5a2 2 0 0 0 0 4H8M16 6h2.5a2 2 0 0 1 0 4H16", "M12 13v4M8.5 20h7M10 17h4"],
    target: ["M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z", "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z", "M12 11.5a.5.5 0 1 0 0 1 .5.5 0 0 0 0-1z"],
    ball: ["M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z", "M12 8l3.5 2.5-1.3 4.1H9.8L8.5 10.5z", "M12 8V3M15.5 10.5L20 9M14.2 14.6l2.6 3.7M9.8 14.6l-2.6 3.7M8.5 10.5L4 9"],
    list: ["M8 6h12M8 12h12M8 18h12", "M4 6h.01M4 12h.01M4 18h.01"],
  };
</script>

<svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  {#each PATHS[name] as d}<path {d} />{/each}
</svg>
