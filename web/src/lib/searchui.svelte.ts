// État partagé de la recherche : une surcouche (plein écran sur mobile, palette centrée sur grand écran) ouverte par `bar`, par « / » ou par ⌘K.
export const searchUi = $state({ bar: false });

export const focusSearch = () => { searchUi.bar = true; };

// Recherches récentes : un confort propre au navigateur, jamais envoyé nulle part (localStorage peut être absent ou plein).
const KEY = "openfootballbase.recentSearches";
export type Recent = { kind: "player" | "club" | "comp" | "country"; label: string; sub: string; to: string };

export function readRecent(): Recent[] {
  try { const v = JSON.parse(localStorage.getItem(KEY) ?? "[]"); return Array.isArray(v) ? v.slice(0, 8) : []; } catch { return []; }
}
export function pushRecent(r: Recent) {
  try { localStorage.setItem(KEY, JSON.stringify([r, ...readRecent().filter((x) => x.to !== r.to)].slice(0, 8))); } catch { /* stockage indisponible */ }
}
export function clearRecent() {
  try { localStorage.removeItem(KEY); } catch { /* stockage indisponible */ }
}
