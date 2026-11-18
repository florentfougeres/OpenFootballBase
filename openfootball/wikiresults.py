"""Résultats de la saison en cours lus sur Wikipedia, pour compléter la source de matchs OpenFootball.

OpenFootball sert l'historique ; sa mise à jour automatique peut s'arrêter en cours de saison (septembre 2026 : la Premier League y est restée à la
journée 5). Les pages Wikipedia de saison, tenues à jour par les contributeurs, contiennent la matrice des résultats : `match_<DOM>_<EXT> = 2–1` dans le
modèle « Sports table », avec la définition des équipes `name_<DOM> = [[Titre de la page|nom]]`. On en tire les scores et on **complète** :

  - match connu d'OpenFootball sans score  -> le score de Wikipedia (provenance `wikipedia`) ;
  - match absent d'OpenFootball             -> le match est créé (sans date ni journée : la matrice n'en donne pas) ;
  - score déjà là et identique              -> rien ; score différent -> OpenFootball est gardé et le désaccord est rapporté.

Le club d'une équipe est reconnu par le titre de sa page Wikipedia (le même que `club.wikipedia_title`), le nom affiché servant de secours.
Trois formats de matrice : le modèle « Sports table » anglais (`match_`/`name_`), son équivalent espagnol « football results » (`partido_`/`nombre_`, Liga) et le
tableau croisé français « Foot résultat » (Ligue 1). Les autres championnats n'ont pas de matrice : seuls ceux de `LEAGUES` sont lus.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Callable

import duckdb

from openfootball.matches import _club_index, current_start_year, resolve_club, season_label

# code de compétition -> (langue, titre de page) à lire ; {y} = année de début, {yy} = deux derniers chiffres de l'année de fin, {Y} = année de fin sur 4 chiffres.
# Plusieurs pages : leurs matrices s'ajoutent (Bundesliga : la matrice est dans le modèle « table » de la page, pas dans la page).
LEAGUES: dict[str, list[tuple[str, str]]] = {
    "ENG-PL": [("en", "{y}–{yy} Premier League")],
    "ITA-SA": [("en", "{y}–{yy} Serie A")],
    "DEU-BL": [("en", "{y}–{yy} Bundesliga"), ("en", "Template:{y}–{yy} Bundesliga table")],
    "BEL-PL": [("en", "{y}–{yy} Belgian Pro League")],
    "NLD-ED": [("en", "{y}–{yy} Eredivisie")],
    "TUR-SL": [("en", "{y}–{yy} Süper Lig")],
    "PRT-PL": [("en", "{y}–{yy} Primeira Liga")],
    "ESP-LL": [("es", "Primera División de España {y}-{yy}")],
    "FRA-L1": [("fr", "Championnat de France de football {y}-{Y}")],
}

_NAME = re.compile(r"\|\s*(?:name|nombre)_([A-Za-z0-9]+)\s*=\s*([^\n]*)")
_LINK = re.compile(r"\[\[([^\]|#]+)(?:\|([^\]]*))?\]\]")
_MATCH = re.compile(r"\|\s*(?:match|partido)_([A-Za-z0-9]+)_([A-Za-z0-9]+)\s*=\s*((?:\[\[[^\]]*\]\]|[^\n|])*)")      # le score peut être un lien : [[Derbi madrileño|2-1]]
_FR_HEAD = re.compile(r"\{\{Foot résultat début\|(.*?)\}\}", re.S)
_SCORE = re.compile(r"(\d+)\s*[–-]\s*(\d+)")


@dataclass
class WikiMatch:
    home: str                           # code d'équipe de la matrice (ARS)
    away: str
    ft: tuple[int, int]


def parse_foot_resultat(wikitext: str) -> tuple[dict[str, tuple[str, str]], list[WikiMatch]]:
    """Tableau croisé français : `{{Foot résultat début|[[T|SIGLE]]|…}}` donne les équipes dans l'ordre des colonnes, puis une ligne `{{Foot résultat|[[T|Nom]]|case|…}}`
    par équipe à domicile (même ordre) ; une case est un score (`0-2`), `J23` (match à venir, journée 23) ou `XXX` (l'équipe contre elle-même)."""
    head = _FR_HEAD.search(wikitext)
    if not head:
        return {}, []
    links = list(_LINK.finditer(head.group(1)))
    names = {f"T{i}": (m.group(1).strip(), (m.group(2) or m.group(1)).strip()) for i, m in enumerate(links)}
    matches: list[WikiMatch] = []
    for i, row in enumerate(re.findall(r"\{\{Foot résultat\|(.*?)\}\}", wikitext[head.end():], re.S)[:len(links)]):
        first = _LINK.match(row)                                         # le nom de l'équipe est un lien, qui contient lui-même un « | »
        cells = row[first.end():].split("|")[1:] if first else row.split("|")[1:]
        for j, cell in enumerate(cells[:len(links)]):
            if i != j and (sc := _SCORE.fullmatch(cell.strip())):
                matches.append(WikiMatch(f"T{i}", f"T{j}", (int(sc.group(1)), int(sc.group(2)))))
    return names, matches


def parse_matrix(wikitext: str) -> tuple[dict[str, tuple[str, str]], list[WikiMatch]]:
    """Wikitexte d'une page de saison -> ({code: (titre de page du club, nom affiché)}, matchs joués). Matrice « Sports table » (en) ou « football results » (es) ; à défaut,
    tableau croisé français."""
    names: dict[str, tuple[str, str]] = {}
    for code, value in _NAME.findall(wikitext):
        if code not in names and (m := _LINK.search(value)):
            names[code] = (m.group(1).strip(), (m.group(2) or m.group(1)).strip())
    matches: dict[tuple[str, str], WikiMatch] = {}
    for home, away, value in _MATCH.findall(wikitext):
        if s := _SCORE.search(value):
            matches[(home, away)] = WikiMatch(home, away, (int(s.group(1)), int(s.group(2))))
    if not matches:
        return parse_foot_resultat(wikitext)
    return names, list(matches.values())


SUSPECT_MARGIN = 8       # une matrice de Wikipedia est éditée à la main : un écart de 8 buts ou plus (0-10), que personne ne confirme, n'est pas repris (7-0 ou 4-4 le sont)


@dataclass
class Report:
    skipped: list[str] = field(default_factory=list)       # scores refusés : match à venir, ou invraisemblable sans confirmation
    updated: int = 0
    inserted: int = 0
    same: int = 0
    conflicts: list[str] = field(default_factory=list)
    unresolved: set[str] = field(default_factory=set)      # équipes sans club chez nous


def apply_results(con: duckdb.DuckDBPyConnection, code: str, label: str, names: dict[str, tuple[str, str]],
                  matches: list[WikiMatch], ref: str, lang: str = "en", today: date | None = None) -> Report:
    """Complète `match` (voir l'en-tête du module). Les équipes sans club reconnu sont rapportées, leurs matchs ignorés."""
    report = Report()
    index = _club_index(con, code, label)
    titles = sorted({t for t, _ in names.values()})
    by_title = dict(con.execute("SELECT wikipedia_title, id FROM club WHERE wikipedia_title IN (SELECT unnest(?))", [titles]).fetchall())
    if lang != "en":                       # page d'une autre langue : le titre du club dans cette langue (`entity_wiki`, relié par le QID Wikidata)
        by_title.update(con.execute("SELECT w.title, c.id FROM entity_wiki w JOIN club c ON c.wikidata_qid = w.qid WHERE w.lang = ? AND w.title IN (SELECT unnest(?))",
                                    [lang, titles]).fetchall())
    club_of: dict[str, int | None] = {}
    for team, (title, shown) in names.items():
        club_of[team] = by_title.get(title) or resolve_club(index, shown) or resolve_club(index, title)
        if club_of[team] is None:
            report.unresolved.add(shown)
    next_id = con.execute("SELECT coalesce(max(id), 0) + 1 FROM match").fetchone()[0]
    today = today or date.today()
    for m in matches:
        hid, aid = club_of.get(m.home), club_of.get(m.away)
        if hid is None or aid is None:
            continue
        label_m = f"{code} {label} {names[m.home][1]} – {names[m.away][1]}"
        if abs(m.ft[0] - m.ft[1]) >= SUSPECT_MARGIN:                                     # invraisemblable : écarté, même si OpenFootball n'a rien (s'il a le même score, il le portera lui-même)
            report.skipped.append(f"{label_m} : score {m.ft[0]}-{m.ft[1]} invraisemblable (écart d'au moins {SUSPECT_MARGIN} buts), non repris")
            continue
        row = con.execute("SELECT id, ft_home, ft_away, match_date FROM match WHERE competition_code = ? AND season_label = ? AND home_club_id = ? AND away_club_id = ?",
                          [code, label, hid, aid]).fetchone()
        if row is None:
            con.execute("""INSERT INTO match (id, competition_code, season_label, home_name, away_name, home_club_id, away_club_id, ft_home, ft_away, source_ref)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        [next_id, code, label, names[m.home][1], names[m.away][1], hid, aid, m.ft[0], m.ft[1], ref])
            con.execute("INSERT INTO match_result_source VALUES (?, 'wikipedia')", [next_id])
            next_id += 1
            report.inserted += 1
        elif row[1] is None and row[3] is not None and row[3] > today:      # le calendrier d'OpenFootball dit que le match n'a pas eu lieu
            report.skipped.append(f"{label_m} : score {m.ft[0]}-{m.ft[1]} pour un match prévu le {row[3]}, non repris")
        elif row[1] is None:
            con.execute("UPDATE match SET ft_home = ?, ft_away = ? WHERE id = ?", [m.ft[0], m.ft[1], row[0]])
            con.execute("INSERT INTO match_result_source VALUES (?, 'wikipedia') ON CONFLICT DO NOTHING", [row[0]])
            report.updated += 1
        elif (row[1], row[2]) == m.ft:
            report.same += 1
        else:
            report.conflicts.append(f"{code} {label} {names[m.home][1]} – {names[m.away][1]} : OpenFootball {row[1]}-{row[2]}, Wikipedia {m.ft[0]}-{m.ft[1]}")
    return report


def import_wikipedia_results(con: duckdb.DuckDBPyConnection, wps: dict, *, leagues: dict[str, list[tuple[str, str]]] | None = None,
                             log_fn: Callable[[str], None] = print) -> dict[str, Report]:
    """Saison en cours des championnats de `LEAGUES`. `wps` : {langue: WikipediaClient} relisant les pages à chaque passage. À lancer APRÈS les imports
    OpenFootball (ils recréent les matchs). Une page absente (saison pas encore créée) ou sans matrice est signalée, jamais fatale."""
    year = current_start_year()
    label = season_label(year)
    out: dict[str, Report] = {}
    for code, pages in (leagues or LEAGUES).items():
        names: dict[str, tuple[str, str]] = {}
        matches: dict[tuple[str, str], WikiMatch] = {}
        titles = [(lang, p.format(y=year, yy=str(year + 1)[2:], Y=year + 1)) for lang, p in pages]
        for lang, title in titles:
            if lang not in wps:
                continue
            (page,) = wps[lang].get_pages([title])
            if not page.exists or not page.wikitext:
                continue
            n, ms = parse_matrix(page.wikitext)
            for k, v in n.items():
                names.setdefault(k, v)
            matches.update({(m.home, m.away): m for m in ms})
        if not matches:
            log_fn(f"  {code} {label} : aucune matrice de résultats lue ({', '.join(t for _, t in titles)})")
            continue
        lang0, title0 = titles[0]
        rep = apply_results(con, code, label, names, list(matches.values()), f"wikipedia:{lang0}:{title0}", lang0)
        out[code] = rep
        extra = f", {len(rep.conflicts)} désaccords" if rep.conflicts else ""
        miss = f", équipes sans club : {', '.join(sorted(rep.unresolved))}" if rep.unresolved else ""
        log_fn(f"  {code} {label} : Wikipedia {len(matches)} scores -> {rep.updated} complétés, {rep.inserted} créés, {rep.same} identiques{extra}{miss}")
        for c in rep.conflicts[:10]:
            log_fn(f"    désaccord : {c}")
        for c in rep.skipped[:10]:
            log_fn(f"    refusé : {c}")
    return out
