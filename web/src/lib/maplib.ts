// MapLibre GL JS, chargé à la demande (le moteur pèse ≈ 300 Ko compressés : seules les pages qui affichent une carte le téléchargent) et fond de carte CARTO clair/sombre selon le thème.
const BASE = "https://basemaps.cartocdn.com/gl/";
export const STYLE = { light: BASE + "positron-gl-style/style.json", dark: BASE + "dark-matter-gl-style/style.json" };

/** Thème sombre : forcé (`data-theme`) ou, à défaut, celui du système (l'app est sombre sauf demande contraire). */
export const isDark = (): boolean => {
  const th = document.documentElement.dataset.theme;
  return th === "dark" || (th !== "light" && !matchMedia("(prefers-color-scheme: light)").matches);
};

let loading: Promise<any> | null = null;
/** MapLibre prêt à l'emploi : feuille de style incluse, worker lancé depuis un blob (même chemin en développement et en production ; la CSP autorise `worker-src blob:`). */
export function loadMapLibre(): Promise<any> {
  return (loading ??= (async () => {
    const [ml, worker] = await Promise.all([
      import("maplibre-gl"),
      import("maplibre-gl/dist/maplibre-gl-worker.mjs?raw"),
      import("maplibre-gl/dist/maplibre-gl.css"),
    ]);
    const maplibre = (ml as any).default ?? ml;
    maplibre.setWorkerUrl(URL.createObjectURL(new Blob([(worker as any).default], { type: "text/javascript" })));
    return maplibre;
  })());
}

/** Appelle `onChange` quand le thème change (réglage de l'app ou du système) ; renvoie de quoi se désabonner. */
export function watchTheme(onChange: () => void): () => void {
  const mo = new MutationObserver(onChange);
  mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  const mq = matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener("change", onChange);
  return () => { mo.disconnect(); mq.removeEventListener("change", onChange); };
}
