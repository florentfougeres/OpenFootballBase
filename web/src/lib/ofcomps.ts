// Compétitions « OF:* » de la table `match` : celles de la source de matchs (OpenFootball) que nous n'avons pas comme championnat.
// Les équipes nationales sont rangées ici (phases finales, qualifications, amicaux) ; tout le reste (championnats du dépôt `world`, Sudamericana…) est « autre ».
import type { IconName } from "../components/Icon.svelte";

export type NationalGroup = "finals" | "qualifying" | "friendly";
type Nat = { fr: string; en: string; icon: IconName; group: NationalGroup };

export const NATIONAL: Record<string, Nat> = {
  "OF:worldcup": { fr: "Coupe du monde", en: "World Cup", icon: "trophy", group: "finals" },
  "OF:euro": { fr: "Championnat d'Europe", en: "European Championship", icon: "trophy", group: "finals" },
  "OF:copa_america": { fr: "Copa América", en: "Copa América", icon: "trophy", group: "finals" },
  "OF:african_cup_of_nations": { fr: "Coupe d'Afrique des nations", en: "Africa Cup of Nations", icon: "trophy", group: "finals" },
  "OF:afc_asian_cup": { fr: "Coupe d'Asie des nations", en: "AFC Asian Cup", icon: "trophy", group: "finals" },
  "OF:gold_cup": { fr: "Gold Cup (CONCACAF)", en: "CONCACAF Gold Cup", icon: "trophy", group: "finals" },
  "OF:oceania_nations_cup": { fr: "Coupe d'Océanie des nations", en: "OFC Nations Cup", icon: "trophy", group: "finals" },
  "OF:uefa_nations_league": { fr: "Ligue des nations UEFA", en: "UEFA Nations League", icon: "trophy", group: "finals" },
  "OF:concacaf_nations_league": { fr: "Ligue des nations CONCACAF", en: "CONCACAF Nations League", icon: "trophy", group: "finals" },
  "OF:fifa_world_cup_qualification": { fr: "Qualifications Coupe du monde", en: "World Cup qualification", icon: "target", group: "qualifying" },
  "OF:uefa_euro_qualification": { fr: "Qualifications Championnat d'Europe", en: "European Championship qualification", icon: "target", group: "qualifying" },
  "OF:copa_america_qualification": { fr: "Qualifications Copa América", en: "Copa América qualification", icon: "target", group: "qualifying" },
  "OF:african_cup_of_nations_qualification": { fr: "Qualifications Coupe d'Afrique des nations", en: "Africa Cup of Nations qualification", icon: "target", group: "qualifying" },
  "OF:afc_asian_cup_qualification": { fr: "Qualifications Coupe d'Asie des nations", en: "AFC Asian Cup qualification", icon: "target", group: "qualifying" },
  "OF:gold_cup_qualification": { fr: "Qualifications Gold Cup", en: "Gold Cup qualification", icon: "target", group: "qualifying" },
  "OF:oceania_nations_cup_qualification": { fr: "Qualifications Coupe d'Océanie", en: "OFC Nations Cup qualification", icon: "target", group: "qualifying" },
  "OF:concacaf_nations_league_qualification": { fr: "Qualifications Ligue des nations CONCACAF", en: "CONCACAF Nations League qualification", icon: "target", group: "qualifying" },
  "OF:friendly": { fr: "Matchs amicaux", en: "Friendlies", icon: "ball", group: "friendly" },
};

export const NATIONAL_ORDER = Object.keys(NATIONAL);
export const isNational = (code: string) => code in NATIONAL;

// Où ranger les autres compétitions « OF:* » : leur confédération, leur pays (nom anglais, pour le drapeau et le nom localisé) et leur niveau (0 = compétition continentale).
// Une compétition absente d'ici tombe dans « Autres championnats et coupes » : à compléter quand la source en ajoute une.
export type Conf = "UEFA" | "CONMEBOL" | "CONCACAF" | "AFC" | "CAF" | "OFC";
export const PLACE: Record<string, { conf: Conf; country?: string; level: number }> = {
  "OF:at.2": { conf: "UEFA", country: "Austria", level: 2 },
  "OF:en.3": { conf: "UEFA", country: "England", level: 3 },
  "OF:en.4": { conf: "UEFA", country: "England", level: 4 },
  "OF:il2": { conf: "UEFA", country: "Israel", level: 2 },
  "OF:ilcup": { conf: "UEFA", country: "Israel", level: 5 },
  "OF:copa-sudamericana": { conf: "CONMEBOL", level: 0 },
  "OF:concacafcl": { conf: "CONCACAF", level: 0 },
  "OF:cr1": { conf: "CONCACAF", country: "Costa Rica", level: 1 },
  "OF:mx2ascenso": { conf: "CONCACAF", country: "Mexico", level: 2 },
  "OF:mx2expansion": { conf: "CONCACAF", country: "Mexico", level: 2 },
  "OF:afl": { conf: "CAF", level: 0 },
  "OF:ke1": { conf: "CAF", country: "Kenya", level: 1 },
  "OF:mw1": { conf: "CAF", country: "Malawi", level: 1 },
  "OF:ng2": { conf: "CAF", country: "Nigeria", level: 2 },
  "OF:rw1": { conf: "CAF", country: "Rwanda", level: 1 },
};
/** « Kenya | Premier League » -> « Premier League » : le pays est dit à part, sur la carte. */
export const bareName = (name: string) => name.replace(/^[^|]+\|\s*/, "");
