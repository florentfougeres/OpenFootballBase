"""Matchs : résultats, buteurs et calendriers lus dans les données ouvertes du projet OpenFootball (github.com/openfootball, CC0).

Troisième source du projet, à côté de Wikipedia et de Wikidata (voir SPEC §1). On ne reprend que les faits de match (date, score, mi-temps,
prolongation, tirs au but, stade, affluence, arbitre, buteurs) ; les effectifs restent ceux de Wikipedia.

Deux temps, séparés pour pouvoir tester chacun sans réseau :
  - lire : un fichier -> une liste de `Match` (`parse_football_json`) ;
  - écrire : `write_matches` remplace les matchs d'une compétition-saison et rattache chaque équipe à un club de `club` par son nom.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

import duckdb
import requests

log = logging.getLogger(__name__)

RAW = "https://raw.githubusercontent.com/openfootball"
MIN_INTERVAL_S = 0.2
MAX_ATTEMPTS = 5

# football.json : fichier de chaque championnat -> notre code de compétition. Un fichier sans compétition chez nous est gardé sous « OF:<clé> ».
LEAGUES: dict[str, str] = {
    "en.1": "ENG-PL", "en.2": "ENG-CH", "de.1": "DEU-BL", "de.2": "DEU-B2", "es.1": "ESP-LL", "es.2": "ESP-SD",
    "fr.1": "FRA-L1", "fr.2": "FRA-L2", "it.1": "ITA-SA", "it.2": "ITA-SB", "nl.1": "NLD-ED", "pt.1": "PRT-PL",
    "tr.1": "TUR-SL", "gr.1": "GRC-L1", "sco.1": "SCO-L1", "mx.1": "MEX-L1", "au.1": "AUS-L1", "at.1": "AUT-L1",
    "be.1": "BEL-PL", "dz.1": "DZA-L1", "eg.1": "EGY-L1", "ma.1": "MAR-L1", "uefa.cl": "UEFA-CL",
    "en.3": "OF:en.3", "en.4": "OF:en.4", "at.2": "OF:at.2",
}


@dataclass
class Goal:
    side: str                       # home | away
    player: str
    minute: str | None = None
    kind: str = "goal"              # goal | penalty | own_goal


@dataclass
class Match:
    home: str
    away: str
    round: str | None = None
    group: str | None = None
    day: date | None = None
    kickoff: str | None = None
    ft: tuple[int, int] | None = None
    ht: tuple[int, int] | None = None
    et: tuple[int, int] | None = None
    pen: tuple[int, int] | None = None
    ground: str | None = None
    attendance: int | None = None
    referee: str | None = None
    goals: list[Goal] = field(default_factory=list)
    source_ref: str = ""


# --------------------------------------------------------------------------------------------------
# Réseau : fichiers bruts GitHub, mis en cache sur disque (un fichier passé ne change plus).

class OpenFootballClient:
    def __init__(self, cache_dir: str | Path = "cache/openfootball", *, transport: Callable[[str], str | None] | None = None,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._transport = transport or self._http
        self._sleep = sleep
        self._last = 0.0
        self._session = requests.Session()
        contact = os.environ.get("OPENFOOTBALL_CONTACT", "unset")
        self._session.headers["User-Agent"] = f"OpenFootballBaseBot/0.1 (open football squads project; contact: {contact})"

    def _http(self, url: str) -> str | None:
        """Texte du fichier, ou None s'il n'existe pas (404). Toute autre erreur persistante lève : ce n'est pas une absence."""
        for attempt in range(MAX_ATTEMPTS):
            wait = MIN_INTERVAL_S - (time.monotonic() - self._last)
            if wait > 0:
                self._sleep(wait)
            self._last = time.monotonic()
            r = self._session.get(url, timeout=60)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                return r.text
            log.warning("%s -> HTTP %s (essai %d)", url, r.status_code, attempt + 1)
            self._sleep(2 ** attempt)
        raise RuntimeError(f"{url} : échec persistant")

    def get(self, url: str, *, fresh: bool = False) -> str | None:
        """`fresh` : relit même si le fichier est en cache (saison en cours). Un 404 est mémorisé comme un fichier absent."""
        path = self.cache_dir / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
        if path.exists() and not fresh:
            text = path.read_text(encoding="utf-8")
            return None if text == "\0404" else text
        text = self._transport(url)
        path.write_text("\0404" if text is None else text, encoding="utf-8")
        return text


# --------------------------------------------------------------------------------------------------
# Lecture

def _pair(v) -> tuple[int, int] | None:
    return (int(v[0]), int(v[1])) if isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(x, int) for x in v) else None


def _day(raw) -> date | None:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", raw or "")
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
    except ValueError:
        return None


def _goals(items, side: str) -> list[Goal]:
    out = []
    for g in items or []:
        name = (g.get("name") or "").strip()
        if not name:
            continue
        minute = str(g["minute"]) + (f"+{g['offset']}" if g.get("offset") else "") if g.get("minute") is not None else None
        out.append(Goal(side, name, minute, "own_goal" if g.get("owngoal") else "penalty" if g.get("penalty") else "goal"))
    return out


def parse_football_json(payload: dict, ref: str) -> list[Match]:
    """football.json / worldcup.json / euro.json : {"matches": [{round, date, time, team1, team2, score, goals1, goals2, group, ground}]}.
    `score` est tantôt {"ft": [a, b], "ht": …, "et": …, "p": …} tantôt directement [a, b] (saisons récentes)."""
    out: list[Match] = []
    for m in payload.get("matches", []):
        t1, t2 = m.get("team1"), m.get("team2")
        if isinstance(t1, dict):
            t1 = t1.get("name")
        if isinstance(t2, dict):
            t2 = t2.get("name")
        if not t1 or not t2:
            continue
        sc = m.get("score")
        if isinstance(sc, list):
            sc = {"ft": sc}
        sc = sc or {}
        ground = m.get("ground") or m.get("stadium")
        out.append(Match(
            home=t1, away=t2, round=m.get("round"), group=m.get("group"), day=_day(m.get("date")), kickoff=m.get("time"),
            ft=_pair(sc.get("ft")), ht=_pair(sc.get("ht")), et=_pair(sc.get("et")), pen=_pair(sc.get("p")),
            ground=ground if isinstance(ground, str) else (ground or {}).get("name"),
            attendance=m.get("attendance") if isinstance(m.get("attendance"), int) else None,
            referee=(m.get("referee") or {}).get("name") if isinstance(m.get("referee"), dict) else m.get("referee"),
            goals=_goals(m.get("goals1"), "home") + _goals(m.get("goals2"), "away"), source_ref=ref))
    return out


# --------------------------------------------------------------------------------------------------
# Rapprochement des noms d'équipes avec nos clubs

_STOP = {"afc", "fc", "cf", "ac", "sc", "the", "fk", "sk", "if", "bk", "sv", "ssc", "as", "us", "rc", "cd", "ud", "de", "la", "le", "del", "di", "da", "do", "club", "rcd"}


def norm(text: str) -> str:
    """« Brighton & Hove Albion FC » et « Brighton & Hove Albion F.C. » donnent la même clé."""
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower().replace("&", " and ").replace(".", "")
    s = re.sub(r"\(.*?\)", " ", s)
    return " ".join(w for w in re.sub(r"[^a-z0-9]+", " ", s).split() if w not in _STOP)


def _club_index(con: duckdb.DuckDBPyConnection, code: str, label: str) -> dict[str, int]:
    """Clés de nom -> club, pour les clubs inscrits dans cette compétition cette saison (sinon dans la compétition, toutes saisons)."""
    # Les championnats ont leurs clubs dans `club_season` (effectifs), les coupes dans `competition_entry` (participants) : on lit les deux.
    members = """SELECT cs.club_id FROM club_season cs JOIN competition co ON co.id = cs.competition_id JOIN season s ON s.id = cs.season_id
                 WHERE co.code = ?1 AND (?2 IS NULL OR s.label = ?2)
                 UNION SELECT ce.club_id FROM competition_entry ce JOIN competition co ON co.id = ce.competition_id
                 JOIN season s ON s.id = ce.season_id WHERE co.code = ?1 AND (?2 IS NULL OR s.label = ?2)"""
    names = "SELECT cl.id, cl.name_en, cl.wikipedia_title, cl.name_local, cl.name_fr FROM club cl WHERE cl.id IN (" + members + ")"
    rows = con.execute(names, [code, label]).fetchall() or con.execute(names, [code, None]).fetchall()
    index: dict[str, int] = {}
    if not rows and not code.startswith("OF:"):          # compétition sans clubs inscrits (Coupe du monde des clubs…) : tous les clubs à effectifs, noms sans ambiguïté seulement
        seen: dict[str, set[int]] = {}
        for cid, *ns in con.execute("""SELECT cl.id, cl.name_en, cl.wikipedia_title, cl.name_local, cl.name_fr FROM club cl
                                       WHERE EXISTS (SELECT 1 FROM club_season cs WHERE cs.club_id = cl.id)""").fetchall():
            for n in ns:
                if n and norm(n):
                    seen.setdefault(norm(n), set()).add(cid)
        index = {k: next(iter(v)) for k, v in seen.items() if len(v) == 1}
    for cid, *names in rows:
        for n in names:
            if n and norm(n):
                index.setdefault(norm(n), cid)
    if index:                                            # compétition connue : les alias s'ajoutent (pas pour une compétition `OF:*`, sans club chez nous)
        ids = dict(con.execute("SELECT wikipedia_title, id FROM club WHERE wikipedia_title IN (SELECT unnest(?))", [sorted(set(CLUB_ALIASES.values()))]).fetchall())
        for alias, title in CLUB_ALIASES.items():
            if title in ids:
                index.setdefault(norm(alias), ids[title])
    return index


# Noms de clubs écrits par OpenFootball qui ne ressemblent pas au titre Wikipedia : nom de la source -> titre de la page du club dans `club`.
# Un alias n'est appliqué que si la cible existe ; un club qui n'est pas dans notre base (Wiener Neustadt, Llagostera…) reste sans rattachement.
CLUB_ALIASES: dict[str, str] = {
    "RB Salzburg": "FC Red Bull Salzburg", "FC Trenkwalder Admira": "Admira Wacker", "Sporting Lokeren": "K.S.C. Lokeren Oost-Vlaanderen",
    "TSV 1860 München": "TSV 1860 Munich", "Bor. Mönchengladbach": "Borussia Mönchengladbach", "Ghazl Al Mehalla": "Ghazl El Mahalla SC",
    "Ittihad El Iskandary": "Al Ittihad Alexandria Club", "Espanyol Barcelona": "RCD Espanyol", "RCD Espanyol de Barcelona": "RCD Espanyol",
    "FC Barcelona B": "FC Barcelona Atlètic", "SM Caen": "Stade Malherbe Caen", "EA Guingamp": "En Avant de Guingamp",
    "Aris Saloniki": "Aris Thessaloniki F.C.", "AEK Athen": "AEK Athens F.C.", "OFI Heraklion": "OFI Crete F.C.",
    "AE Lárissa": "Athlitiki Enosi Larissa F.C.", "GS Kallithea": "Athens Kallithea F.C.", "AE Kifisias": "A.E. Kifisia F.C.",
    "Chievo Verona": "AC ChievoVerona", "Trapani Calcio": "FC Trapani 1905", "Ascoli Picchio FC": "Ascoli Calcio 1898 FC",
    "Vicenza Calcio": "LR Vicenza", "Como Calcio": "Como 1907", "Raja Casablanca": "Raja CA", "Maghrib de Fès": "Maghreb Fez",
    "Gallos Blancos": "Querétaro F.C.", "Monarcas Morelia": "Atlético Morelia", "SBV Excelsior": "Excelsior Rotterdam", "PSV": "PSV Eindhoven",
    "NEC": "NEC Nijmegen", "AVS": "AVS Futebol SAD", "CSKA Moskva": "PFC CSKA Moscow", "Zenit St. Petersburg": "FC Zenit Saint Petersburg",
    "Dinamo Kiev": "FC Dynamo Kyiv", "Spartak Moskva": "FC Spartak Moscow", "Lokomotiv Moskva": "FC Lokomotiv Moscow", "FC Steaua Bucureşti": "FCSB",
}


def resolve_club(index: dict[str, int], team: str) -> int | None:
    """Club de `team` : clé de nom identique, sinon le seul club de la compétition dont les mots contiennent ceux de l'équipe (ou l'inverse) :
    « Real Betis Balompié » -> « Real Betis », « Athletic Club » -> « Athletic Bilbao ». Deux candidats possibles : aucun (jamais au hasard)."""
    key = norm(team)
    if key in index:
        return index[key]
    words = set(key.split())
    found = {cid for k, cid in index.items() if words and (words <= set(k.split()) or set(k.split()) <= words)
             and any(len(w) >= 4 for w in words & set(k.split()))}
    return found.pop() if len(found) == 1 else None


# --------------------------------------------------------------------------------------------------
# Écriture

@dataclass
class WriteReport:
    matches: int = 0
    played: int = 0
    unmatched: set[str] = field(default_factory=set)       # équipes sans club correspondant


def write_matches(con: duckdb.DuckDBPyConnection, code: str, label: str, matches: list[Match]) -> WriteReport:
    """Remplace les matchs de cette compétition-saison (un import = l'état courant de la source)."""
    report = WriteReport()
    index = _club_index(con, code, label)
    next_id = con.execute("SELECT coalesce(max(id), 0) + 1 FROM match").fetchone()[0]
    con.execute("BEGIN")
    try:
        for child in ("match_goal", "match_lineup", "match_card", "match_result_source"):
            con.execute(f"DELETE FROM {child} WHERE match_id IN (SELECT id FROM match WHERE competition_code = ? AND season_label = ?)", [code, label])
        con.execute("DELETE FROM match WHERE competition_code = ? AND season_label = ?", [code, label])
        for m in matches:
            hid, aid = resolve_club(index, m.home), resolve_club(index, m.away)
            if hid is None and index:
                report.unmatched.add(m.home)
            if aid is None and index:
                report.unmatched.add(m.away)
            con.execute("INSERT INTO match (id, competition_code, season_label, round, group_name, match_date, kickoff, home_name, away_name, home_club_id, away_club_id,"
                        " ft_home, ft_away, ht_home, ht_away, et_home, et_away, pen_home, pen_away, ground, attendance, referee, source_ref)"
                        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                next_id, code, label, m.round, m.group, m.day, m.kickoff, m.home, m.away, hid, aid,
                *(m.ft or (None, None)), *(m.ht or (None, None)), *(m.et or (None, None)), *(m.pen or (None, None)),
                m.ground, m.attendance, m.referee, m.source_ref])
            for seq, g in enumerate(m.goals, 1):
                con.execute("INSERT INTO match_goal (match_id, seq, side, player_name, minute, kind) VALUES (?,?,?,?,?,?)", [next_id, seq, g.side, g.player, g.minute, g.kind])
            report.matches += 1
            report.played += m.ft is not None
            next_id += 1
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return report


# --------------------------------------------------------------------------------------------------
# Import des championnats (football.json)

def competition_title(raw: str | None) -> str | None:
    """« FIFA World Cup 2022 » -> « FIFA World Cup » ; « Algeria | Ligue 1 2024/25 » -> « Algeria | Ligue 1 » ; « Copa América 2024  # in USA » -> « Copa América »."""
    name = re.sub(r"\s+#.*$", "", (raw or "").lstrip("= ").strip())
    name = re.sub(r"\s*\d{4}(?:[/-]\d{2,4})?(?:\s*-\s*\d{4})?$", "", name).strip()
    return name or None


def set_competition_name(con: duckdb.DuckDBPyConnection, code: str, raw: str | None) -> None:
    """Nom d'une compétition `OF:*` (celle d'un fichier source), pour l'affichage ; les compétitions qui existent chez nous gardent leur nom."""
    if code.startswith("OF:") and (name := competition_title(raw)):
        con.execute("INSERT INTO match_competition VALUES (?, ?) ON CONFLICT (code) DO UPDATE SET name = excluded.name", [code, name])


def season_label(year: int) -> str:
    return f"{year}/{str(year + 1)[2:]}"


def current_start_year(today: date | None = None) -> int:
    t = today or date.today()
    return t.year if t.month >= 7 else t.year - 1


def import_leagues(con: duckdb.DuckDBPyConnection, client: OpenFootballClient, *, since: int = 2010, keys: list[str] | None = None,
                   fresh_seasons: int = 2, log_fn: Callable[[str], None] = print) -> dict[str, WriteReport]:
    """Tous les championnats de football.json de `since` à la saison en cours ; les `fresh_seasons` dernières sont relues à chaque passage."""
    last = current_start_year()
    done: dict[str, WriteReport] = {}
    for year in range(since, last + 1):
        folder = f"{year}-{str(year + 1)[2:]}"
        for key in keys or list(LEAGUES):
            text = client.get(f"{RAW}/football.json/master/{folder}/{key}.json", fresh=year > last - fresh_seasons)
            if text is None:
                continue
            ref = f"football.json/{folder}/{key}.json"
            matches = parse_football_json(json.loads(text), ref)
            if not matches:
                continue
            code, label = LEAGUES.get(key, f"OF:{key}"), season_label(year)
            rep = write_matches(con, code, label, matches)
            set_competition_name(con, code, json.loads(text).get("name"))
            done[f"{code} {label}"] = rep
            extra = f", {len(rep.unmatched)} équipes sans club ({', '.join(sorted(rep.unmatched)[:3])}…)" if rep.unmatched else ""
            log_fn(f"  {code} {label} : {rep.matches} matchs ({rep.played} joués){extra}")
    return done


# --------------------------------------------------------------------------------------------------
# Tournois de sélections (worldcup.json, euro.json) : même format, avec buteurs et stades. Équipes nationales : pas de club à rattacher.

TOURNAMENTS: dict[str, tuple[str, str, list[int]]] = {          # code -> (dépôt, fichier, éditions)
    "OF:worldcup": ("worldcup.json", "worldcup.json", [1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978, 1982, 1986, 1990,
                                                        1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022, 2026]),
    "OF:euro": ("euro.json", "euro.json", [2020, 2024]),
}


def import_tournaments(con: duckdb.DuckDBPyConnection, client: OpenFootballClient, *, fresh_from: int | None = None,
                       log_fn: Callable[[str], None] = print) -> dict[str, WriteReport]:
    """Les éditions passées viennent du cache ; celles de `fresh_from` et après (tournoi en cours ou à venir) sont relues."""
    fresh_from = fresh_from if fresh_from is not None else date.today().year - 1
    done: dict[str, WriteReport] = {}
    for code, (repo, fname, years) in TOURNAMENTS.items():
        for year in years:
            text = client.get(f"{RAW}/{repo}/master/{year}/{fname}", fresh=year >= fresh_from)
            if text is None:
                continue
            matches = parse_football_json(json.loads(text), f"{repo}/{year}/{fname}")
            if matches:
                done[f"{code} {year}"] = write_matches(con, code, str(year), matches)
                set_competition_name(con, code, json.loads(text).get("name"))
                log_fn(f"  {code} {year} : {done[f'{code} {year}'].matches} matchs")
    return done


# --------------------------------------------------------------------------------------------------
# Détail des matchs : fichiers « *-full.txt » (buteurs avec minute, compositions, remplacements, cartons, arbitre, stade, affluence).

FULL_FILES: dict[str, tuple[str, str]] = {                      # code -> (dépôt, chemin ; {y} = année de début, {yy} = deux derniers chiffres de la fin)
    "ENG-PL": ("england", "{y}-{yy}/1-premierleague-full.txt"), "DEU-BL": ("deutschland", "{y}-{yy}/1-bundesliga-full.txt"),
    "ESP-LL": ("espana", "{y}-{yy}/1-liga-full.txt"), "ITA-SA": ("italy", "{y}-{yy}/1-seriea-full.txt"),
    "FRA-L1": ("europe", "france/{y}-{yy}_fr1-full.txt"), "AUT-L1": ("austria", "{y}-{yy}/1-bundesliga-full.txt"),
}
FIRST_FULL_YEAR = 2025


@dataclass
class FullMatch:
    home: str
    away: str
    day: date | None = None
    ground: str | None = None
    attendance: int | None = None
    ft: tuple[int, int] | None = None
    referee: str | None = None
    goals: list[Goal] = field(default_factory=list)
    lineups: list[tuple[str, str, str, str | None, bool]] = field(default_factory=list)      # (côté, joueur, rôle, minute, capitaine)
    cards: list[tuple[str, str, str | None, str]] = field(default_factory=list)              # (côté, joueur, minute, jaune|rouge)


_MONTHS = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
_HEAD = re.compile(r"^\w{3} (?P<mon>\w{3}) (?P<day>\d{1,2}) \d{2}:\d{2} UTC[+-]\d+(?: @ (?P<ground>.*?))?(?:, Att: (?P<att>\d+))?\s*$")
_SCORE = re.compile(r"^ {2}(?P<h>.+?) v (?P<a>.+?)(?:\s{2,}(?P<fh>\d+)-(?P<fa>\d+)(?: \(\d+-\d+\))?)?\s*$")
_MIN = r"\d+(?:\+\d+)?"
_GOAL_ONLY = re.compile(rf"^({_MIN})'(?:\((og|p|pen)\))?$")
_GOAL = re.compile(rf"^(.*?)\s+({_MIN})'(?:\((og|p|pen)\))?$")
_PLAYER = re.compile(rf"^(?P<name>.+?)(?P<cap> \[c\])?(?: \((?P<min>{_MIN})' (?P<sub>.+)\))?$")


def _kind(flag: str | None) -> str:
    return "own_goal" if flag == "og" else "penalty" if flag in ("p", "pen") else "goal"


def _parse_goals(text: str, ft: tuple[int, int] | None) -> list[Goal]:
    """`(A 17', B 57'; C 90'(og))` : à gauche de « ; » les buts de l'équipe qui reçoit, à droite ceux de l'autre ; sans « ; », une seule équipe a marqué (le score dit laquelle)."""
    text = text.strip()
    parts = [p.strip() for p in (text[1:-1] if text.startswith("(") and text.endswith(")") else text).split(";")]    # une seule paire : « 58'(og)) » garde son « ) »
    sides = ["home", "away"] if len(parts) == 2 else ["away" if ft and ft[0] == 0 else "home"]
    out: list[Goal] = []
    for side, part in zip(sides, parts):
        last = None
        for tok in (x.strip() for x in part.split(",")):
            if (m := _GOAL_ONLY.match(tok)) and last:
                out.append(Goal(side, last, m.group(1), _kind(m.group(2))))
            elif m := _GOAL.match(tok):
                last = m.group(1)
                out.append(Goal(side, last, m.group(2), _kind(m.group(3))))
    return out


def _parse_lineup(side: str, text: str) -> list[tuple[str, str, str, str | None, bool]]:
    out = []
    for tok in re.split(r",\s+|\s+-\s+", " ".join(text.split())):
        m = _PLAYER.match(tok.strip())
        if not m:
            continue
        out.append((side, m["name"].strip(), "start", m["min"], bool(m["cap"])))      # titulaire (minute = sa sortie s'il est remplacé)
        if m["sub"]:
            out.append((side, m["sub"].strip(), "sub", m["min"], False))
    return out


def parse_full_txt(text: str, start_year: int) -> list[FullMatch]:
    """Un fichier `*-full.txt` -> les matchs. Les lignes non reconnues sont ignorées : le détail est un complément, jamais une raison d'échouer."""
    out: list[FullMatch] = []
    lines = text.splitlines()
    i, cur, side = 0, None, None
    while i < len(lines):
        line = lines[i]
        if m := _HEAD.match(line):
            mon = _MONTHS.get(m["mon"])
            year = start_year if mon and mon >= 7 else start_year + 1
            cur = FullMatch("", "", date(year, mon, int(m["day"])) if mon else None, (m["ground"] or "").strip() or None, int(m["att"]) if m["att"] else None)
            side = None
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if s := _SCORE.match(nxt):
                cur.home, cur.away = s["h"].strip(), s["a"].strip()
                cur.ft = (int(s["fh"]), int(s["fa"])) if s["fh"] else None
                out.append(cur)
                i += 1
            else:
                cur = None
        elif cur and line.startswith("     (") and not cur.goals:
            buf = line.strip()
            while not buf.endswith(")") and i + 1 < len(lines):
                i += 1
                buf += " " + lines[i].strip()
            cur.goals = _parse_goals(buf, cur.ft)
        elif cur and (t := re.match(r"^(?P<team>.+?): (?P<rest>.*)$", line)) and t["team"].strip() in (cur.home, cur.away) and not line.startswith(" "):
            side = "home" if t["team"].strip() == cur.home else "away"
            buf = t["rest"]
            while i + 1 < len(lines) and lines[i + 1].startswith("      "):
                i += 1
                buf += " " + lines[i].strip()
            cur.lineups += _parse_lineup(side, buf)
        elif cur and side and (c := re.match(r"^\s+(Yellow|Red):\s+(.*)$", line)):
            for tok in c[2].split(","):
                if g := _GOAL.match(tok.strip()):
                    cur.cards.append((side, g.group(1), g.group(2), c[1].lower()))
        elif cur and line.startswith("Refs:"):
            cur.referee = line[5:].split(",")[0].strip() or None
        i += 1
    return out


def import_full(con: duckdb.DuckDBPyConnection, client: OpenFootballClient, *, fresh_from: int | None = None,
                log_fn: Callable[[str], None] = print) -> int:
    """Complète les matchs déjà importés (affluence, arbitre, buteurs, compositions, cartons) ; rattache chaque match par la paire de clubs.
    À lancer APRÈS `import_leagues` : celui-ci recrée les matchs (et efface leur détail) à chaque passage."""
    last = current_start_year()
    fresh_from = fresh_from if fresh_from is not None else last - 1
    total = 0
    for code, (repo, pattern) in FULL_FILES.items():
        for year in range(FIRST_FULL_YEAR, last + 1):
            path = pattern.format(y=year, yy=str(year + 1)[2:])
            text = client.get(f"{RAW}/{repo}/master/{path}", fresh=year >= fresh_from)
            if text is None:
                continue
            label = season_label(year)
            index = _club_index(con, code, label)
            done = missing = 0
            con.execute("BEGIN")
            try:
                for fm in parse_full_txt(text, year):
                    hid, aid = resolve_club(index, fm.home), resolve_club(index, fm.away)
                    row = con.execute("SELECT id FROM match WHERE competition_code = ? AND season_label = ? AND home_club_id = ? AND away_club_id = ?",
                                      [code, label, hid, aid]).fetchone() if hid and aid else None
                    if row is None:
                        missing += 1
                        continue
                    mid = row[0]
                    con.execute("UPDATE match SET attendance = ?, referee = ?, ground = coalesce(ground, ?) WHERE id = ?", [fm.attendance, fm.referee, fm.ground, mid])
                    for child in ("match_goal", "match_lineup", "match_card"):
                        con.execute(f"DELETE FROM {child} WHERE match_id = ?", [mid])
                    for seq, g in enumerate(fm.goals, 1):
                        con.execute("INSERT INTO match_goal (match_id, seq, side, player_name, minute, kind) VALUES (?,?,?,?,?,?)", [mid, seq, g.side, g.player, g.minute, g.kind])
                    for seq, (sd, name, role, minute, cap) in enumerate(fm.lineups, 1):
                        con.execute("INSERT INTO match_lineup (match_id, side, seq, player_name, role, minute, captain) VALUES (?,?,?,?,?,?,?)", [mid, sd, seq, name, role, minute, cap])
                    for seq, (sd, name, minute, kind) in enumerate(fm.cards, 1):
                        con.execute("INSERT INTO match_card (match_id, seq, side, player_name, minute, kind) VALUES (?,?,?,?,?,?)", [mid, seq, sd, name, minute, kind])
                    done += 1
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
            total += done
            log_fn(f"  {code} {label} : détail de {done} matchs" + (f" ({missing} non rattachés)" if missing else ""))
    return total


# --------------------------------------------------------------------------------------------------
# Autres dépôts au format Football.TXT : deux « dialectes » de lignes de match.
#   1. « HH:MM  Équipe (PAY) v Équipe (PAY)  2-1 (1-0) » regroupés par date sous « ▪ Tour » : club-worldcup, south-america (Libertadores, Sudamericana), world.
#   2. « Équipe  0-2 Équipe  @ Stade » avec la liste des buteurs sur la ligne suivante : internationals (sélections, depuis 1872).

_TXT_DATE = re.compile(r"^\s*\w{3} (?P<mon>\w{3}) (?P<day>\d{1,2})(?: (?P<year>\d{4}))?\s*$")
_TIMED = re.compile(r"^\s+(?:(?P<t>\d{2}:\d{2})\s+)?(?P<h>\S.*?)\s+v\s+(?P<a>\S.*?)(?:\s{2,}(?P<s>\d+-\d+.*))?\s*$")
_INTL = re.compile(r"^\s{2}(?P<h>\S.*?)\s{2,}(?P<s>\d+-\d+(?: pen\. \d+-\d+)?(?: a\.e\.t\.)?(?: \([^)]*\))?)\s+(?P<a>\S.*?)(?:\s+@\s+(?P<g>.*?))?\s*$")
_PAIR = re.compile(r"(\d+)-(\d+)")


# Championnats du dépôt `world` qui existent chez nous : clé de fichier -> notre code. Les autres restent « OF:<clé> ».
WORLD_TO_OURS: dict[str, str] = {
    "au1": "AUS-L1", "cafcl": "CAF-CL", "cn1": "CHN-L1", "dz1": "DZA-L1", "eg1": "EGY-L1", "gh1": "GHA-L1", "il1": "ISR-L1", "jp1": "JPN-L1",
    "kz1": "KAZ-L1", "ma1": "MAR-L1", "mls": "USA-MLS", "mx1": "MEX-L1", "sa1": "SAU-PL", "sn1": "SEN-L1", "za1": "ZAF-L1", "ng1": "NGA-L1",
    "zw1": "ZWE-L1", "tz1": "TZA-L1", "ug1": "UGA-L1", "zm1": "ZMB-L1",
}


def _tail(s: str | None) -> tuple[tuple | None, tuple | None, tuple | None, tuple | None]:
    """`2-1 (1-0)` | `3-5 pen. 1-1 a.e.t. (1-1, 0-0)` | `2-1 a.e.t. (1-1, 0-0)` -> (temps réglementaire, mi-temps, prolongation, tirs au but)."""
    if not s:
        return None, None, None, None
    pairs = lambda t: [(int(a), int(b)) for a, b in _PAIR.findall(t)]
    pen = None
    if " pen." in s:
        head, s = s.split(" pen.", 1)
        pen = (pairs(head) or [None])[0]
    main, _, paren = s.partition("(")
    mp, pp = pairs(main), pairs(paren)
    if not mp and len(pp) > 1:                         # « 2-4 pen. (1-1, 0-1) » : tirs au but, puis (temps réglementaire, mi-temps)
        return pp[0], pp[1], None, pen
    if "a.e.t." in main:
        return (pp[0] if pp else None), (pp[1] if len(pp) > 1 else None), (mp[0] if mp else None), pen
    return (mp[0] if mp else None), (pp[0] if pp else None), None, pen


def _strip_country(name: str) -> str:
    return re.sub(r"\s+\([A-Z]{2,4}\)$", "", name.strip())


def _calendar(hint_year: int, split: bool = False):
    """Date d'une ligne « Sat Feb 4 » : l'année explicite quand il y en a une. Sinon, pour une saison « 2024/25 » (`split`), juillet-décembre = 2024 et
    janvier-juin = 2025 ; pour une année civile, celle de la date précédente, +1 si le mois chute d'au moins 6 (les journées ne sont pas toujours listées dans l'ordre)."""
    state = {"year": hint_year, "month": 0}

    def to_date(m: re.Match) -> date | None:
        mon = _MONTHS.get(m["mon"])
        if not mon:
            return None
        if m["year"]:
            state["year"] = int(m["year"])
        elif split:
            state["year"] = hint_year if mon >= 7 else hint_year + 1
        elif state["month"] - mon >= 6:
            state["year"] += 1
        state["month"] = mon
        try:
            return date(state["year"], mon, int(m["day"]))
        except ValueError:
            return None
    return to_date


def parse_txt_timed(text: str, hint_year: int, ref: str, split: bool = False) -> list[Match]:
    """Dialecte 1. Une ligne sans heure (continuation) reprend l'heure de la précédente."""
    out: list[Match] = []
    to_date = _calendar(hint_year, split)
    rnd, day, kick = None, None, None
    for line in text.splitlines():
        if line.startswith("▪"):
            rnd = line[1:].strip() or None
        elif m := _TXT_DATE.match(line):
            day = to_date(m)
        elif day and (m := _TIMED.match(line)) and not line.lstrip().startswith("#"):
            kick = m["t"] or kick
            ft, ht, et, pen = _tail(m["s"])
            out.append(Match(_strip_country(m["h"]), _strip_country(m["a"]), round=rnd, day=day, kickoff=kick, ft=ft, ht=ht, et=et, pen=pen, source_ref=ref))
    return out


_INTL_GOAL = re.compile(rf"(?P<name>[^\d;()]+?)\s+(?P<mins>{_MIN}'(?:\((?:og|p|pen)\))?(?:,\s*{_MIN}'(?:\((?:og|p|pen)\))?)*)")


def _intl_goals(text: str, ft) -> list[Goal]:
    text = text.strip()
    parts = [p.strip() for p in (text[1:-1] if text.startswith("(") and text.endswith(")") else text).split(";")]
    sides = ["home", "away"] if len(parts) == 2 else ["away" if ft and ft[0] == 0 else "home"]
    out = []
    for side, part in zip(sides, parts):
        for g in _INTL_GOAL.finditer(part):
            for mm in re.finditer(rf"({_MIN})'(?:\((og|p|pen)\))?", g["mins"]):
                out.append(Goal(side, g["name"].strip(), mm.group(1), _kind(mm.group(2))))
    return out


def parse_txt_intl(text: str, hint_year: int, ref: str, split: bool = False) -> list[Match]:
    """Dialecte 2 (internationals) : date seule sur sa ligne, puis « Équipe  score Équipe  @ stade » et les buteurs entre parenthèses."""
    out: list[Match] = []
    to_date = _calendar(hint_year, split)
    rnd, group, day = None, None, None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("▪"):
            rnd = line[1:].strip() or None
            group = rnd if rnd and rnd.lower().startswith("group") else None
        elif m := _TXT_DATE.match(line):
            day = to_date(m)
        elif (m := _INTL.match(line)) and not line.lstrip().startswith("#"):
            ft, ht, et, pen = _tail(m["s"])
            goals: list[Goal] = []
            if i + 1 < len(lines) and lines[i + 1].startswith("     ("):
                buf = lines[i + 1].strip()
                while not buf.endswith(")") and i + 2 < len(lines):
                    i += 1
                    buf += " " + lines[i + 1].strip()
                i += 1
                goals = _intl_goals(buf, ft)
            out.append(Match(m["h"].strip(), m["a"].strip(), round=rnd, group=group, day=day, ft=ft, ht=ht, et=et, pen=pen,
                             ground=m["g"], goals=goals, source_ref=ref))
        i += 1
    return out


def _tree(client: OpenFootballClient, repo: str) -> list[str]:
    """Chemins des fichiers d'un dépôt (un seul appel à l'API GitHub, relu à chaque passage pour voir les nouvelles saisons)."""
    text = client.get(f"https://api.github.com/repos/openfootball/{repo}/git/trees/master?recursive=1", fresh=True)
    return [t["path"] for t in json.loads(text or "{}").get("tree", []) if t.get("type") == "blob"]


def _txt_target(repo: str, path: str) -> tuple[str, str, int, Callable] | None:
    """Fichier -> (code, saison, année de départ, lecteur) ; None si le fichier n'est pas un résultat à importer."""
    name = path.rsplit("/", 1)[-1]
    if repo == "club-worldcup" and (m := re.fullmatch(r"(\d{4})/clubworldcup\.txt", path)):
        return "FIFA-CWC", m[1], int(m[1]), parse_txt_timed
    if repo == "south-america" and (m := re.fullmatch(r"copa-libertadores/(\d{4})_(copal|copas)\.txt", path)):
        return ("CONMEBOL-CL" if m[2] == "copal" else "OF:copa-sudamericana"), m[1], int(m[1]), parse_txt_timed
    if repo == "world" and (m := re.fullmatch(r"(\d{4})(?:-(\d{2}))?_([\w.-]+)\.txt", name)) and path.count("/") >= 1 and "attic" not in path:
        return WORLD_TO_OURS.get(m[3], f"OF:{m[3]}"), (f"{m[1]}/{m[2]}" if m[2] else m[1]), int(m[1]), parse_txt_timed
    if repo == "internationals" and (m := re.fullmatch(r"([a-z_]+)/(\d{4})(?:-(\d{2}))?_[\w.-]+\.txt", path)) and m[1] not in ("fifa_world_cup", "uefa_euro", "more"):
        return f"OF:{m[1]}", (f"{m[2]}/{m[3]}" if m[3] else m[2]), int(m[2]), parse_txt_intl
    return None


def import_txt_repos(con: duckdb.DuckDBPyConnection, client: OpenFootballClient, *, repos: list[str] | None = None, fresh_from: int | None = None,
                     already: set[str] = frozenset(), log_fn: Callable[[str], None] = print) -> dict[str, WriteReport]:
    """Coupe du monde des clubs, Copa Libertadores et Sudamericana, championnats de `world`, matchs de sélections de `internationals`."""
    fresh_from = fresh_from if fresh_from is not None else date.today().year - 1
    done: dict[str, WriteReport] = {}
    for repo in repos or ["club-worldcup", "south-america", "world", "internationals"]:
        n = 0
        for path in _tree(client, repo):
            target = _txt_target(repo, path)
            if not target:
                continue
            code, label, year, reader = target
            if f"{code} {label}" in already:               # déjà lu dans une source plus complète pour cette saison (football.json) : on ne l'écrase pas
                continue
            text = client.get(f"{RAW}/{repo}/master/{path}", fresh=year >= fresh_from)
            matches = reader(text, year, f"{repo}/{path}", "/" in label) if text else []
            if matches:
                done[f"{code} {label}"] = write_matches(con, code, label, matches)
                set_competition_name(con, code, next((l for l in text.splitlines() if l.startswith("=")), None))
                n += len(matches)
        log_fn(f"  {repo} : {n} matchs")
    return done


def purge_unseen(con: duckdb.DuckDBPyConnection, seen: set[str]) -> int:
    """Après un import complet : retire les matchs `OF:*` dont la compétition n'a plus de fichier (une compétition devenue « nôtre », ex. `OF:clubworldcup` -> `FIFA-CWC`)."""
    stale = [c for (c,) in con.execute("SELECT DISTINCT competition_code FROM match WHERE competition_code LIKE 'OF:%'").fetchall() if c not in seen]
    for code in stale:
        for child in ("match_goal", "match_lineup", "match_card", "match_result_source"):
            con.execute(f"DELETE FROM {child} WHERE match_id IN (SELECT id FROM match WHERE competition_code = ?)", [code])
        con.execute("DELETE FROM match WHERE competition_code = ?", [code])
        con.execute("DELETE FROM match_competition WHERE code = ?", [code])
    return len(stale)


# --------------------------------------------------------------------------------------------------
# Rattachement des noms de joueurs (buteurs, compositions, cartons) à l'effectif du club : seulement quand un seul joueur convient.

def _tokens(name: str) -> frozenset[str]:
    from openfootball.names import fold            # import local : names n'a pas besoin d'être chargé pour lire un fichier
    return frozenset(re.sub(r"[^a-z0-9]+", " ", fold(name)).split())


def pick_player(squad: list[tuple[int, frozenset[str]]], name: str) -> int | None:
    """Mêmes mots (la casse et les accents ne comptent pas) ; sinon les mots de l'un contenus dans ceux de l'autre (« Smith Rowe » / « Emile Smith Rowe »,
    « Alisson » / « Alisson Becker »). Un seul joueur doit répondre à un niveau, sinon aucun lien."""
    toks = _tokens(name)
    if not toks:
        return None
    for level in (lambda p: p == toks, lambda p: toks <= p or (p <= toks and bool(p))):
        found = {pid for pid, p in squad if level(p)}
        if len(found) == 1:
            return found.pop()
        if found:
            return None
    return None


def link_match_players(con: duckdb.DuckDBPyConnection, log_fn: Callable[[str], None] = print) -> dict[str, int]:
    """Renseigne `player_id` sur `match_goal`, `match_lineup` et `match_card` : le joueur de l'effectif du club (cette saison) qui porte ce nom.
    Un but contre son camp est compté dans l'effectif de l'équipe adverse (celle qui en profite). Idempotent : ne touche que les lignes sans lien."""
    squads: dict[tuple[int, str], list[tuple[int, frozenset[str]]]] = {}

    def squad(club_id: int, label: str):
        key = (club_id, label)
        if key not in squads:
            squads[key] = [(pid, _tokens(name)) for pid, name in con.execute(
                """SELECT p.id, p.name FROM player_club_season pcs JOIN club_season cs ON cs.id = pcs.club_season_id JOIN season s ON s.id = cs.season_id
                   JOIN player p ON p.id = pcs.player_id WHERE cs.club_id = ? AND s.label = ?""", key).fetchall()]
        return squads[key]

    linked = {}
    for table, own_goal in (("match_goal", "t.kind = 'own_goal'"), ("match_lineup", "FALSE"), ("match_card", "FALSE")):
        rows = con.execute(f"""SELECT t.rowid, t.player_name, m.season_label,
                   CASE WHEN (t.side = 'home') <> ({own_goal}) THEN m.home_club_id ELSE m.away_club_id END
            FROM {table} t JOIN match m ON m.id = t.match_id WHERE t.player_id IS NULL""").fetchall()
        updates = [(pid, rid) for rid, name, label, club in rows if club and (pid := pick_player(squad(club, label), name))]
        if updates:
            con.executemany(f"UPDATE {table} SET player_id = ? WHERE rowid = ?", updates)
        linked[table] = len(updates)
        log_fn(f"  {table} : {len(updates)} / {len(rows)} noms rattachés à un joueur de l'effectif")
    return linked


# --------------------------------------------------------------------------------------------------
# Classement calculé (sert à l'audit et à la page « Classement »)

STANDINGS_SQL = """
WITH side AS (
  SELECT competition_code, season_label, home_club_id club_id, home_name team, ft_home gf, ft_away ga FROM match WHERE ft_home IS NOT NULL
  UNION ALL
  SELECT competition_code, season_label, away_club_id, away_name, ft_away, ft_home FROM match WHERE ft_home IS NOT NULL)
SELECT competition_code, season_label, club_id, team, count(*) played,
       count(*) FILTER (WHERE gf > ga) won, count(*) FILTER (WHERE gf = ga) drawn, count(*) FILTER (WHERE gf < ga) lost,
       sum(gf) gf, sum(ga) ga, sum(gf) - sum(ga) gd, 3 * count(*) FILTER (WHERE gf > ga) + count(*) FILTER (WHERE gf = ga) points
FROM side GROUP BY competition_code, season_label, club_id, team"""
