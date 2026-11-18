"""Taille et lieu de naissance d'OpenFootball (openfootball/playersdata.py) : liés par nom + date de naissance exacte, jamais par le nom seul."""
import datetime

import duckdb
import pytest

from openfootball.db import migrate
from openfootball.playersdata import link_players, parse_players

TXT = """=================================
=  France

Kylian Mbappé,                F,  1.78 m,  b. 20 Dec 1998 @ Paris
Eli Junior Kroupi,            M,  - ,      b. 23 Jun 2006 @ Lorient
Lilian Baret,                 M,  - ,      b. 25 May 2006
Paul Pogba,                   M,  1.91 m,  b. 15 Mar 1993 @ Lagny-sur-Marne
Paul Pogba,                   M,  1.90 m,  b. 1 Jan 2000 @ Nulle part
"""


def test_lecture_des_lignes():
    rows = parse_players(TXT)
    assert rows[0] == ("Kylian Mbappé", datetime.date(1998, 12, 20), 178, "Paris")
    assert rows[1][2:] == (None, "Lorient") and rows[2][3] is None and len(rows) == 5       # taille « - » : vide ; lieu absent : vide ; titres ignorés


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    migrate(c)
    for pid, name, born in ((1, "Kylian Mbappé", "1998-12-20"), (2, "Paul Pogba", "1993-03-15"), (3, "Eli Junior Kroupi", "2007-01-01"), (4, "Paul Pogba", "1993-03-15")):
        c.execute("INSERT INTO player (id, name) VALUES (?, ?)", [pid, name])
        c.execute("INSERT INTO player_birth VALUES (?, ?, 11)", [pid, born])
    c.execute("INSERT INTO player_profile (player_id, height_cm) VALUES (1, 178)")             # Wikipedia a déjà la taille de Mbappé, pas son lieu
    return c


def test_lien_par_nom_et_naissance_sans_ecraser_wikipedia(con):
    stats = link_players(con, parse_players(TXT))
    # Mbappé : relié, mais Wikipedia a la taille -> seul le lieu est ajouté ; Kroupi : autre date de naissance chez nous -> pas relié ;
    # Pogba : deux joueurs de notre côté pour le même couple -> ambigu, aucun lien ; le Pogba de 2000 n'existe pas chez nous
    assert (stats["linked"], stats["ambiguous"], stats["stored"]) == (1, 1, 1)
    assert con.execute("SELECT player_id, height_cm, birth_place FROM player_openfootball").fetchall() == [(1, None, "Paris")]
