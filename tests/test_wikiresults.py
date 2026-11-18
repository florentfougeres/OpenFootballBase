"""Résultats de la saison en cours lus sur Wikipedia (openfootball/wikiresults.py) : lecture de la matrice et fusion avec les matchs d'OpenFootball."""
import duckdb
import pytest

from openfootball.db import migrate
from openfootball.matches import Match, write_matches
from openfootball.wikiresults import apply_results, import_wikipedia_results, parse_matrix

PAGE = """{{#invoke:Sports table|main|style=WDL
|name_ARS=[[Arsenal F.C.|Arsenal]]
|name_AVL=[[Aston Villa F.C.|Aston Villa]]
|name_BOU={{nowrap|[[AFC Bournemouth|Bournemouth]]}}
<!-- Match results -->
| match_ARS_AVL = 3–0
| match_ARS_BOU =
| match_AVL_ARS = 0–1
| match_AVL_BOU = {{small|6 Dec}}
| match_BOU_ARS = [https://example.org/m 2–2]
| match_BOU_AVL = 1-1
}}"""


def test_matrice_noms_et_scores_joues():
    names, ms = parse_matrix(PAGE)
    assert names == {"ARS": ("Arsenal F.C.", "Arsenal"), "AVL": ("Aston Villa F.C.", "Aston Villa"), "BOU": ("AFC Bournemouth", "Bournemouth")}
    assert {(m.home, m.away): m.ft for m in ms} == {("ARS", "AVL"): (3, 0), ("AVL", "ARS"): (0, 1), ("BOU", "ARS"): (2, 2), ("BOU", "AVL"): (1, 1)}   # vide ou « 6 Dec » : pas joué


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    migrate(c)
    c.execute("INSERT INTO country VALUES ('ENG', 'England', 'Angleterre')")
    c.execute("INSERT INTO competition (id, code, name_en, name_fr, country_code, level) VALUES (1, 'ENG-PL', 'Premier League', 'Premier League', 'ENG', 1)")
    c.execute("INSERT INTO season (id, start_year, label) VALUES (1, 2026, '2026/27')")
    for cid, title in ((1, "Arsenal F.C."), (2, "Aston Villa F.C."), (3, "AFC Bournemouth")):
        c.execute("INSERT INTO club (id, name_en, wikipedia_title, country_code) VALUES (?, ?, ?, 'ENG')", [cid, title, title])
        c.execute("INSERT INTO club_season (id, club_id, season_id, competition_id) VALUES (?, ?, 1, 1)", [cid, cid])
    return c


def test_fusion_complete_cree_ignore_et_rapporte_les_desaccords(con):
    # OpenFootball : Arsenal–Aston Villa sans score (en retard), Aston Villa–Arsenal 0-1 (identique), Bournemouth–Arsenal 3-1 (désaccord avec 2-2)
    write_matches(con, "ENG-PL", "2026/27", [
        Match("Arsenal FC", "Aston Villa FC", day=None, source_ref="x"),
        Match("Aston Villa FC", "Arsenal FC", ft=(0, 1), source_ref="x"),
        Match("AFC Bournemouth", "Arsenal FC", ft=(3, 1), source_ref="x")])
    names, ms = parse_matrix(PAGE)
    rep = apply_results(con, "ENG-PL", "2026/27", names, ms, "wikipedia:test")
    assert (rep.updated, rep.inserted, rep.same, len(rep.conflicts)) == (1, 1, 1, 1)
    rows = con.execute("SELECT m.home_name, m.away_name, m.ft_home, m.ft_away, r.source FROM match m LEFT JOIN match_result_source r ON r.match_id = m.id ORDER BY m.id").fetchall()
    assert rows[0] == ("Arsenal FC", "Aston Villa FC", 3, 0, "wikipedia")           # complété
    assert rows[1][2:] == (0, 1, None)                                              # identique : provenance inchangée
    assert rows[2][2:] == (3, 1, None) and "OpenFootball 3-1, Wikipedia 2-2" in rep.conflicts[0]      # le score d'OpenFootball est gardé
    assert rows[3] == ("Bournemouth", "Aston Villa", 1, 1, "wikipedia")             # créé : absent d'OpenFootball


def test_import_lit_les_pages_de_la_saison_en_cours(con, monkeypatch):
    import openfootball.wikiresults as wr
    monkeypatch.setattr(wr, "current_start_year", lambda: 2026)

    class Page:
        exists, wikitext = True, PAGE

    class Wp:
        def get_pages(self, titles):
            self.titles = titles
            return [Page() for _ in titles]

    wp = Wp()
    out = import_wikipedia_results(con, {"en": wp}, leagues={"ENG-PL": [("en", "{y}–{yy} Premier League")]}, log_fn=lambda _: None)
    assert wp.titles == ["2026–27 Premier League"] and out["ENG-PL"].inserted == 4


FR = """{{Foot résultat début|[[Angers Sporting Club de l'Ouest|SCO]]|[[Association de la jeunesse auxerroise|AJA]]|[[Stade brestois 29|SB29]]|mise à jour=09 novembre}}
{{Foot résultat|[[Angers Sporting Club de l'Ouest|Angers SCO]]|XXX|J23|0-2}}
{{Foot résultat|[[Association de la jeunesse auxerroise|AJ Auxerre]]|1-3|XXX|J34}}
{{Foot résultat|[[Stade brestois 29]]|5-1|2-0|XXX}}
"""
ES = """{{#invoke:football results|main
|nombre_ALA=[[Deportivo Alavés|Alavés]]
|nombre_ATH=[[Athletic Club|Athletic]]
| partido_ALA_ATH =
| partido_ATH_ALA = [[Derbi vasco|2–1]]
| partido_ALA_ATM = 1-2
}}"""


def test_matrice_francaise_croisee():
    from openfootball.wikiresults import parse_foot_resultat
    names, ms = parse_foot_resultat(FR)
    assert names["T1"] == ("Association de la jeunesse auxerroise", "AJA")
    assert {(m.home, m.away): m.ft for m in ms} == {("T0", "T2"): (0, 2), ("T1", "T0"): (1, 3), ("T2", "T0"): (5, 1), ("T2", "T1"): (2, 0)}     # « J23 » : à venir


def test_matrice_espagnole_avec_score_en_lien():
    names, ms = parse_matrix(ES)
    assert names["ATH"] == ("Athletic Club", "Athletic")
    assert {(m.home, m.away): m.ft for m in ms} == {("ATH", "ALA"): (2, 1), ("ALA", "ATM"): (1, 2)}


def test_club_d_une_page_francaise_reconnu_par_son_titre_dans_cette_langue(con):
    con.execute("INSERT INTO club (id, name_en, wikipedia_title, wikidata_qid, country_code) VALUES (9, 'AJ Auxerre', 'AJ Auxerre', 'Q1', 'ENG')")
    con.execute("INSERT INTO entity_wiki VALUES ('Q1', 'fr', 'Association de la jeunesse auxerroise')")
    names, ms = parse_foot_resultat_for_test()
    rep = apply_results(con, "ENG-PL", "2026/27", names, ms, "wikipedia:fr:x", "fr")
    assert "AJA" not in rep.unresolved and rep.inserted == 0 and rep.updated == 0           # AJA est reconnu (pas de match entre deux clubs reconnus ici)


def parse_foot_resultat_for_test():
    from openfootball.wikiresults import parse_foot_resultat
    return parse_foot_resultat(FR)
