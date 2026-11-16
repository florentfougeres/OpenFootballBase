"""Contrôles de cohérence sur l'ensemble de la base (palmarès, statistiques, carrières), à lancer avant chaque publication.

`checks.py` vérifie une saison avant son gel ; ici on cherche les incohérences qui traversent les saisons : un titre attribué à un club qui n'a pas joué
la compétition, un joueur qui a des statistiques avant ses 14 ans (deux homonymes fusionnés, le plus souvent), un titre vacant revenu après un import.
Un problème `blocking` doit empêcher la publication ; un `warning` est à relire (le détail dit quoi regarder).
"""
from __future__ import annotations

import duckdb

from openfootball.checks import Problem
from openfootball.honours import VACANT

MIN_FIELD = 10            # une compétition-saison n'est « connue en entier » qu'avec au moins ce nombre de clubs inscrits
MIN_AGE_STATS = 13        # âge minimal pour une ligne de statistiques (Falcao joue à 13 ans) ; la carrière commence avec les équipes de jeunes, dès 7 ans
MIN_AGE_CAREER = 7
MAX_LEAGUE_APPS = 80      # plus de matches de championnat dans une saison : lecture erronée
MIN_NATIONAL_SQUAD, MAX_NATIONAL_SQUAD = 11, 40
LIMIT = 25                # cas listés par contrôle (le total est toujours donné)


def _scan(con: duckdb.DuckDBPyConnection, check: str, severity: str, sql: str, what: str, args: list | None = None) -> list[Problem]:
    """Une requête `SELECT scope, detail …` : un problème par ligne (au plus LIMIT), plus une ligne de total si elle en retourne davantage."""
    rows = con.execute(sql, args or []).fetchall()
    out = [Problem(check, severity, str(scope), str(detail)) for scope, detail in rows[:LIMIT]]
    if len(rows) > LIMIT:
        out.append(Problem(check, severity, f"{len(rows)} cas", f"{what} (les {LIMIT} premiers sont listés)"))
    return out


def run_audit(con: duckdb.DuckDBPyConnection) -> list[Problem]:
    out: list[Problem] = []
    for code, year in VACANT:
        out += _scan(con, "vacant_title", "blocking", """
            SELECT co.code || ' ' || w.season_start, 'titre vacant présent : ' || w.winner_name
            FROM competition_winner w JOIN competition co ON co.id = w.competition_id WHERE co.code = ? AND w.season_start = ?""",
                     "titres vacants revenus dans le palmarès", [code, year])

    out += _scan(con, "winner_not_in_field", "warning", f"""
        SELECT co.code || ' ' || w.season_start, w.winner_name || ' sans effectif cette saison (' || f.n || ' clubs inscrits dans la compétition)'
        FROM competition_winner w JOIN competition co ON co.id = w.competition_id
        JOIN (SELECT cs.competition_id, s.start_year, count(DISTINCT cs.club_id) n, list(DISTINCT cs.club_id) clubs
              FROM club_season cs JOIN season s ON s.id = cs.season_id GROUP BY ALL HAVING count(DISTINCT cs.club_id) >= {MIN_FIELD}) f
          ON f.competition_id = w.competition_id AND f.start_year = w.season_start
        WHERE w.club_id IS NOT NULL AND NOT list_contains(f.clubs, w.club_id)
          AND NOT EXISTS (SELECT 1 FROM club_season x JOIN season sx ON sx.id = x.season_id WHERE x.club_id = w.club_id AND sx.start_year = w.season_start)
        ORDER BY co.code, w.season_start""", "vainqueurs sans aucun effectif cette saison alors que la compétition est connue en entier")

    out += _scan(con, "stats_before_birth", "warning", f"""
        SELECT p.name || ' (né en ' || year(b.birth_date) || ')', 'statistiques dès ' || min(s.season) || ' : homonymes fusionnés ou date de naissance fausse ?'
        FROM player_stat_club s JOIN player_birth b ON b.player_id = s.player_id JOIN player p ON p.id = s.player_id
        WHERE b.precision >= 9 AND try_cast(left(s.season, 4) AS INTEGER) < year(b.birth_date) + {MIN_AGE_STATS}
        GROUP BY p.name, b.birth_date ORDER BY p.name""", "joueurs avec des statistiques avant leurs 13 ans")

    out += _scan(con, "career_before_birth", "warning", f"""
        SELECT p.name || ' (né en ' || year(b.birth_date) || ')', 'carrière dès ' || min(c.start_year) || ' : homonymes fusionnés ou date de naissance fausse ?'
        FROM player_career c JOIN player_birth b ON b.player_id = c.player_id JOIN player p ON p.id = c.player_id
        WHERE b.precision >= 9 AND c.start_year < year(b.birth_date) + {MIN_AGE_CAREER}
        GROUP BY p.name, b.birth_date ORDER BY p.name""", "joueurs avec une carrière avant leurs 7 ans")

    out += _scan(con, "stats_implausible", "warning", f"""
        SELECT p.name || ' — ' || s.club || ' ' || s.season, s.apps || ' matches, ' || s.goals || ' buts (' || coalesce(s.competition_group, '?') || ')'
        FROM player_stat_club s JOIN player p ON p.id = s.player_id
        WHERE (s.apps > 0 AND s.goals >= 10 AND s.goals > 3 * s.apps) OR (s.competition_group = 'League' AND s.apps > {MAX_LEAGUE_APPS}
               AND NOT (s.season LIKE '%–%' AND (try_cast(right(s.season, 2) AS INTEGER) - try_cast(substr(s.season, 3, 2) AS INTEGER) + 100) % 100 > 1))
        ORDER BY s.goals DESC""", "lignes de statistiques invraisemblables (plus de 3 buts par match, ou trop de matches de championnat)")

    out += _scan(con, "national_squad_size", "warning", f"""
        SELECT competition || ' ' || year, n || ' joueurs'
        FROM (SELECT competition, year, count(*) n FROM national_title GROUP BY ALL)
        WHERE n < {MIN_NATIONAL_SQUAD} OR n > {MAX_NATIONAL_SQUAD}""", "éditions dont la liste est trop courte ou trop longue")

    out += _scan(con, "national_two_champions", "warning", """
        SELECT competition || ' ' || year, string_agg(DISTINCT team, ' / ')
        FROM national_title GROUP BY competition, year HAVING count(DISTINCT team) > 1""", "éditions avec plusieurs équipes victorieuses")
    return out
