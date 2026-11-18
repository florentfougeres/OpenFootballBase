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


def test_date_de_naissance_peu_fiable_retiree_et_non_reimportee(monkeypatch):
    import datetime
    import openfootball.enrich as enrich
    con = _db()
    con.execute("INSERT INTO player (id, name) VALUES (1, 'Mike Flynn'), (2, 'Autre')")
    con.execute("INSERT INTO player_wikidata VALUES (1, 'Q6846866'), (2, 'Q2')")
    con.execute("INSERT INTO player_birth VALUES (1, DATE '1980-10-17', 11)")
    asked = []
    monkeypatch.setattr(enrich, "parse_birth", lambda rows: {q: (datetime.date(1990, 1, 1), 11) for q in rows})

    class Wd:
        def query(self, sparql):
            asked.append(sparql)
            return [q for q in ("Q2", "Q6846866") if q in sparql]     # ce que Wikidata répondrait pour les éléments demandés
    enrich.enrich_birth_dates(con, Wd(), log=lambda _: None)
    assert "Q6846866" not in asked[0]                                            # jamais réinterrogé
    assert con.execute("SELECT player_id FROM player_birth ORDER BY 1").fetchall() == [(2,)]   # la date fausse est partie, l'autre est écrite


def test_champion_calcule_different_du_palmares_signale():
    con = _db()
    con.execute("INSERT INTO season (id, start_year, label) VALUES (1, 2020, '2020/21')")
    for cid, name in ((1, "Alpha"), (2, "Beta")):
        con.execute("INSERT INTO club (id, name_en, wikipedia_title, country_code) VALUES (?, ?, ?, 'FRA')", [cid, name, name])
    # Alpha gagne à l'aller et au retour : champion calculé = Alpha (6 points) ; le palmarès dit Beta
    for i, (h, a, hid, aid) in enumerate((("Alpha", "Beta", 1, 2), ("Beta", "Alpha", 2, 1)), 1):
        con.execute("INSERT INTO match (id, competition_code, season_label, home_name, away_name, home_club_id, away_club_id, ft_home, ft_away, source_ref) "
                    "VALUES (?, 'FRA-L1', '2020/21', ?, ?, ?, ?, ?, ?, 'x')", [i, h, a, hid, aid, 1 if h == "Alpha" else 0, 0 if h == "Alpha" else 1])
    con.execute("INSERT INTO competition_winner (competition_id, season_start, winner_qid, winner_name, season_qid, club_id) VALUES (1, 2020, 'Q2', 'Beta', 'Q1', 2)")
    got = _checks(con)["champion_mismatch"]
    assert len(got) == 1 and "Alpha" in got[0].detail and "Beta" in got[0].detail
