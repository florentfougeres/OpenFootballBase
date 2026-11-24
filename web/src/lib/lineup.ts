// Compositions : formations et postes. Les positions (x de 0 à 100 de gauche à droite, y de 0 = but adverse en haut à 100 = son propre but) viennent de Tactica11.
// `line` : la ligne de l'effectif (GK, DF, MF, FW, les valeurs de la colonne `position`) dont on propose d'abord les joueurs pour ce poste.
export type Line = "GK" | "DF" | "MF" | "FW";
export interface Slot { role: string; line: Line; x: number; y: number }

export const FORMATIONS: Record<string, Slot[]> = {
  "4-3-3": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "RB", line: "DF", x: 84, y: 72 },
    { role: "CB", line: "DF", x: 62, y: 77 },
    { role: "CB", line: "DF", x: 38, y: 77 },
    { role: "LB", line: "DF", x: 16, y: 72 },
    { role: "CM", line: "MF", x: 70, y: 40 },
    { role: "DM", line: "MF", x: 50, y: 58 },
    { role: "CM", line: "MF", x: 30, y: 40 },
    { role: "RW", line: "FW", x: 80, y: 26 },
    { role: "ST", line: "FW", x: 50, y: 18 },
    { role: "LW", line: "FW", x: 20, y: 26 },
  ],
  "4-3-3 faux 9": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "RB", line: "DF", x: 84, y: 72 },
    { role: "CB", line: "DF", x: 62, y: 77 },
    { role: "CB", line: "DF", x: 38, y: 77 },
    { role: "LB", line: "DF", x: 16, y: 72 },
    { role: "DM", line: "MF", x: 50, y: 62 },
    { role: "CM", line: "MF", x: 68, y: 50 },
    { role: "CM", line: "MF", x: 32, y: 50 },
    { role: "RW", line: "FW", x: 82, y: 24 },
    { role: "SS", line: "FW", x: 50, y: 32 },
    { role: "LW", line: "FW", x: 18, y: 24 },
  ],
  "4-2-3-1": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "RB", line: "DF", x: 84, y: 72 },
    { role: "CB", line: "DF", x: 62, y: 77 },
    { role: "CB", line: "DF", x: 38, y: 77 },
    { role: "LB", line: "DF", x: 16, y: 72 },
    { role: "DM", line: "MF", x: 64, y: 60 },
    { role: "DM", line: "MF", x: 36, y: 60 },
    { role: "RM", line: "MF", x: 80, y: 38 },
    { role: "AM", line: "MF", x: 50, y: 36 },
    { role: "LM", line: "MF", x: 20, y: 38 },
    { role: "ST", line: "FW", x: 50, y: 16 },
  ],
  "4-4-2": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "RB", line: "DF", x: 84, y: 72 },
    { role: "CB", line: "DF", x: 62, y: 77 },
    { role: "CB", line: "DF", x: 38, y: 77 },
    { role: "LB", line: "DF", x: 16, y: 72 },
    { role: "RM", line: "MF", x: 84, y: 50 },
    { role: "CM", line: "MF", x: 60, y: 54 },
    { role: "CM", line: "MF", x: 40, y: 54 },
    { role: "LM", line: "MF", x: 16, y: 50 },
    { role: "ST", line: "FW", x: 60, y: 20 },
    { role: "ST", line: "FW", x: 40, y: 20 },
  ],
  "4-4-2 losange": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "RB", line: "DF", x: 84, y: 72 },
    { role: "CB", line: "DF", x: 62, y: 77 },
    { role: "CB", line: "DF", x: 38, y: 77 },
    { role: "LB", line: "DF", x: 16, y: 72 },
    { role: "DM", line: "MF", x: 50, y: 62 },
    { role: "CM", line: "MF", x: 70, y: 48 },
    { role: "CM", line: "MF", x: 30, y: 48 },
    { role: "AM", line: "MF", x: 50, y: 36 },
    { role: "ST", line: "FW", x: 60, y: 18 },
    { role: "ST", line: "FW", x: 40, y: 18 },
  ],
  "4-5-1": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "RB", line: "DF", x: 84, y: 72 },
    { role: "CB", line: "DF", x: 62, y: 77 },
    { role: "CB", line: "DF", x: 38, y: 77 },
    { role: "LB", line: "DF", x: 16, y: 72 },
    { role: "RM", line: "MF", x: 85, y: 48 },
    { role: "CM", line: "MF", x: 65, y: 54 },
    { role: "DM", line: "MF", x: 50, y: 62 },
    { role: "CM", line: "MF", x: 35, y: 54 },
    { role: "LM", line: "MF", x: 15, y: 48 },
    { role: "ST", line: "FW", x: 50, y: 18 },
  ],
  "3-5-2": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "CB", line: "DF", x: 72, y: 78 },
    { role: "CB", line: "DF", x: 50, y: 80 },
    { role: "CB", line: "DF", x: 28, y: 78 },
    { role: "RM", line: "MF", x: 88, y: 52 },
    { role: "CM", line: "MF", x: 65, y: 56 },
    { role: "CM", line: "MF", x: 50, y: 60 },
    { role: "CM", line: "MF", x: 35, y: 56 },
    { role: "LM", line: "MF", x: 12, y: 52 },
    { role: "ST", line: "FW", x: 60, y: 20 },
    { role: "ST", line: "FW", x: 40, y: 20 },
  ],
  "3-4-3": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "CB", line: "DF", x: 72, y: 78 },
    { role: "CB", line: "DF", x: 50, y: 80 },
    { role: "CB", line: "DF", x: 28, y: 78 },
    { role: "RM", line: "MF", x: 86, y: 54 },
    { role: "CM", line: "MF", x: 62, y: 58 },
    { role: "CM", line: "MF", x: 38, y: 58 },
    { role: "LM", line: "MF", x: 14, y: 54 },
    { role: "RW", line: "FW", x: 80, y: 26 },
    { role: "ST", line: "FW", x: 50, y: 18 },
    { role: "LW", line: "FW", x: 20, y: 26 },
  ],
  "3-4-2-1": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "CB", line: "DF", x: 72, y: 78 },
    { role: "CB", line: "DF", x: 50, y: 80 },
    { role: "CB", line: "DF", x: 28, y: 78 },
    { role: "RM", line: "MF", x: 86, y: 54 },
    { role: "CM", line: "MF", x: 62, y: 58 },
    { role: "CM", line: "MF", x: 38, y: 58 },
    { role: "LM", line: "MF", x: 14, y: 54 },
    { role: "AM", line: "MF", x: 66, y: 34 },
    { role: "AM", line: "MF", x: 34, y: 34 },
    { role: "ST", line: "FW", x: 50, y: 16 },
  ],
  "5-3-2": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "RB", line: "DF", x: 90, y: 66 },
    { role: "CB", line: "DF", x: 70, y: 78 },
    { role: "CB", line: "DF", x: 50, y: 80 },
    { role: "CB", line: "DF", x: 30, y: 78 },
    { role: "LB", line: "DF", x: 10, y: 66 },
    { role: "CM", line: "MF", x: 68, y: 52 },
    { role: "DM", line: "MF", x: 50, y: 56 },
    { role: "CM", line: "MF", x: 32, y: 52 },
    { role: "ST", line: "FW", x: 60, y: 22 },
    { role: "ST", line: "FW", x: 40, y: 22 },
  ],
  "5-2-3": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "RB", line: "DF", x: 90, y: 66 },
    { role: "CB", line: "DF", x: 70, y: 78 },
    { role: "CB", line: "DF", x: 50, y: 80 },
    { role: "CB", line: "DF", x: 30, y: 78 },
    { role: "LB", line: "DF", x: 10, y: 66 },
    { role: "CM", line: "MF", x: 62, y: 56 },
    { role: "CM", line: "MF", x: 38, y: 56 },
    { role: "RW", line: "FW", x: 80, y: 26 },
    { role: "ST", line: "FW", x: 50, y: 18 },
    { role: "LW", line: "FW", x: 20, y: 26 },
  ],
  "5-4-1": [
    { role: "GK", line: "GK", x: 50, y: 92 },
    { role: "RB", line: "DF", x: 90, y: 66 },
    { role: "CB", line: "DF", x: 70, y: 78 },
    { role: "CB", line: "DF", x: 50, y: 80 },
    { role: "CB", line: "DF", x: 30, y: 78 },
    { role: "LB", line: "DF", x: 10, y: 66 },
    { role: "RM", line: "MF", x: 84, y: 46 },
    { role: "CM", line: "MF", x: 60, y: 52 },
    { role: "CM", line: "MF", x: 40, y: 52 },
    { role: "LM", line: "MF", x: 16, y: 46 },
    { role: "ST", line: "FW", x: 50, y: 18 },
  ],
};
export const FORMATION_NAMES = Object.keys(FORMATIONS);

/** Formation par défaut. */
export const DEFAULT_FORMATION = "4-3-3";

/** Poste affiché : sigle anglais (GK, CB, ST…) ou français (G, DC, BU…) selon la langue. */
const FR: Record<string, string> = { GK: "G", RB: "DD", CB: "DC", LB: "DG", CM: "MC", RM: "MD", LM: "MG", DM: "MDC", AM: "MOC", RW: "AD", LW: "AG", SS: "AT", ST: "BU" };
export const roleLabel = (role: string, lang: string) => (lang === "fr" ? FR[role] ?? role : role);

/** Ce que montre le rond d'un joueur : ses initiales, son numéro de maillot, un numéro choisi à la main, le poste, ou sa photo (les initiales à défaut). */
export type Display = "initials" | "number" | "free" | "position" | "photo" | "none";
export const DISPLAYS: Display[] = ["initials", "number", "free", "position", "photo", "none"];

/** Marqueur d'un joueur : un rond ou un maillot (couleur, motif et seconde couleur ; le gardien a la sienne), et les tailles (en %) du marqueur, du numéro et du nom. */
export type Marker = "circle" | "jersey";
export type Pattern = "plain" | "halves" | "stripes" | "hoops";
export const PATTERNS: Pattern[] = ["plain", "halves", "stripes", "hoops"];
export interface Style { marker: Marker; color: string; color2: string; pattern: Pattern; gk: string; size: number; label: number; name: number }
export const defaultStyle = (): Style => ({ marker: "circle", color: "#ffffff", color2: "#1d4ed8", pattern: "plain", gk: "#eab308", size: 100, label: 100, name: 100 });
const PAT_CODE: Record<Pattern, string> = { plain: "p", halves: "h", stripes: "s", hoops: "o" };
const hex = (x: string, d: string) => (/^[0-9a-f]{6}$/i.test(x) ? `#${x.toLowerCase()}` : d);
const pct = (x: string) => { const n = parseInt(x, 10); return n >= 50 && n <= 160 ? n : 100; };
/** Dans l'adresse : `st=j.ffffff.1d4ed8.h.eab308.100.100.100` (marqueur c/j, couleur, couleur 2, motif, gardien, tailles marqueur / numéro / nom). */
export const encodeStyle = (t: Style) => [t.marker === "jersey" ? "j" : "c", t.color.slice(1), t.color2.slice(1), PAT_CODE[t.pattern], t.gk.slice(1), t.size, t.label, t.name].join(".");
export function decodeStyle(x: string | null): Style {
  const d = defaultStyle(), a = (x ?? "").split(".");
  if (a.length < 8) return d;
  return { marker: a[0] === "j" ? "jersey" : "circle", color: hex(a[1], d.color), color2: hex(a[2], d.color2), pattern: PATTERNS.find((p) => PAT_CODE[p] === a[3]) ?? "plain", gk: hex(a[4], d.gk), size: pct(a[5]), label: pct(a[6]), name: pct(a[7]) };
}

/** Réglages d'affichage de la composition (interrupteurs). */
export interface Options { formation: boolean; badge: boolean; nat: boolean; gkTop: boolean }
const FLAGS: [keyof Options, string][] = [["formation", "f"], ["badge", "b"], ["nat", "n"], ["gkTop", "g"]];

/** Composition = formation + un joueur (clé de l'effectif) ou null par poste, ce que montrent les ronds, les numéros libres, un titre, un sous-titre et les interrupteurs.
 *  Dans l'adresse : `f=4-3-3&p=Q1,Q2,,…&d=photo&n=1,2,,…&t=Titre&u=Sous-titre&o=fbn` (poste vide = rien ; `o` : lettres des interrupteurs activés). */
export interface Lineup { formation: string; players: (string | null)[]; display: Display; nums: (number | null)[]; title: string; subtitle: string; opts: Options; style: Style }
export const defaultOptions = (): Options => ({ formation: true, badge: true, nat: false, gkTop: false });
export const emptyLineup = (formation = DEFAULT_FORMATION, display: Display = "number"): Lineup =>
  ({ formation, players: FORMATIONS[formation].map(() => null), display, nums: FORMATIONS[formation].map(() => null), title: "", subtitle: "", opts: defaultOptions(), style: defaultStyle() });

export function encodeLineup(l: Lineup): string {
  const qs = new URLSearchParams({ f: l.formation, p: l.players.map((k) => (k ? encodeURIComponent(k) : "")).join(","), d: l.display, o: FLAGS.filter(([k]) => l.opts[k]).map(([, c]) => c).join("") });
  if (l.nums.some((n) => n !== null)) qs.set("n", l.nums.map((n) => n ?? "").join(","));
  if (l.title.trim()) qs.set("t", l.title.trim());
  if (l.subtitle.trim()) qs.set("u", l.subtitle.trim());
  qs.set("st", encodeStyle(l.style));
  return qs.toString();
}
export function decodeLineup(qs: URLSearchParams): Lineup | null {
  const f = qs.get("f");
  if (!f || !FORMATIONS[f]) return null;
  const raw = (qs.get("p") ?? "").split(","), nums = (qs.get("n") ?? "").split(",");
  const d = qs.get("d") as Display, o = qs.get("o");
  return {
    formation: f, display: DISPLAYS.includes(d) ? d : "number", title: (qs.get("t") ?? "").slice(0, 40), subtitle: (qs.get("u") ?? "").slice(0, 60),
    style: decodeStyle(qs.get("st")),
    opts: o === null ? defaultOptions() : Object.fromEntries(FLAGS.map(([k, c]) => [k, o.includes(c)])) as unknown as Options,
    players: FORMATIONS[f].map((_, i) => (raw[i] ? decodeURIComponent(raw[i]) : null)),
    nums: FORMATIONS[f].map((_, i) => { const n = parseInt(nums[i] ?? "", 10); return n >= 0 && n <= 99 ? n : null; }),
  };
}
