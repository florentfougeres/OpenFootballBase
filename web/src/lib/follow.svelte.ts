// Suivis : des clubs, joueurs et compétitions épinglés, gardés dans le navigateur de l'appareil (aucun compte, rien d'envoyé).
// On garde le chemin sans la langue (`club/Arsenal_F.C.`) : le lien est reconstruit dans la langue courante.
export type FollowKind = "club" | "player" | "comp";
export type Follow = { kind: FollowKind; id: string; label: string; sub: string; path: string };

const KEY = "openfootballbase.follows";
const read = (): Follow[] => {
  try { const v = JSON.parse(localStorage.getItem(KEY) ?? "[]"); return Array.isArray(v) ? v.filter((x) => x && x.kind && x.id && x.path) : []; } catch { return []; }
};

export const follows = $state({ items: read() });

const save = () => { try { localStorage.setItem(KEY, JSON.stringify(follows.items)); } catch { /* stockage indisponible : le suivi vaut pour la session */ } };

export const isFollowed = (kind: FollowKind, id: string) => follows.items.some((f) => f.kind === kind && f.id === id);

/** Ajoute ou retire un suivi ; renvoie vrai quand il vient d'être ajouté. */
export function toggleFollow(f: Follow): boolean {
  const on = isFollowed(f.kind, f.id);
  follows.items = on ? follows.items.filter((x) => !(x.kind === f.kind && x.id === f.id)) : [f, ...follows.items];
  save();
  return !on;
}
