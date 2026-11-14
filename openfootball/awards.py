"""Ballon d'Or : le classement de chaque édition, lu dans le tableau de la page Wikipedia « <année> Ballon d'Or » (rien d'autre).

Le tableau varie d'une édition à l'autre (rang | joueur | nationalité | poste | club(s) | points, ou avec le détail des votes) : les colonnes sont
repérées par leur titre. Une cellule illisible reste vide ; un joueur sans page garde son nom sans lien.
"""
from __future__ import annotations

import re
from typing import Callable

import duckdb

from openfootball.parse.squad import _name_and_link, clean
from openfootball.parse.stats import _TABLE, _grid, _headers, _int, _link, _text
from openfootball.sources.wikidata import club_qids

AWARD = "BALLON_DOR"
_RANK = re.compile(r"^\s*(\d{1,2})(?:st|nd|rd|th)?\b", re.I)


def parse_ranking(wikitext: str) -> list[dict]:
    """Lignes (rang, joueur, lien, club, lien du club, points) du premier tableau « Rank | Player… » de la page."""
    for tbl in _TABLE.findall(clean(wikitext)):
        rows = _grid(tbl)
        labels, start = _headers(rows)
        names = [b.lower() for _, b in labels]
        if not start or "player" not in names:
            continue
        ri = next((i for i, n in enumerate(names) if n.startswith("rank") or n in ("#", "pos", "place")), 0)
        pi = names.index("player")
        ci = next((i for i, n in enumerate(names) if n.startswith("club")), None)
        gi = next((i for i, n in enumerate(names) if n in ("points", "total", "pts")), None)
        out = []
        for cells in rows[start:]:
            if len(cells) <= max(ri, pi):
                continue
            m = _RANK.match(cells[ri].text)
            if not m:
                continue
            name, link = _name_and_link(cells[pi].raw, full=True)
            if not name:
                continue
            club = cells[ci] if ci is not None and ci < len(cells) else None
            out.append({"rank": int(m.group(1)), "player": name, "player_link": link,
                        "club": _text(club.raw.split("<br")[0]) if club else None, "club_link": _link(club.raw) if club else None,
                        "points": _int(cells[gi].raw) if gi is not None and gi < len(cells) else None})
        if out:
            return out
    return []


def import_ballon_dor(con: duckdb.DuckDBPyConnection, wp, *, since: int = 2000, until: int = 2025, log: Callable[[str], None] = print) -> int:
    """Classement de chaque édition de `since` à `until` (l'édition 2020 n'a pas eu lieu : pas de tableau, rien d'écrit)."""
    titles = {y: f"{y} Ballon d'Or" for y in range(since, until + 1)}
    rows: list[tuple] = []
    for y, page in zip(titles, wp.get_pages(list(titles.values()))):
        got = parse_ranking(page.wikitext) if page.exists and page.wikitext else []
        if not got:
            log(f"  {y} : pas de classement lu")
            continue
        for r in got:
            rows.append((y, r, page.resolved_title or page.title))
    links = sorted({r["player_link"] for _, r, _ in rows if r["player_link"]} | {r["club_link"] for _, r, _ in rows if r["club_link"]})
    qids = club_qids(wp, links) if links else {}
    con.execute("BEGIN")
    try:
        con.execute("DELETE FROM award_ranking WHERE award = ? AND year BETWEEN ? AND ?", [AWARD, since, until])
        for y, r, src in rows:
            pq = qids.get(r["player_link"]) if r["player_link"] else None
            cq = qids.get(r["club_link"]) if r["club_link"] else None
            club = con.execute("SELECT id FROM club WHERE wikidata_qid = ? OR wikipedia_title = ?", [cq, r["club_link"]]).fetchone() if (cq or r["club_link"]) else None
            con.execute("INSERT INTO award_ranking VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                        [AWARD, y, r["rank"], r["player"], r["player_link"], pq, r["club"], r["club_link"], club[0] if club else None, r["points"], src])
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    log(f"  Ballon d'Or : {len(rows)} lignes, {len({y for y, _, _ in rows})} éditions")
    return len(rows)
