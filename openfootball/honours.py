"""Palmarès : le vainqueur de chaque saison d'une compétition, d'après Wikidata (rien d'autre).

Une compétition est retrouvée par son QID (celui de sa page Wikipedia anglaise) ; ses saisons sont les éléments reliés par P3450 (« saison de
championnat ou de compétition ») et leur vainqueur est P1346. L'année vient du libellé de la saison (« 2003–04 Ligue 1 », « 2019 Brasileirão ») :
P580 est souvent absent. Un co-vainqueur donne deux lignes. Rien n'est deviné : une saison sans vainqueur sur Wikidata n'a pas de ligne.
"""
from __future__ import annotations

import re
from typing import Callable

import duckdb

from openfootball.enrich import LEAGUE_PAGES
from openfootball.sources.wikidata import club_qids

_YEAR = re.compile(r"\b((?:18|19|20)\d{2})\b")
_CHUNK = 25


def season_start(label: str) -> int | None:
    """« 2003–04 Ligue 1 » -> 2003 ; « 2019 Campeonato Brasileiro » -> 2019 ; sans année plausible : None."""
    m = _YEAR.search(label or "")
    return int(m.group(1)) if m else None


def resolve_competition_qids(con: duckdb.DuckDBPyConnection, wp, *, log: Callable[[str], None] = print) -> int:
    """QID Wikidata de chaque compétition sans QID, par le titre de sa page Wikipedia anglaise. Un QID déjà pris par une autre compétition est ignoré."""
    rows = con.execute("""SELECT c.id, coalesce(i.wikipedia_title, c.name_en) FROM competition c LEFT JOIN competition_info i ON i.code = c.code
                          WHERE c.id NOT IN (SELECT competition_id FROM competition_wikidata) ORDER BY c.id""").fetchall()
    titles = [LEAGUE_PAGES.get(t, t) for _, t in rows]
    found = club_qids(wp, titles)
    taken = {r[0] for r in con.execute("SELECT qid FROM competition_wikidata").fetchall()}
    n = 0
    for (cid, _), title in zip(rows, titles):
        qid = found.get(title)
        if qid and qid not in taken:
            con.execute("INSERT INTO competition_wikidata VALUES (?, ?)", [cid, qid])
            taken.add(qid)
            n += 1
    log(f"  compétitions : {n} QID trouvés sur {len(rows)}")
    return n


def _club_for(con, qid: str, name: str, country: str | None) -> int | None:
    """Club de la base pour un vainqueur. Wikidata a souvent DEUX éléments pour un même club (le club et sa « section football », Bayern :
    Q15789 et Q97905919) : on cherche par QID OU par nom exact (nom anglais, local, page), et on préfère l'enregistrement qui a des saisons
    (le vrai club de la base) puis celui du même pays."""
    row = con.execute("""SELECT c.id FROM club c
                         WHERE c.wikidata_qid = ? OR ((c.name_en = ? OR c.name_local = ? OR c.wikipedia_title = ?) AND (? IS NULL OR c.country_code = ?))
                         ORDER BY EXISTS (SELECT 1 FROM club_season cs WHERE cs.club_id = c.id) DESC,
                                  (SELECT count(*) FROM club_season cs WHERE cs.club_id = c.id) DESC, (c.wikidata_qid = ?) DESC, c.id LIMIT 1""",
                      [qid, name, name, name, country, country, qid]).fetchone()
    return row[0] if row else None


def import_winners(con: duckdb.DuckDBPyConnection, wd, *, log: Callable[[str], None] = print) -> int:
    """Remplace le palmarès par celui de Wikidata. Rend le nombre de lignes (compétition, saison, vainqueur) écrites."""
    comps = con.execute("""SELECT c.id, w.qid, c.country_code FROM competition c JOIN competition_wikidata w ON w.competition_id = c.id ORDER BY c.id""").fetchall()
    by_qid = {q: (cid, cc) for cid, q, cc in comps}
    rows: dict[tuple[int, int, str], tuple[str, str]] = {}
    for i in range(0, len(comps), _CHUNK):
        qs = [q for _, q, _ in comps[i:i + _CHUNK]]
        sparql = ("SELECT ?comp ?season ?seasonLabel ?winner ?winnerLabel WHERE { VALUES ?comp { " + " ".join(f"wd:{q}" for q in qs) + " } "
                  "?season wdt:P3450 ?comp ; wdt:P1346 ?winner . "
                  'SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }')
        for b in wd.query(sparql):
            cid, _cc = by_qid[b["comp"].rsplit("/", 1)[-1]]
            year = season_start(b.get("seasonLabel", ""))
            wq = b["winner"].rsplit("/", 1)[-1]
            if year:
                rows[(cid, year, wq)] = (b.get("winnerLabel") or wq, b["season"].rsplit("/", 1)[-1])
    # Contrôle : quand la base connaît les participants d'une compétition cette saison-là, le vainqueur en est un. Wikidata se trompe parfois
    # (la MLS 2011 et 2012 « gagnées » par le Real Madrid) : une telle ligne est écartée plutôt que publiée.
    parts: dict[tuple[int, int], set[int]] = {}
    for cid, year, club in con.execute("""SELECT DISTINCT x.competition_id, s.start_year, x.club_id FROM (
            SELECT competition_id, season_id, club_id FROM club_season UNION SELECT competition_id, season_id, club_id FROM competition_entry) x
        JOIN season s ON s.id = x.season_id""").fetchall():
        parts.setdefault((cid, year), set()).add(club)
    skipped: list[str] = []
    con.execute("BEGIN")
    try:
        con.execute("DELETE FROM competition_winner")
        for (cid, year, wq), (name, sq) in sorted(rows.items()):
            country = next(cc for c, _q, cc in comps if c == cid)
            club = _club_for(con, wq, name, country)
            if club is not None and (cid, year) in parts and club not in parts[(cid, year)]:
                skipped.append(f"{name} {year}")
                continue
            con.execute("INSERT INTO competition_winner VALUES (?, ?, ?, ?, ?, ?)", [cid, year, wq, name, club, sq])
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    if skipped:
        log(f"  {len(skipped)} vainqueurs écartés (pas parmi les participants de la saison) : {', '.join(skipped[:8])}{'…' if len(skipped) > 8 else ''}")
    seasons = len({(c, y) for c, y, _ in rows})
    log(f"  palmarès : {len(rows)} vainqueurs, {seasons} saisons, {len({c for c, _, _ in rows})} compétitions")
    return len(rows)


# --- Compléter avec les pages Wikipedia des saisons -------------------------------------------------------------------------------
_PARAM = re.compile(r"^\s*\|\s*(?:champions?(?:_other)?|winners?)\s*=\s*(.+)$", re.I | re.M)
_LINK = re.compile(r"\[\[(?!File:|Image:)([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")


def infobox_winner(wikitext: str) -> tuple[str, str] | None:
    """(titre de la page du vainqueur, libellé) d'après le paramètre `winners` / `champions` de l'infobox d'une page de saison ; None si absent."""
    head = wikitext[:6000]
    for m in _PARAM.finditer(head):
        link = _LINK.search(m.group(1))
        if link:
            title = link.group(1).strip()
            return title, (link.group(2) or title).strip()
    return None


# Compétitions « premier niveau d'un pays » créées avec un nom générique (« Finland top division ») : le vrai nom du championnat, avec ses anciens noms.
_LEAGUE_NAMES: dict[str, tuple[str, ...]] = {
    "AND-L1": ("Primera Divisió",), "ARM-L1": ("Armenian Premier League",), "BIH-L1": ("Premier League of Bosnia and Herzegovina",),
    "EST-L1": ("Meistriliiga",), "FIN-L1": ("Veikkausliiga",), "GEO-L1": ("Erovnuli Liga", "Georgian Premier League"),
    "GIB-L1": ("Gibraltar Football League",), "HKG-L1": ("Hong Kong Premier League",), "IND-L1": ("Indian Super League",),
    "IRL-L1": ("League of Ireland Premier Division",), "IRN-L1": ("Persian Gulf Pro League",), "ISL-L1": ("Besta deild karla", "Úrvalsdeild"),
    "LTU-L1": ("A Lyga",), "LUX-L1": ("Luxembourg National Division",), "LVA-L1": ("Latvian Higher League",),
    "MKD-L1": ("Macedonian First Football League",), "MLT-L1": ("Maltese Premier League",), "NIR-L1": ("NIFL Premiership", "IFA Premiership"),
    "PHL-L1": ("Philippines Football League",), "SGP-L1": ("Singapore Premier League",), "THA-L1": ("Thai League 1",),
    "UZB-L1": ("Uzbekistan Super League",), "VEN-L1": ("Venezuelan Primera División",), "WAL-L1": ("Cymru Premier", "Welsh Premier League"),
    "XKS-L1": ("Football Superleague of Kosovo",), "NGA-L1": ("Nigeria Professional Football League",), "MYS-L1": ("Malaysia Super League",),
    "SCO-L1": ("Scottish Premier League", "Scottish Premiership"),
}


def _season_titles(name: str, year: int, extra: tuple[str, ...]) -> list[str]:
    """Titres essayés pour la page d'une saison : « 2024–25 Ligue 1 », « 2019 Brasileirão » ; noms alternatifs en plus."""
    label = f"{year}–{str(year + 1)[2:]}"
    return [f"{p} {n}" for n in dict.fromkeys((name, *extra)) for p in (label, str(year))]


def fill_winners_from_wikipedia(con: duckdb.DuckDBPyConnection, wp, *, since: int = 2000, log: Callable[[str], None] = print) -> int:
    """Saisons de la base sans vainqueur (Wikidata ne le renseigne pas) : on le lit dans l'infobox de la page Wikipedia de la saison.
    Le vainqueur est relié à un club de la base par son QID (via la page) ; la ligne porte `season_qid = 'enwiki:<page>'`."""
    from openfootball.scopes import load_scopes
    extra = {s.competition_code: s.page_names for s in load_scopes()}
    todo = con.execute("""
        SELECT co.id, co.code, co.name_en, s.start_year FROM (
            SELECT competition_id, season_id FROM club_season UNION SELECT competition_id, season_id FROM competition_entry) x
        JOIN competition co ON co.id = x.competition_id JOIN season s ON s.id = x.season_id
        WHERE s.start_year >= ? AND NOT EXISTS (SELECT 1 FROM competition_winner w WHERE w.competition_id = co.id AND w.season_start = s.start_year)
        GROUP BY ALL ORDER BY co.code, s.start_year""", [since]).fetchall()
    log(f"  {len(todo)} saisons sans vainqueur à chercher sur Wikipedia")
    candidates = {(cid, y): _season_titles(*((_LEAGUE_NAMES[code][0], y, _LEAGUE_NAMES[code][1:] + extra.get(code, ())) if code in _LEAGUE_NAMES
                                              else (LEAGUE_PAGES.get(name, name), y, extra.get(code, ())))) for cid, code, name, y in todo}
    all_titles = list(dict.fromkeys(t for ts in candidates.values() for t in ts))
    pages: dict[str, str] = {}
    for i in range(0, len(all_titles), 50):
        for p in wp.get_pages(all_titles[i:i + 50]):
            if p.exists and p.wikitext:
                pages[p.title] = p.wikitext
                if getattr(p, "resolved_title", None):
                    pages[p.resolved_title] = p.wikitext
    found: dict[tuple[int, int], tuple[str, str, str]] = {}
    for (cid, y), titles in candidates.items():
        for t in titles:
            if t in pages and (w := infobox_winner(pages[t])):
                found[(cid, y)] = (w[0], w[1], t)
                break
    qids = club_qids(wp, sorted({w[0] for w in found.values()})) if found else {}
    n = 0
    con.execute("BEGIN")
    try:
        for (cid, y), (target, label, page) in sorted(found.items()):
            qid = qids.get(target)
            club = con.execute("SELECT id FROM club WHERE wikidata_qid = ? OR wikipedia_title = ?", [qid, target]).fetchone() if (qid or target) else None
            con.execute("INSERT INTO competition_winner VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                        [cid, y, qid or f"enwiki:{target}", label, club[0] if club else None, f"enwiki:{page}"])
            n += 1
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    log(f"  vainqueurs lus sur les pages de saison : {n} / {len(todo)}")
    return n
