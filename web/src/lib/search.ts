// Recherche groupée de la palette : joueurs (DuckDB), clubs, compétitions et pays (listes déjà en mémoire).
import { app, countryOf, enc, href, type Row } from "./app.svelte";
import { q } from "./db";
import { fold } from "./fold";
import { clubName, compName } from "./format";

export type Hit = {
  id: string;
  kind: "player" | "club" | "comp" | "country";
  label: string;
  sub: string;              // ligne grise sous le nom
  meta: string;             // à droite
  to: string;               // adresse (#/fr/…)
  flag?: string | null;     // drapeau (joueur, pays, compétition)
  club?: Row;               // club : pour son logo
  logoUrl?: string | null;  // compétition : logo
};
export type Groups = { players: Hit[]; clubs: Hit[]; comps: Hit[]; countries: Hit[] };
export const emptyGroups = (): Groups => ({ players: [], clubs: [], comps: [], countries: [] });

/** Rang d'une correspondance : 0 le nom commence par la saisie, 1 un mot du nom commence par elle, 2 elle est au milieu, 9 absente. */
const rank = (name: string, needle: string) => {
  const n = fold(name);
  return n.startsWith(needle) ? 0 : n.includes(" " + needle) ? 1 : n.includes(needle) ? 2 : 9;
};

export async function search(term: string): Promise<Groups> {
  const needle = fold(term);
  const out = emptyGroups();
  if (needle.length < 2) return out;

  // Clubs avec effectifs : déjà en mémoire (pas d'attente DuckDB).
  out.clubs = [...app.clubs.values()]
    .map((c) => ({ c, r: Math.min(...[c.name_en, c.name_fr, c.wikipedia_title].filter(Boolean).map((n) => rank(String(n), needle))) }))
    .filter((x) => x.r < 9)
    .sort((a, b) => a.r - b.r || (b.c.wikipedia_count ?? 0) - (a.c.wikipedia_count ?? 0))
    .slice(0, 5)
    .map(({ c }) => ({
      id: `c:${c.wikipedia_title}`, kind: "club" as const, label: clubName(c), club: c,
      sub: [countryOf(c.country_code).name, c.league].filter(Boolean).join(" · "), meta: "",
      to: href("club", enc(c.wikipedia_title)),
    }));

  out.comps = [...app.comps.values()]
    .filter((c) => [c.name_en, c.name_fr, c.code].some((n) => rank(String(n ?? ""), needle) < 9))
    .sort((a, b) => rank(compName(a.code), needle) - rank(compName(b.code), needle) || (a.level ?? 9) - (b.level ?? 9))
    .slice(0, 4)
    .map((c) => ({ id: `k:${c.code}`, kind: "comp" as const, label: compName(c.code), sub: countryOf(c.country_code).name, meta: "", flag: countryOf(c.country_code).flag,
                   logoUrl: (c.logo_url as string | null) ?? null, to: href("competition", c.code) }));

  out.countries = [...app.countries.values()]
    .filter((c) => [c.name_en, c.name_fr].some((n) => rank(String(n ?? ""), needle) < 9))
    .slice(0, 3)
    .map((c) => ({ id: `n:${c.code}`, kind: "country" as const, label: app.lang === "fr" ? c.name_fr : c.name_en, sub: "", meta: "", flag: countryOf(c.code).flag, to: href("country", c.code) }));

  if (app.ready) {
    const like = `%${term}%`, start = `${term}%`, word = `% ${term}%`;
    const cols = `any_value(player) AS player, COALESCE(player_qid, 'name:' || player) AS key, arg_max(nat_flag, season) AS flag, arg_max(nationality, season) AS nat,
              arg_max(position, season) AS pos, arg_max(club, season) AS club, count(DISTINCT season) AS n, min(season) AS first, max(season) AS last`;
    // « commence par » ET « un mot commence par » au même rang (« ronaldo » doit trouver Cristiano Ronaldo autant que Ronaldo Vieira), puis les plus
    // présents dans la base (nombre de saisons) : les joueurs connus remontent, un homonyme obscur ne les écarte pas.
    let players = await q(
      `SELECT ${cols} FROM squad WHERE strip_accents(player) ILIKE strip_accents(?)
       GROUP BY COALESCE(player_qid, 'name:' || player)
       ORDER BY CASE WHEN strip_accents(any_value(player)) ILIKE strip_accents(?) OR strip_accents(any_value(player)) ILIKE strip_accents(?) THEN 1 ELSE 2 END,
                n DESC, any_value(player) LIMIT 8`,
      [like, start, word]);
    // Faute de frappe (« viera » pour Vieira) : on rapproche aussi la saisie des mots des noms (similarité de Jaro-Winkler) ; les plus présents d'abord.
    // Saisie de plusieurs mots (« patrick vieira ») : les correspondances exactes d'abord, puis la ressemblance du NOM ENTIER (sinon « patrick » ramène Patrice).
    if (needle.length >= 4) {
      const multi = needle.includes(" ");
      const fuzzy = await q(
        multi
          ? `WITH names AS (SELECT COALESCE(player_qid, 'name:' || player) AS key, any_value(player) AS player, count(DISTINCT season) AS n FROM squad GROUP BY 1),
                  fz AS (SELECT key FROM names WHERE jaro_winkler_similarity(lower(strip_accents(player)), ?) >= 0.9 ORDER BY n DESC LIMIT 8)
             SELECT ${cols} FROM squad WHERE COALESCE(player_qid, 'name:' || player) IN (SELECT key FROM fz) GROUP BY COALESCE(player_qid, 'name:' || player) ORDER BY n DESC LIMIT 5`
          : `WITH names AS (SELECT COALESCE(player_qid, 'name:' || player) AS key, any_value(player) AS player, count(DISTINCT season) AS n FROM squad GROUP BY 1),
                  tok AS (SELECT key, n, unnest(string_split(lower(strip_accents(player)), ' ')) AS w FROM names),
                  fz AS (SELECT key FROM (SELECT key, n, max(jaro_winkler_similarity(w, ?)) AS sim FROM tok GROUP BY key, n) WHERE sim >= 0.9 ORDER BY n DESC, sim DESC LIMIT 8)
             SELECT ${cols} FROM squad WHERE COALESCE(player_qid, 'name:' || player) IN (SELECT key FROM fz) GROUP BY COALESCE(player_qid, 'name:' || player) ORDER BY n DESC LIMIT 5`,
        [needle]);
      const seen = new Set(players.map((p) => p.key));
      const extra = fuzzy.filter((p) => !seen.has(p.key));
      players = multi ? [...players, ...extra] : [...players, ...extra].sort((a, b) => Number(b.n) - Number(a.n));
    }
    players = players.slice(0, 5);
    out.players = players.map((p) => ({
      id: `p:${p.key}`, kind: "player" as const, label: p.player, flag: p.flag,
      sub: [p.pos, p.club ? clubName(app.clubs.get(p.club) ?? { wikipedia_title: p.club, name_en: p.club }) : ""].filter(Boolean).join(" · "),
      meta: p.first === p.last ? String(p.first) : `${String(p.first).slice(0, 4)}–${String(p.last).slice(2, 4)}`,
      to: href("player", enc(p.key)),
    }));
    if (needle.length >= 3 && out.clubs.length < 3) {                      // clubs du monde sans effectif : seulement s'il y a peu de clubs à effectifs
      const world = await q(`SELECT wikidata_qid AS qid, name_local, name_en, country_iso, logo_url, colors_hex FROM club WHERE NOT has_squads
        AND (strip_accents(name_local) ILIKE strip_accents(?) OR strip_accents(coalesce(name_en, '')) ILIKE strip_accents(?)) ORDER BY coalesce(wikipedia_count, 0) DESC LIMIT 3`, [like, like]);
      out.clubs.push(...world.map((c) => ({
        id: `w:${c.qid}`, kind: "club" as const, label: String(app.lang === "fr" ? c.name_local : c.name_en || c.name_local), club: c as Row,
        sub: c.country_iso ? countryOf(String(c.country_iso)).name : "", meta: "", to: href("club", String(c.qid)),
      })));
    }
  }
  return out;
}
