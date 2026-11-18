"""Matchs (openfootball/matches.py) : lecture des deux formats de score, rapprochement des clubs, écriture idempotente, classement."""
import json

import duckdb
import pytest

from openfootball.db import migrate
from openfootball.matches import (STANDINGS_SQL, OpenFootballClient, import_leagues, norm, parse_football_json, write_matches)

PAYLOAD = {"name": "English Premier League 2025/26", "matches": [
    {"round": "Matchday 1", "date": "2025-08-15", "time": "20:00", "team1": "Liverpool FC", "team2": "AFC Bournemouth",
     "score": {"ft": [4, 2], "ht": [1, 0]}},
    {"round": "Matchday 1", "date": "2025-08-16", "time": "12:30", "team1": "Aston Villa FC", "team2": "Newcastle United FC",
     "score": [0, 0]},                                                        # saisons récentes : directement [domicile, extérieur]
    {"round": "Matchday 2", "date": "2025-08-23", "team1": "Liverpool FC", "team2": "Aston Villa FC"},   # pas encore joué
    {"round": "Final", "date": "2022-12-18", "team1": "Argentina", "team2": "France", "score": {"ft": [2, 2], "et": [3, 3], "p": [4, 2]},
     "goals1": [{"name": "Lionel Messi", "minute": "23", "penalty": True}, {"name": "Gonzalo Montiel", "minute": "118", "owngoal": True}],
     "goals2": [{"name": "Kylian Mbappé", "minute": "90", "offset": 8}], "ground": "Lusail Stadium"},
]}


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    migrate(c)
    c.execute("INSERT INTO country VALUES ('ENG', 'England', 'Angleterre')")
    c.execute("INSERT INTO competition (id, code, name_en, name_fr, country_code, level) VALUES (1, 'ENG-PL', 'Premier League', 'Premier League', 'ENG', 1)")
    c.execute("INSERT INTO season (id, start_year, label) VALUES (1, 2025, '2025/26')")
    for cid, title in ((1, "Liverpool F.C."), (2, "A.F.C. Bournemouth"), (3, "Aston Villa F.C."), (4, "Newcastle United F.C.")):
        c.execute("INSERT INTO club (id, name_en, wikipedia_title, country_code) VALUES (?, ?, ?, 'ENG')", [cid, title, title])
        c.execute("INSERT INTO competition_entry VALUES (1, 1, ?)", [cid])
    return c


def test_les_deux_formats_de_score_et_les_buteurs():
    ms = parse_football_json(PAYLOAD, "x.json")
    assert [m.ft for m in ms] == [(4, 2), (0, 0), None, (2, 2)] and ms[0].ht == (1, 0)
    final = ms[3]
    assert (final.et, final.pen, final.ground) == ((3, 3), (4, 2), "Lusail Stadium")
    assert [(g.side, g.player, g.minute, g.kind) for g in final.goals] == [
        ("home", "Lionel Messi", "23", "penalty"), ("home", "Gonzalo Montiel", "118", "own_goal"), ("away", "Kylian Mbappé", "90+8", "goal")]


def test_norm_ignore_points_et_suffixes():
    assert norm("Brighton & Hove Albion FC") == norm("Brighton & Hove Albion F.C.") == "brighton and hove albion"
    assert norm("AFC Bournemouth") == norm("A.F.C. Bournemouth")


def test_ecriture_rattache_les_clubs_et_remplace(con):
    ms = parse_football_json(PAYLOAD, "x.json")[:3]
    rep = write_matches(con, "ENG-PL", "2025/26", ms)
    assert (rep.matches, rep.played, rep.unmatched) == (3, 2, set())
    assert con.execute("SELECT home_club_id, away_club_id FROM match ORDER BY id").fetchall() == [(1, 2), (3, 4), (1, 3)]
    write_matches(con, "ENG-PL", "2025/26", ms[:1])                    # un second import remplace, il n'ajoute pas
    assert con.execute("SELECT count(*) FROM match").fetchone()[0] == 1


def test_equipe_inconnue_signalee_sans_perdre_le_match(con):
    rep = write_matches(con, "ENG-PL", "2025/26", parse_football_json({"matches": [{"team1": "Liverpool FC", "team2": "Inconnu FC", "score": [1, 0]}]}, "x"))
    assert rep.unmatched == {"Inconnu FC"}
    assert con.execute("SELECT away_name, away_club_id FROM match").fetchall() == [("Inconnu FC", None)]


def test_classement_calcule(con):
    write_matches(con, "ENG-PL", "2025/26", parse_football_json(PAYLOAD, "x")[:2])
    rows = {r[3]: (r[10], r[11]) for r in con.execute(STANDINGS_SQL).fetchall()}      # nom -> (différence, points)
    assert rows["Liverpool FC"] == (2, 3) and rows["Aston Villa FC"] == (0, 1) and rows["AFC Bournemouth"] == (-2, 0)


def test_import_ligues_utilise_le_cache_et_mappe_les_codes(con, tmp_path):
    asked = []

    def transport(url):
        asked.append(url)
        return json.dumps(PAYLOAD) if url.endswith("/2025-26/en.1.json") else None

    client = OpenFootballClient(tmp_path, transport=transport, sleep=lambda _: None)
    done = import_leagues(con, client, since=2025, keys=["en.1", "fr.1"], fresh_seasons=0, log_fn=lambda _: None)
    assert list(done) == ["ENG-PL 2025/26"]
    n = len(asked)
    import_leagues(con, client, since=2025, keys=["en.1", "fr.1"], fresh_seasons=0, log_fn=lambda _: None)
    assert len(asked) == n                                            # fichiers (et absences) lus depuis le cache


def test_clubs_de_championnat_lus_dans_club_season_et_variantes_de_nom(con):
    con.execute("DELETE FROM competition_entry")                                  # championnat : les clubs sont dans club_season
    con.execute("INSERT INTO club (id, name_en, wikipedia_title, country_code) VALUES (5, 'Real Betis', 'Real Betis', 'ENG'), (6, 'Athletic Bilbao', 'Athletic Bilbao', 'ENG')")
    for i, cid in enumerate((5, 6), 1):
        con.execute("INSERT INTO club_season (id, club_id, season_id, competition_id) VALUES (?, ?, 1, 1)", [i, cid])
    write_matches(con, "ENG-PL", "2025/26", parse_football_json({"matches": [{"team1": "Real Betis Balompié", "team2": "Athletic Club", "score": [1, 0]}]}, "x"))
    assert con.execute("SELECT home_club_id, away_club_id FROM match").fetchall() == [(5, 6)]


FULL = """= England | Premier League 2025/26

▪ Regular Season - 1
Fri Aug 15 19:00 UTC+0 @ Anfield, Liverpool, Att: 60315
  Liverpool v Bournemouth  4-2 (1-0)
     (Hugo EKITIKE 37', Cody GAKPO 49', Federico Chiesa 88', MOHAMED SALAH 90+4';
      Antoine SEMENYO 64', 76')

Liverpool: ALISSON - Virgil VAN DIJK [c], Milos KERKEZ (60' Andy ROBERTSON),
      Jeremie FRIMPONG (60' Wataru ENDO)
    Yellow: Milos KERKEZ 43'

Bournemouth: Djordje PETROVIC - Adam SMITH [c] (90' James Hill)
    Yellow: David BROOKS 14', Francisco Evanilson 81'
    Red:    Marcos SENESI 70'

Refs: Anthony Taylor, Gary Beswick

Sat Aug 23 16:30 UTC+0 @ MAPEI Stadium, Reggio Emilia, Att: 19106
  Sassuolo v Napoli  0-2 (0-1)
     (Scott McTominay 17', RODRIGO MUNIZ 58'(og))

Sat Aug 30 12:30 UTC+0 @ Villa Park, Birmingham
  Aston Villa v Newcastle United
"""


def test_detail_d_un_fichier_full():
    from openfootball.matches import parse_full_txt
    a, b, c = parse_full_txt(FULL, 2025)
    assert (a.home, a.away, a.ft, a.attendance, a.referee, a.ground) == ("Liverpool", "Bournemouth", (4, 2), 60315, "Anthony Taylor", "Anfield, Liverpool")
    assert [(g.side, g.player, g.minute) for g in a.goals] == [("home", "Hugo EKITIKE", "37"), ("home", "Cody GAKPO", "49"), ("home", "Federico Chiesa", "88"),
                                                              ("home", "MOHAMED SALAH", "90+4"), ("away", "Antoine SEMENYO", "64"), ("away", "Antoine SEMENYO", "76")]
    assert [l for l in a.lineups if l[0] == "home" and l[2] == "sub"] == [("home", "Andy ROBERTSON", "sub", "60", False), ("home", "Wataru ENDO", "sub", "60", False)]
    assert ("home", "Virgil VAN DIJK", "start", None, True) in a.lineups
    assert a.cards == [("home", "Milos KERKEZ", "43", "yellow"), ("away", "David BROOKS", "14", "yellow"),
                       ("away", "Francisco Evanilson", "81", "yellow"), ("away", "Marcos SENESI", "70", "red")]
    assert [(g.side, g.kind) for g in b.goals] == [("away", "goal"), ("away", "own_goal")]      # sans « ; » : le score dit quelle équipe a marqué
    assert (c.ft, c.goals, c.day.isoformat()) == (None, [], "2025-08-30")                          # match à venir


def test_import_full_rattache_par_la_paire_de_clubs(con, tmp_path):
    from openfootball.matches import FULL_FILES, import_full
    txt = FULL.split("Sat Aug 23")[0].replace("Liverpool v Bournemouth", "Liverpool v AFC Bournemouth")
    write_matches(con, "ENG-PL", "2025/26", parse_football_json(PAYLOAD, "x")[:2])
    client = OpenFootballClient(tmp_path, transport=lambda u: txt if "england" in u and u.endswith("1-premierleague-full.txt") and "2025-26" in u else None, sleep=lambda _: None)
    import_full(con, client, log_fn=lambda _: None)
    assert con.execute("SELECT attendance, referee FROM match WHERE home_name = 'Liverpool FC'").fetchone() == (60315, "Anthony Taylor")
    assert con.execute("SELECT count(*) FROM match_goal").fetchone()[0] == 6
    assert con.execute("SELECT count(*) FROM match_card").fetchone()[0] == 4


CWC = """= Club World Cup 2022

▪ Round 2
  Sat Feb 4 2023
    15:30  Wydad AC (MAR)          v Al Hilal (KSA)           3-5 pen. 1-1 a.e.t. (1-1, 0-0)
    18:00  Seattle Sounders (USA)  v Al Ahly SC (EGY)         0-1 (0-0)
  Sun Feb 5
           Team A                  v Team B                   2-0
▪ Final
  Sat Feb 11
    22:00  Real Madrid (ESP)       v Al Hilal (KSA)
"""

INTL = """= FIFA World Cup 2022

▪ Group A
Sun Nov 20
  Qatar                  0-2 Ecuador                  @ Al Khor, Qatar
     (Enner Valencia 16'(p),31')
Fri Nov 25
  Qatar                  1-3 Senegal                  @ Doha, Qatar
     (Mohammed Muntari 78';
      Boulaye Dia 41' Famara Diédhiou 48' Bamba Dieng 84')
Dec 1
"""


def test_dialecte_heure_equipe_v_equipe():
    from openfootball.matches import parse_txt_timed
    a, b, c, d = parse_txt_timed(CWC, 2022, "x")
    assert (a.home, a.away, a.ft, a.ht, a.et, a.pen, a.round) == ("Wydad AC", "Al Hilal", (1, 1), (0, 0), (1, 1), (3, 5), "Round 2")
    assert (b.ft, b.ht, b.day.isoformat()) == ((0, 1), (0, 0), "2023-02-04")
    assert (c.kickoff, c.ft, c.day.isoformat()) == ("18:00", (2, 0), "2023-02-05")        # continuation : reprend l'heure ; la date sans année suit
    assert (d.ft, d.round) == (None, "Final")


def test_dialecte_selections_avec_buteurs():
    from openfootball.matches import parse_txt_intl
    a, b = parse_txt_intl(INTL, 2022, "x")
    assert (a.home, a.away, a.ft, a.ground, a.group) == ("Qatar", "Ecuador", (0, 2), "Al Khor, Qatar", "Group A")
    assert [(g.side, g.player, g.minute, g.kind) for g in a.goals] == [("away", "Enner Valencia", "16", "penalty"), ("away", "Enner Valencia", "31", "goal")]
    assert [(g.side, g.player) for g in b.goals] == [("home", "Mohammed Muntari"), ("away", "Boulaye Dia"), ("away", "Famara Diédhiou"), ("away", "Bamba Dieng")]


def test_tirs_au_but_sans_prolongation_et_annee_d_une_saison_non_chronologique():
    from openfootball.matches import parse_txt_timed
    txt = """▪ Matchday 1
  Wed Oct 2 2024
    18:00  A v B   2-4 pen. (1-1, 0-1)
▪ Matchday 2
  Fri Sep 27
    16:00  C v D   0-0
  Sat Jan 11
    16:00  E v F   1-0
"""
    a, b, c = parse_txt_timed(txt, 2024, "x", split=True)
    assert (a.ft, a.ht, a.pen) == ((1, 1), (0, 1), (2, 4))
    assert (b.day.isoformat(), c.day.isoformat()) == ("2024-09-27", "2025-01-11")        # septembre reste 2024 malgré l'ordre du fichier


def test_alias_de_club_et_nom_de_competition(con):
    con.execute("INSERT INTO club (id, name_en, wikipedia_title, country_code) VALUES (9, 'Gladbach', 'Borussia Mönchengladbach', 'ENG')")
    con.execute("INSERT INTO club_season (id, club_id, season_id, competition_id) VALUES (9, 9, 1, 1)")
    from openfootball.matches import competition_title, set_competition_name
    rep = write_matches(con, "ENG-PL", "2025/26", parse_football_json({"matches": [{"team1": "Bor. Mönchengladbach", "team2": "Liverpool FC", "score": [1, 0]}]}, "x"))
    assert con.execute("SELECT home_club_id FROM match").fetchone() == (9,) and "Bor. Mönchengladbach" not in rep.unmatched
    assert competition_title("= Algeria | Ligue 1 2024/25") == "Algeria | Ligue 1" and competition_title("= Copa América 2024      # in USA") == "Copa América"
    assert competition_title("World Cup 2022") == "World Cup"
    set_competition_name(con, "OF:dz1", "= Algeria | Ligue 1 2024/25")
    set_competition_name(con, "ENG-PL", "Premier League 2025/26")                  # une compétition à nous garde son nom : rien n'est écrit
    assert con.execute("SELECT * FROM match_competition").fetchall() == [("OF:dz1", "Algeria | Ligue 1")]


def test_rattachement_des_noms_de_joueurs_a_l_effectif(con):
    from openfootball.matches import link_match_players, pick_player, _tokens
    squad = [(1, _tokens("Emile Smith Rowe")), (2, _tokens("Mohamed Salah")), (3, _tokens("Gabriel Jesus")), (4, _tokens("Gabriel Martinelli"))]
    assert pick_player(squad, "MOHAMED SALAH") == 2 and pick_player(squad, "Smith Rowe") == 1
    assert pick_player(squad, "Gabriel") is None and pick_player(squad, "Inconnu") is None           # ambigu ou absent : aucun lien
    write_matches(con, "ENG-PL", "2025/26", parse_football_json({"matches": [{"team1": "Liverpool FC", "team2": "AFC Bournemouth", "score": [1, 0]}]}, "x"))
    con.execute("INSERT INTO player (id, name) VALUES (1, 'Mohamed Salah'), (2, 'Alisson')")
    con.execute("INSERT INTO club_season (id, club_id, season_id, competition_id) VALUES (1, 1, 1, 1)")
    for pid in (1, 2):
        con.execute("INSERT INTO player_club_season (id, player_id, club_season_id, confidence, source) VALUES (?, ?, 1, 'attested', 'wikipedia_season')", [pid, pid])
    mid = con.execute("SELECT id FROM match").fetchone()[0]
    con.execute("INSERT INTO match_goal (match_id, seq, side, player_name, kind) VALUES (?, 1, 'home', 'MOHAMED SALAH', 'goal'), (?, 2, 'away', 'Alisson', 'own_goal'), (?, 3, 'home', 'Nobody', 'goal')", [mid] * 3)
    assert link_match_players(con, log_fn=lambda _: None)["match_goal"] == 2                      # le csc d'« Alisson » est compté chez Liverpool, équipe adverse du bénéficiaire
    assert con.execute("SELECT seq, player_id FROM match_goal ORDER BY seq").fetchall() == [(1, 1), (2, 2), (3, None)]


def test_championnat_de_world_rattache_a_notre_competition():
    from openfootball.matches import _txt_target
    assert _txt_target("world", "africa/algeria/2024-25_dz1.txt")[:3] == ("DZA-L1", "2024/25", 2024)
    assert _txt_target("world", "africa/zambia/2024_zm9.txt")[:2] == ("OF:zm9", "2024")            # sans équivalent chez nous : reste « OF:* »
    assert _txt_target("club-worldcup", "2022/clubworldcup.txt")[:2] == ("FIFA-CWC", "2022")
    assert _txt_target("south-america", "copa-libertadores/2023_copal.txt")[0] == "CONMEBOL-CL"
