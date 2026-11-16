"""Contrôles de cohérence de la base entière (openfootball/audit.py), sur le vrai schéma en mémoire."""
import duckdb

from openfootball.audit import run_audit
from openfootball.db import migrate


def _db() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    migrate(con)
    con.execute("INSERT INTO country VALUES ('FRA', 'France', 'France')")
    con.execute("INSERT INTO competition (id, code, name_en, name_fr, country_code, level) VALUES (1, 'FRA-L1', 'Ligue 1', 'Ligue 1', 'FRA', 1)")
    return con


def _checks(con) -> dict[str, list]:
    out: dict[str, list] = {}
    for p in run_audit(con):
        out.setdefault(p.check, []).append(p)
    return out


def test_base_vide_sans_probleme():
    assert run_audit(_db()) == []


def test_titre_vacant_qui_revient_bloque():
    con = _db()
    con.execute("INSERT INTO competition_winner (competition_id, season_start, winner_qid, winner_name, season_qid) VALUES (1, 1992, 'Q132885', 'Olympique de Marseille', 'Q1')")
    got = _checks(con)
    assert [p.severity for p in got["vacant_title"]] == ["blocking"]


def test_statistiques_avant_14_ans_et_buts_impossibles():
    con = _db()
    con.execute("INSERT INTO player (id, name) VALUES (1, 'Mike Flynn')")
    con.execute("INSERT INTO player_birth VALUES (1, DATE '1980-03-04', 11)")
    con.execute("INSERT INTO player_stat_club VALUES (1, 1, 'Oldham', 'Oldham Athletic', '1987–88', NULL, 'League', 31, 1, NULL), "
                "(1, 2, 'Oldham', 'Oldham Athletic', '2020', NULL, 'League', 11, 100, NULL), "
                "(1, 3, 'Zagreb', 'NK Zagreb', '1998–04', NULL, 'League', 124, 28, NULL)")
    got = _checks(con)
    assert [p.scope for p in got["stats_before_birth"]] == ["Mike Flynn (né en 1980)"]
    assert len(got["stats_implausible"]) == 1 and "100 buts" in got["stats_implausible"][0].detail   # la saison sur 6 ans (124 matches) est normale


def test_edition_nationale_trop_courte():
    con = _db()
    con.execute("INSERT INTO national_title (competition, year, team, player_name, source_title) VALUES ('EURO', 2000, 'France', 'A', 'x')")
    assert [p.scope for p in _checks(con)["national_squad_size"]] == ["EURO 2000"]
