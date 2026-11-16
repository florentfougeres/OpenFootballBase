"""Entraîneurs : lecture des mandats Wikidata (début, fin, doublons) et écriture de `club_coach`."""
import duckdb

from openfootball.coaches import import_coaches, parse_coaches
from openfootball.db import migrate

CLUB = "http://www.wikidata.org/entity/Q1893"


def _row(coach="Q923088", label="Stefano Pioli", start="2011-10-04T00:00:00Z", end="2014-01-07T00:00:00Z"):
    r = {"club": CLUB, "coach": f"http://www.wikidata.org/entity/{coach}", "coachLabel": label}
    if start:
        r["start"] = start
    if end:
        r["end"] = end
    return r


def test_mandat_lu_avec_dates():
    got = parse_coaches([_row()])
    ((key, (name, end)),) = got.items()
    assert key[:2] == ("Q1893", "Q923088") and str(key[2]) == "2011-10-04" and name == "Stefano Pioli" and str(end) == "2014-01-07"


def test_sans_debut_ou_sans_libelle_ignore():
    assert parse_coaches([_row(start=None), _row(label="Q923088")]) == {}


def test_fin_avant_debut_ignoree_et_doublon_fusionne():
    got = parse_coaches([_row(end="2010-01-01T00:00:00Z")])
    assert list(got.values())[0][1] is None                                       # fin impossible : mandat gardé, fin vide
    dup = parse_coaches([_row(end="2012-01-01T00:00:00Z"), _row(end="2013-01-01T00:00:00Z")])
    assert len(dup) == 1 and str(list(dup.values())[0][1]) == "2013-01-01"
    ouvert = parse_coaches([_row(end=None), _row(end="2013-01-01T00:00:00Z")])
    assert list(ouvert.values())[0][1] is None                                    # une déclaration sans fin : le mandat reste ouvert


def test_import_remplace_la_table():
    con = duckdb.connect(":memory:")
    migrate(con)
    con.execute("INSERT INTO country VALUES ('ITA', 'Italie', 'Italy')")
    con.execute("INSERT INTO competition (id, code, name_en, name_fr, country_code, level) VALUES (1, 'ITA-SA', 'Serie A', 'Serie A', 'ITA', 1)")
    con.execute("INSERT INTO season (id, start_year, label, status) VALUES (1, 2011, '2011/12', 'backfill')")
    con.execute("INSERT INTO club (id, wikidata_qid, wikipedia_title, name_en) VALUES (1, 'Q1893', 'Bologna F.C. 1909', 'Bologna'), (2, 'Q2', 'Sans effectif', 'X')")
    con.execute("INSERT INTO club_season (id, club_id, season_id, competition_id) VALUES (1, 1, 1, 1)")
    asked = []

    class Wd:
        def query(self, sparql):
            asked.append(sparql)
            return [_row(), _row(coach="Q294351", label="Siniša Mihajlović", start="2019-01-28T00:00:00Z", end=None)]
    assert import_coaches(con, Wd(), log=lambda _: None) == 2
    assert "wd:Q1893" in asked[0] and "wd:Q2 " not in asked[0]                    # seuls les clubs à effectifs sont interrogés
    assert con.execute("SELECT coach_name, end_date IS NULL FROM club_coach ORDER BY start_date").fetchall() == [("Stefano Pioli", False), ("Siniša Mihajlović", True)]
    assert import_coaches(con, Wd(), log=lambda _: None) == 2                      # idempotent
