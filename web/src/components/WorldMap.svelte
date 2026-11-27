<script lang="ts">
  import { app, countryOf, enc, href, t } from "../lib/app.svelte";
  import { clubName } from "../lib/format";
  import Sheet from "./Sheet.svelte";
  import Logo from "./Logo.svelte";
  import Flag from "./Flag.svelte";
  import Spinner from "./Spinner.svelte";
  import { STYLE, isDark, loadMapLibre, watchTheme } from "../lib/maplib";

  // Carte d'Explorer : les pays (cercle = nombre de clubs) ou les clubs (regroupés, puis écussons), sur un fond de carte CARTO clair (Positron) ou sombre (Dark Matter) selon le thème.
  // Le zoom descend jusqu'à une région, jamais jusqu'à la rue ; là où des clubs se recouvrent encore, un groupe s'ouvre en liste. Les repères sont de vrais liens et boutons (clavier, lecteur d'écran).
  // Les groupes sont calculés ici (supercluster, au zoom entier courant) et non par la source de MapLibre : une seule couche de groupes à la fois, jamais deux niveaux superposés.
  let { mode }: { mode: "clubs" | "countries" } = $props();

  const MAX_ZOOM = 9;
  const CLUSTER_MAX_ZOOM = 7;                           // au-delà, plus aucun groupe : chaque club a son repère
  const CREST_ZOOM = 5.5;                               // à partir de là, un club isolé s'affiche avec son écusson
  const NATIONS = ["ENG", "SCO", "WAL", "NIR"];        // le fond de pays n'a qu'un Royaume-Uni (GBR) : un tap sur lui propose les quatre nations

  let host: HTMLDivElement | undefined = $state();
  let phase = $state<"loading" | "ready" | "error">("loading");
  let list = $state<{ title: string; items: { key: string; to: string; name: string; sub: string; club?: any; code?: string }[] } | null>(null);

  // Clubs avec un vrai effectif, puis ceux qui ont des coordonnées (les référentiels sont des Map non réactives : on lit `app.ready`).
  const squadClubs = $derived.by(() => { app.ready; return [...app.clubs.values()].filter((c) => app.squadClubs.has(c.wikipedia_title as string)); });
  const clubs = $derived(squadClubs.filter((c) => c.lat != null && c.lon != null));
  const withoutCoords = $derived(squadClubs.length - clubs.length);
  const perCountry = $derived.by(() => {
    const m = new Map<string, number>();
    for (const c of squadClubs) if (c.country_code) m.set(c.country_code as string, (m.get(c.country_code as string) ?? 0) + 1);
    return m;
  });

  const css = (v: string) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const reduce = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
  const BUBBLE = "grid place-items-center rounded-full border-2 border-white bg-accent font-bold tabular-nums text-accent-fg shadow-md transition active:scale-95 hover:scale-110 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-fg";

  $effect(() => {
    if (!host) return;
    const el = host;
    let map: any, off = false;
    const markers = new Map<string, { m: any; el: HTMLElement }>();
    const cleanups: (() => void)[] = [];
    // lus ici, hors de l'async : ce sont les dépendances de l'effet
    const wanted = mode, clubList = clubs, counts = perCountry;
    void app.lang;

    (async () => {
      try {
        const [maplibre, SC, geo] = await Promise.all([
          loadMapLibre(),
          import("supercluster"),
          wanted === "countries" ? fetch(new URL(import.meta.env.BASE_URL + "geo/countries.json", location.href)).then((r) => r.json()) : Promise.resolve(null),
        ]);
        if (off) return;
        const Supercluster = (SC as any).default ?? SC;

        let dark = isDark();
        map = new maplibre.Map({
          container: el, attributionControl: false, dragRotate: false, pitchWithRotate: false, touchPitch: false,
          minZoom: 0.6, maxZoom: MAX_ZOOM, renderWorldCopies: false, maxBounds: [[-180, -58], [180, 80]],
          style: dark ? STYLE.dark : STYLE.light, center: [15, 25], zoom: 1,
        });
        map.touchZoomRotate.disableRotation();
        map.addControl(new maplibre.NavigationControl({ showCompass: false }), "top-right");
        map.addControl(new maplibre.AttributionControl({ compact: true, customAttribution: wanted === "countries" ? "Natural Earth" : undefined }), "bottom-right");
        cleanups.push(() => map.remove());
        const failed = setTimeout(() => { if (phase === "loading") phase = "error"; }, 20000);        // fond injoignable : on le dit, la liste reste là
        cleanups.push(() => clearTimeout(failed));

        // Pays (mode « Pays ») : leur nombre de clubs et leur nom dans la langue de l'app ; teinte et survol posés SOUS les étiquettes du fond.
        if (geo) {
          for (const f of geo.features) {
            const code = f.properties.c as string;
            f.properties.k = code === "GBR" ? NATIONS.reduce((n, x) => n + (counts.get(x) ?? 0), 0) : counts.get(code) ?? 0;
            f.properties.nm = code === "GBR" ? (app.lang === "fr" ? "Royaume-Uni" : "United Kingdom") : countryOf(code).name || f.properties.n;
          }
        }
        // Un changement de fond (thème) vide le style : sources et couches sont reposées à chaque `style.load`.
        const setup = () => {
          if (!geo || map.getSource("countries")) return;
          const before = map.getStyle().layers.find((l: any) => l.type === "symbol")?.id;
          map.addSource("countries", { type: "geojson", data: geo });
          map.addLayer({ id: "land", type: "fill", source: "countries", filter: [">", ["get", "k"], 0], paint: { "fill-color": css("--accent"), "fill-opacity": 0.16 } }, before);
          map.addLayer({ id: "hover", type: "fill", source: "countries", filter: ["==", ["get", "c"], ""], paint: { "fill-color": css("--accent"), "fill-opacity": 0.32 } }, before);
        };
        map.on("style.load", setup);
        await new Promise<void>((res) => map.once("load", () => res()));
        if (off) return;
        clearTimeout(failed);
        map.fitBounds([[-125, -40], [150, 62]], { padding: 8, animate: false });          // après le chargement : la boîte a alors sa taille

        const applyTheme = () => {
          const d = isDark();
          if (d === dark) return;
          dark = d;
          map.setStyle(d ? STYLE.dark : STYLE.light);
        };
        cleanups.push(watchTheme(applyTheme));

        // Les repères grossissent avec le zoom (cercles de pays) : petits sur la carte du monde où l'Europe est dense, pleins à l'échelle d'un pays.
        const scale = () => el.style.setProperty("--k", String(Math.max(0.5, Math.min(1, 0.5 + (map.getZoom() - 1) * 0.2))));
        const crests = () => el.setAttribute("data-crest", map.getZoom() >= CREST_ZOOM ? "1" : "0");
        scale(); crests();
        map.on("zoom", () => { scale(); crests(); });

        // MapLibre place chaque repère avec un `transform` sur son élément racine : les transitions et l'échelle du survol vont sur l'élément INTERNE, sinon le repère glisse et saute au survol.
        const place = (key: string, lngLat: [number, number], build: () => HTMLElement, z?: number) => {
          let e = markers.get(key);
          if (!e) {
            const wrap = document.createElement("div");
            if (z != null) wrap.style.zIndex = String(z);
            wrap.append(build());
            e = { el: wrap, m: new maplibre.Marker({ element: wrap, anchor: "center" }).setLngLat(lngLat).addTo(map) };
            markers.set(key, e);
          }
          return e;
        };
        const flyTo = (center: [number, number], zoom: number) => map.easeTo({ center, zoom: Math.min(zoom, MAX_ZOOM), duration: reduce() ? 0 : 500 });

        if (wanted === "countries") {
          const lookup = new Map<string, any>(geo.features.map((f: any) => [f.properties.c, f.properties]));
          const row = (code: string) => ({ key: code, to: href("country", code), name: countryOf(code).name, sub: String(counts.get(code) ?? 0), code });
          const open = (code: string) => {
            if (code === "GBR") list = { title: lookup.get("GBR")?.nm ?? "United Kingdom", items: NATIONS.filter((x) => counts.has(x)).map(row) };
            else location.hash = href("country", code);
          };
          const ranked = [...lookup.values()].filter((p) => p.k > 0).sort((a, b) => b.k - a.k);
          ranked.forEach((p, i) => {
            const size = Math.round(24 + Math.min(20, Math.sqrt(p.k) * 2.2));
            place(p.c, [p.cx, p.cy], () => {
              const b = document.createElement("button");
              b.type = "button";
              b.className = BUBBLE;
              b.style.cssText = `width:calc(${size}px * var(--k,1));height:calc(${size}px * var(--k,1));font-size:calc(${size > 32 ? 14 : 11}px * var(--k,1))`;
              b.textContent = String(p.k);
              b.setAttribute("aria-label", `${p.nm} : ${p.k} ${p.k > 1 ? t("clubsN") : t("clubsN1")}`);
              b.addEventListener("click", () => open(p.c));
              return b;
            }, 1000 - i);
          });
          map.on("click", "land", (e: any) => { const p = e.features?.[0]?.properties; if (p?.k > 0) open(p.c); });
          map.on("mousemove", "land", (e: any) => {
            const p = e.features?.[0]?.properties;
            map.getCanvas().style.cursor = p?.k > 0 ? "pointer" : "";
            map.setFilter("hover", ["==", ["get", "c"], p?.k > 0 ? p.c : ""]);
          });
          map.on("mouseleave", "land", () => { map.getCanvas().style.cursor = ""; map.setFilter("hover", ["==", ["get", "c"], ""]); });
        } else {
          const index = new Supercluster({ radius: 36, maxZoom: CLUSTER_MAX_ZOOM, minPoints: 2 });
          index.load(clubList.map((c) => ({ type: "Feature", geometry: { type: "Point", coordinates: [c.lon, c.lat] },
            properties: { t: c.wikipedia_title, n: clubName(c), city: c.city ?? "", lg: c.logo_url ?? "", co: c.colors_hex ?? "" } })));

          const clusterPin = (id: number, n: number, lng: number, lat: number) => {
            const size = Math.round(28 + Math.min(24, Math.log2(n) * 5));
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = BUBBLE;
            btn.style.cssText = `width:${size}px;height:${size}px;font-size:${size > 40 ? 14 : 12}px`;
            btn.textContent = String(n);
            btn.setAttribute("aria-label", `${n} ${t("clubsN")}`);
            btn.addEventListener("click", () => {
              const z = index.getClusterExpansionZoom(id);
              if (z > MAX_ZOOM || map.getZoom() >= MAX_ZOOM - 0.05) {          // échelle maximale : le groupe s'ouvre en liste
                const leaves = index.getLeaves(id, 80, 0);
                list = { title: `${n} ${t("clubsN")}`, items: leaves.map((l: any) => ({ key: l.properties.t, to: href("club", enc(l.properties.t)), name: l.properties.n, sub: l.properties.city, club: app.clubs.get(l.properties.t) })) };
              } else flyTo([lng, lat], z);
            });
            return btn;
          };
          // Club isolé : un point de loin, l'écusson ENTIER de près (jamais rogné par un rond) ; le nom apparaît au survol et au focus clavier, le clic ouvre la fiche.
          const clubPin = (p: any) => {
            const a = document.createElement("a");
            a.href = href("club", enc(p.t));
            a.className = "club-pin group relative block";
            a.setAttribute("aria-label", p.n + (p.city ? ` (${p.city})` : ""));
            const dot = document.createElement("span");
            dot.className = "club-dot block size-4 rounded-full border-2 border-white bg-accent shadow-md transition group-hover:scale-150";
            const crest = document.createElement("span");
            crest.className = "club-crest block size-9 overflow-hidden rounded-xl bg-white p-1 shadow-md ring-1 ring-black/15 transition group-hover:scale-110 group-focus-visible:scale-110";
            if (p.lg) {
              const img = document.createElement("img");
              img.src = p.lg; img.alt = ""; img.loading = "lazy"; img.className = "block size-full object-contain";
              img.onerror = () => { img.remove(); crest.style.background = p.co || "var(--accent)"; };
              crest.append(img);
            } else crest.style.background = p.co || "var(--accent)";
            const tip = document.createElement("span");
            tip.className = "club-tip pointer-events-none absolute bottom-full left-1/2 z-10 mb-1.5 -translate-x-1/2 whitespace-nowrap rounded-lg bg-fg px-2.5 py-1 text-xs font-semibold text-bg opacity-0 shadow-lg transition group-hover:opacity-100 group-focus-visible:opacity-100";
            tip.textContent = p.n;
            a.append(dot, crest, tip);
            return a;
          };

          const refresh = () => {
            const b = map.getBounds(), z = Math.min(MAX_ZOOM, Math.floor(map.getZoom())), pad = 2;
            const feats = index.getClusters([Math.max(-180, b.getWest() - pad), Math.max(-85, b.getSouth() - pad), Math.min(180, b.getEast() + pad), Math.min(85, b.getNorth() + pad)], z);
            const seen = new Set<string>();
            for (const f of feats) {
              const [lng, lat] = f.geometry.coordinates as [number, number], p = f.properties;
              const key = p.cluster ? `c${p.cluster_id}` : `p${p.t}`;
              seen.add(key);
              place(key, [lng, lat], () => (p.cluster ? clusterPin(p.cluster_id, p.point_count, lng, lat) : clubPin(p)));
            }
            for (const [key, e] of markers) if (!seen.has(key)) { e.m.remove(); markers.delete(key); }
          };
          // Recalculé à chaque image du mouvement (et non à son arrêt) : au seuil de zoom, les groupes se défont tout de suite au lieu d'attendre la fin de l'animation.
          let raf = 0;
          map.on("move", () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; refresh(); }); });
          map.on("moveend", refresh);
          cleanups.push(() => cancelAnimationFrame(raf));
          refresh();
        }
        phase = "ready";
      } catch (e) {
        console.error(e);
        if (!off) phase = "error";
      }
    })();

    return () => { off = true; cleanups.forEach((f) => f()); for (const e of markers.values()) e.m.remove(); markers.clear(); };
  });
</script>

<div class="relative mt-4 overflow-hidden rounded-2xl border border-line bg-surface-2" role="region" aria-label={mode === "clubs" ? t("mapClubs") : t("mapCountries")}>
  <div bind:this={host} class="map map-themed h-[max(20rem,calc(100dvh-19rem))] w-full sm:h-[min(68dvh,46rem)]"></div>
  {#if phase === "loading"}<div class="absolute inset-0 grid place-items-center bg-surface-2"><Spinner /></div>{/if}
  {#if phase === "error"}<p class="absolute inset-0 grid place-items-center p-6 text-center text-sm text-muted">{t("mapError")}</p>{/if}
  {#if phase === "ready"}
    <p class="pointer-events-none absolute left-3 top-3 max-w-[calc(100%-5.5rem)] rounded-lg bg-surface/90 px-2.5 py-1 text-xs font-medium text-muted shadow-sm">
      {mode === "clubs" ? `${clubs.length} ${t("clubsN")}${withoutCoords > 0 ? `, ${withoutCoords} ${t("mapNoCoords")}` : ""}` : t("mapCountriesHint")}
    </p>
  {/if}
</div>

<Sheet open={!!list} onclose={() => (list = null)} title={list?.title ?? ""}>
  {#if list}
    <ul class="divide-y divide-line/40">
      {#each list.items as it (it.key)}
        <li>
          <a class="row" href={it.to} onclick={() => (list = null)}>
            {#if it.club}<Logo club={it.club} size={32} />{:else if it.code}<Flag code={countryOf(it.code).flag} label={it.name} size={24} />{/if}
            <span class="min-w-0 flex-1"><span class="block truncate font-semibold">{it.name}</span>{#if it.sub && !it.code}<span class="block truncate text-xs text-muted">{it.sub}</span>{/if}</span>
            {#if it.code}<span class="shrink-0 text-xs tabular-nums text-muted">{it.sub}</span>{/if}
            <span class="shrink-0 text-muted" aria-hidden="true">›</span>
          </a>
        </li>
      {/each}
    </ul>
  {/if}
</Sheet>

<style>
  /* Point ou écusson selon le zoom (l'attribut est posé par le composant) ; le repère survolé passe devant les autres. */
  :global(.map[data-crest="1"] .club-dot), :global(.map[data-crest="0"] .club-crest) { display: none; }
  .map :global(.maplibregl-marker:hover), .map :global(.maplibregl-marker:focus-within) { z-index: 5; }
  .map :global(.club-pin:focus-visible) { outline: 2px solid var(--fg); outline-offset: 3px; border-radius: 0.75rem; }
  @media (hover: none) { .map :global(.club-tip) { display: none; } }
</style>
