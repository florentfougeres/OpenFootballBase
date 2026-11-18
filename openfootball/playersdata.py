"""Taille et lieu de naissance des joueurs, d'après le dépôt `players` d'OpenFootball (domaine public) : une ligne par joueur et par sélection,
`Kylian Mbappé,   F,  1.78 m,  b. 20 Dec 1998 @ Paris`.

Le nom seul ne désigne pas un joueur (1 315 homonymes de nos joueurs ont une autre date de naissance dans ce fichier) : on ne relie QUE sur le **couple nom + date de naissance
exacte**, et seulement si ce couple désigne un seul joueur de chaque côté. On ne touche pas à Wikipedia : la table `player_openfootball` ne reçoit une valeur que là où le profil
Wikipedia n'en a pas (la taille diffère de plus de 2 cm de la nôtre pour 15 % des joueurs communs : on ne sait pas laquelle est juste, on n'écrase donc rien).
"""
from __future__ import annotations

import collections
import datetime
import re
from typing import Callable

import duckdb

from openfootball.matches import RAW, OpenFootballClient, _tree
from openfootball.names import fold

_MONTHS = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
_ROW = re.compile(r"^(?P<name>[^,]+?),\s*(?P<pos>[A-Z]{1,2}),\s*(?P<h>[\d.]+ m|-)\s*,\s*b\. (?P<d>\d{1,2}) (?P<m>[A-Z][a-z]{2}) (?P<y>\d{4})(?: @ (?P<pl>.*))?$")


def parse_players(text: str) -> list[tuple[str, datetime.date, int | None, str | None]]:
    """(nom, date de naissance, taille en cm ou None, lieu ou None) de chaque ligne reconnue ; les autres (titres, lignes vides, naissances partielles) sont ignorées."""
    out = []
    for line in text.splitlines():
        m = _ROW.match(line.rstrip())
        if not m:
            continue
        try:
            born = datetime.date(int(m["y"]), _MONTHS[m["m"]], int(m["d"]))
        except (ValueError, KeyError):
            continue
        height = None if m["h"] == "-" else round(float(m["h"].split()[0]) * 100)
        out.append((m["name"].strip(), born, height, (m["pl"] or "").strip() or None))
    return out


def link_players(con: duckdb.DuckDBPyConnection, rows: list[tuple[str, datetime.date, int | None, str | None]]) -> dict[str, int]:
    """Remplace `player_openfootball` : pour chaque couple (nom, naissance) unique des deux côtés, la taille et le lieu que Wikipedia n'a pas."""
    ours: dict[tuple[str, datetime.date], list[tuple]] = collections.defaultdict(list)
    for pid, name, born, height, place in con.execute("""SELECT p.id, p.name, b.birth_date, pp.height_cm, pp.birth_place FROM player p
            JOIN player_birth b ON b.player_id = p.id AND b.precision >= 11 LEFT JOIN player_profile pp ON pp.player_id = p.id""").fetchall():
        ours[(fold(name), born)].append((pid, height, place))
    seen = collections.Counter((fold(n), b) for n, b, _, _ in rows)
    stats = {"rows": len(rows), "linked": 0, "ambiguous": 0, "stored": 0}
    todo: list[tuple[int, int | None, str | None]] = []
    for name, born, height, place in rows:
        key = (fold(name), born)
        cands = ours.get(key)
        if not cands:
            continue
        if len(cands) > 1 or seen[key] > 1:                     # deux joueurs (ou deux lignes) pour un même couple : aucun lien
            stats["ambiguous"] += 1
            continue
        stats["linked"] += 1
        pid, our_height, our_place = cands[0]
        new_h = height if height and our_height is None else None
        new_p = place if place and not our_place else None
        if new_h or new_p:
            todo.append((pid, new_h, new_p))
    con.execute("BEGIN")
    try:
        con.execute("DELETE FROM player_openfootball")
        if todo:
            con.executemany("INSERT INTO player_openfootball VALUES (?, ?, ?) ON CONFLICT DO NOTHING", todo)
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    stats["stored"] = len(todo)
    return stats


def import_players(con: duckdb.DuckDBPyConnection, client: OpenFootballClient, *, log_fn: Callable[[str], None] = print) -> dict[str, int]:
    rows: list = []
    for path in _tree(client, "players"):
        if path.endswith(".players.txt") and not path.startswith("attic/"):
            if text := client.get(f"{RAW}/players/master/{path}"):
                rows += parse_players(text)
    stats = link_players(con, rows)
    log_fn(f"  joueurs OpenFootball : {stats['rows']} lignes, {stats['linked']} reliées (nom + naissance), {stats['ambiguous']} ambiguës, "
           f"{stats['stored']} complètent Wikipedia (taille ou lieu)")
    return stats
