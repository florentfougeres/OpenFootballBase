<script lang="ts">
  import { app, t } from "../lib/app.svelte";
  import { STYLE, isDark, loadMapLibre, watchTheme } from "../lib/maplib";

  // Mini-carte de la fiche club : l'écusson posé sur la position du club, à l'échelle d'une région (jamais d'une rue).
  // MapLibre n'est téléchargé que lorsque la carte entre à l'écran ; les gestes à deux doigts (Ctrl + molette sur ordinateur) évitent de bloquer le défilement de la page.
  let { lat, lon, name, logo = null, color = null }: { lat: number; lon: number; name: string; logo?: string | null; color?: string | null } = $props();

  let host: HTMLDivElement | undefined = $state();
  let failed = $state(false);

  $effect(() => {
    if (!host) return;
    const el = host, x = lon, y = lat, label = name, img = logo, bg = color, fr = app.lang === "fr";
    let map: any, off = false, io: IntersectionObserver | undefined, unwatch: (() => void) | undefined;

    const start = async () => {
      try {
        const maplibre = await loadMapLibre();
        if (off) return;
        let dark = isDark();
        map = new maplibre.Map({
          container: el, attributionControl: false, dragRotate: false, pitchWithRotate: false, touchPitch: false, cooperativeGestures: true,
          minZoom: 3, maxZoom: 9, style: dark ? STYLE.dark : STYLE.light, center: [x, y], zoom: 6.5,
          locale: fr
            ? { "CooperativeGesturesHandler.WindowsHelpText": "Ctrl + molette pour zoomer", "CooperativeGesturesHandler.MacHelpText": "⌘ + molette pour zoomer", "CooperativeGesturesHandler.MobileHelpText": "Utilisez deux doigts pour déplacer la carte" }
            : undefined,
        });
        map.addControl(new maplibre.NavigationControl({ showCompass: false }), "top-right");
        map.addControl(new maplibre.AttributionControl({ compact: true }), "bottom-right");

        // Le repère : l'écusson entier sur une tuile blanche (jamais rogné), ou une pastille de la couleur du club.
        const pin = document.createElement("div");
        pin.className = "grid size-10 place-items-center rounded-xl bg-white p-1 shadow-md ring-1 ring-black/15";
        if (img) {
          const i = document.createElement("img");
          i.src = img; i.alt = ""; i.className = "block size-full object-contain";
          i.onerror = () => { i.remove(); pin.style.background = bg || "var(--accent)"; };
          pin.append(i);
        } else pin.style.background = bg || "var(--accent)";
        pin.setAttribute("role", "img"); pin.setAttribute("aria-label", label);
        new maplibre.Marker({ element: pin, anchor: "center" }).setLngLat([x, y]).addTo(map);

        unwatch = watchTheme(() => { const d = isDark(); if (d !== dark) { dark = d; map.setStyle(d ? STYLE.dark : STYLE.light); } });
      } catch (e) {
        console.error(e);
        if (!off) failed = true;
      }
    };

    // Chargement à l'entrée à l'écran (un peu avant), pas à l'ouverture de la page.
    io = new IntersectionObserver((entries) => { if (entries.some((e) => e.isIntersecting)) { io?.disconnect(); start(); } }, { rootMargin: "200px" });
    io.observe(el);
    return () => { off = true; io?.disconnect(); unwatch?.(); map?.remove(); };
  });
</script>

<div class="relative overflow-hidden rounded-2xl border border-line bg-surface-2" role="region" aria-label={`${t("map")} · ${name}`}>
  <div bind:this={host} class="map-themed h-44 w-full sm:h-56"></div>
  {#if failed}<p class="absolute inset-0 grid place-items-center p-4 text-center text-sm text-muted">{t("mapError")}</p>{/if}
</div>
