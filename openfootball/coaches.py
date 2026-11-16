"""Entraîneurs des clubs : les mandats de la propriété Wikidata « entraîneur » (P286), avec leurs dates de début (P580) et de fin (P582).

Un mandat sans date de début n'est pas gardé (on ne saurait pas le placer dans le temps) ; deux déclarations identiques (même club, même
entraîneur, même début) n'en font qu'un. Les libellés sont ceux de Wikidata, en anglais puis en français.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Callable

import duckdb

BATCH = 80


def _date(raw: str | None) -> date | None:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", raw or "")
    if not m:
        return None                                    # absent, année négative ou format inattendu
    try:
        return date(int(m.group(1)), max(int(m.group(2)), 1), max(int(m.group(3)), 1))
    except ValueError:
        return None


def parse_coaches(rows: list[dict]) -> dict[tuple[str, str, date], tuple[str, date | None]]:
    """Lignes SPARQL (?club ?coach ?coachLabel ?start ?end) -> {(club_qid, coach_qid, début): (nom, fin)}."""
    out: dict[tuple[str, str, date], tuple[str, date | None]] = {}
    for r in rows:
        start = _date(r.get("start"))
        label = r.get("coachLabel", "")
        if start is None or not label or re.fullmatch(r"Q\d+", label):          # sans libellé, le service renvoie le QID lui-même
            continue
        end = _date(r.get("end"))
        if end is not None and end < start:
            end = None                                  # fin antérieure au début : fin ignorée, le mandat reste daté
        key = (r["club"].rsplit("/", 1)[-1], r["coach"].rsplit("/", 1)[-1], start)
        if key in out:
            old = out[key][1]
            end = None if old is None or end is None else max(old, end)             # deux déclarations : on ne ferme le mandat que si les deux le font
        out[key] = (label, end)
    return out


def import_coaches(con: duckdb.DuckDBPyConnection, wd, *, log: Callable[[str], None] = print) -> int:
    """Remplace `club_coach` : les mandats de tous les clubs ayant des effectifs et un QID."""
    clubs = {q: cid for cid, q in con.execute("""SELECT c.id, c.wikidata_qid FROM club c WHERE c.wikidata_qid IS NOT NULL
                                                  AND EXISTS (SELECT 1 FROM club_season cs WHERE cs.club_id = c.id) ORDER BY c.id""").fetchall()}
    qids = list(clubs)
    found: dict[tuple[str, str, date], tuple[str, date | None]] = {}
    for i in range(0, len(qids), BATCH):
        chunk = qids[i:i + BATCH]
        sparql = ("SELECT ?club ?coach ?coachLabel ?start ?end WHERE { VALUES ?club { " + " ".join(f"wd:{q}" for q in chunk) + " } "
                  "?club p:P286 ?st . ?st ps:P286 ?coach . OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end } "
                  'SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". } }')
        found.update(parse_coaches(wd.query(sparql)))
    if not found:
        log("  entraîneurs : aucun mandat reçu, table inchangée")
        return 0
    con.execute("BEGIN")
    try:
        con.execute("DELETE FROM club_coach")
        con.executemany("INSERT INTO club_coach VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                        [(clubs[club], coach, name, start, end) for (club, coach, start), (name, end) in found.items() if club in clubs])
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    n = con.execute("SELECT count(*) FROM club_coach").fetchone()[0]
    log(f"  entraîneurs : {n} mandats, {con.execute('SELECT count(DISTINCT club_id) FROM club_coach').fetchone()[0]} clubs sur {len(clubs)}")
    return n
