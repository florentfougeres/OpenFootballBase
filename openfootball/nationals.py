"""Titres en équipe nationale : le vainqueur de chaque édition (infobox de la page du tournoi) et sa liste de joueurs (page « <édition> squads »).

Une compétition, ses années possibles et le titre des pages sont déclarés dans `COMPETITIONS`. Une édition sans page, sans vainqueur reconnu ou
sans liste lisible n'est pas écrite (rien n'est deviné). Un joueur est crédité du titre s'il figure dans la liste de l'équipe victorieuse : il a pu ne
pas jouer, comme pour les titres de clubs (approximation dite sur le site).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

import duckdb

from openfootball.countries import country_of_fifa
from openfootball.honours import _LINK, _PARAM
from openfootball.names import fold
from openfootball.parse.squad import _int, _name_and_link, _params, clean, iter_templates
from openfootball.sources.wikidata import club_qids


@dataclass(frozen=True)
class Competition:
    code: str
    pages: str                   # titre de la page du tournoi (« {y} FIFA World Cup »)
    squads: str                  # titre de la page des effectifs
    years: tuple[int, ...]


def _every(start: int, stop: int, step: int) -> tuple[int, ...]:
    return tuple(range(start, stop + 1, step))


COMPETITIONS = (
    Competition("WORLD_CUP", "{y} FIFA World Cup", "{y} FIFA World Cup squads", (1930, 1934, 1938) + _every(1950, 2022, 4)),
    Competition("EURO", "UEFA Euro {y}", "UEFA Euro {y} squads", _every(1960, 2024, 4)),
    Competition("COPA_AMERICA", "{y} Copa América", "{y} Copa América squads", _every(1916, 2024, 1)),
    Competition("AFCON", "{y} Africa Cup of Nations", "{y} Africa Cup of Nations squads", _every(1957, 2025, 1)),
    Competition("ASIAN_CUP", "{y} AFC Asian Cup", "{y} AFC Asian Cup squads", _every(1956, 2023, 1)),
    Competition("GOLD_CUP", "{y} CONCACAF Gold Cup", "{y} CONCACAF Gold Cup squads", _every(1991, 2025, 1)),
    Competition("CONFEDERATIONS_CUP", "{y} FIFA Confederations Cup", "{y} FIFA Confederations Cup squads", (1992, 1995, 1997, 1999, 2001, 2003, 2005, 2009, 2013, 2017)),
)
# Les pages d'effectifs utilisent plusieurs familles de modèles : « nat fs player », « nat fs g player », « nat fs player no caps »,
# « National football squad player », « National football squad player (goals) », « … (no caps) ». On repère tout modèle de cette famille.
_PLAYER_TEMPLATE = re.compile(r"^(?:nat(?:ional)? f(?:ootball )?s(?:quad)?\b)[^|{}]*\bplayer\b[^|{}]*$", re.I)
_TEMPLATE_NAME = re.compile(r"\{\{\s*([^|{}\n]+?)\s*\|")
# Noms d'une même équipe selon la page : l'infobox dit « FRG » ou « NED », la page des effectifs « West Germany » ou « Netherlands ».
_SAME = (("west germany", "frg", "germany fr"), ("germany", "ger"), ("czechoslovakia", "tch"), ("netherlands", "ned", "holland"), ("united states", "us", "usa"),
         ("soviet union", "urs", "ussr"), ("yugoslavia", "yug"), ("serbia and montenegro", "scg"), ("egypt", "united arab republic", "uar", "egy"),
         ("dr congo", "democratic republic of the congo", "zaire", "cod", "zai"), ("ivory coast", "cote d'ivoire", "civ"), ("east germany", "gdr", "ddr"),
         ("iran", "persia", "irn"), ("south korea", "korea republic", "kor"), ("china", "china pr"), ("england", "eng"))
_HEADING = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$", re.M)
_NATION_WORDS = re.compile(r"\s*national (?:football |soccer )?team\s*$", re.I)


def champion(wikitext: str) -> str | None:
    """Nom de l'équipe victorieuse d'après l'infobox : lien (« [[France national football team|France]] »), code FIFA (« FRA », « {{fb|FRA}} ») ou texte."""
    head = wikitext[:6000]
    for m in _PARAM.finditer(head):
        raw = m.group(1).split("|champion")[0]
        code = re.search(r"\{\{\s*(?:fb|fbaicon|flagicon|flag)\s*\|\s*([A-Z]{3})\b", raw, re.I) or re.fullmatch(r"\s*([A-Z]{3})\s*(?:\|.*)?", raw)
        if code:
            name = country_of_fifa(code.group(1).upper())[1]
            if name:
                return name
        link = _LINK.search(raw)
        if link:
            return _NATION_WORDS.sub("", (link.group(2) or link.group(1))).strip()
        text = re.sub(r"\{\{[^{}]*\}\}|<[^>]+>|\[\[|\]\]|'{2,}", "", raw).strip()
        if text:
            return _NATION_WORDS.sub("", text).strip()
    return None


def team_section(wikitext: str, team: str) -> str:
    """Texte de la section de `team` dans la page des effectifs (du titre jusqu'au titre suivant de même niveau ou plus haut)."""
    group = next((g for g in _SAME if fold(team) in g), (fold(team),))
    heads = [(m.start(), m.end(), len(m.group(1)), fold(re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", m.group(2)))) for m in _HEADING.finditer(wikitext)]
    for i, (_s, end, level, name) in enumerate(heads):
        if name in group:
            nxt = next((h[0] for h in heads[i + 1:] if h[2] <= level), len(wikitext))
            return wikitext[end:nxt]
    return ""


def players(section: str) -> list[dict]:
    out: list[dict] = []
    names = tuple(dict.fromkeys(n for n in _TEMPLATE_NAME.findall(section) if _PLAYER_TEMPLATE.match(n)))
    for _, body in iter_templates(section, names) if names else ():
        p = _params(body)
        name, link = _name_and_link(p.get("name", ""), full=True)
        if name:
            out.append({"name": name, "link": link, "no": _int(p.get("no")), "pos": (p.get("pos") or "").strip() or None})
    return out


def import_national_titles(con: duckdb.DuckDBPyConnection, wp, *, log: Callable[[str], None] = print) -> int:
    """Remplace `national_title` : pour chaque édition connue, la liste de l'équipe victorieuse."""
    wanted = [(c, y) for c in COMPETITIONS for y in c.years]
    pages: dict[str, object] = {}
    for i in range(0, len(wanted), 40):
        chunk = wanted[i:i + 40]
        for p in wp.get_pages([c.pages.format(y=y) for c, y in chunk] + [c.squads.format(y=y) for c, y in chunk]):
            pages[p.title] = p
    rows: list[tuple] = []
    for c, y in wanted:
        main, sq = pages.get(c.pages.format(y=y)), pages.get(c.squads.format(y=y))
        if not (main and main.exists and sq and sq.exists and main.wikitext and sq.wikitext):
            continue
        team = champion(clean(main.wikitext))
        if not team:
            log(f"  {c.code} {y} : vainqueur illisible")
            continue
        got = players(team_section(clean(sq.wikitext), team))
        if len(got) < 11:
            log(f"  {c.code} {y} : {team} : liste illisible ({len(got)} joueurs)")
            continue
        rows += [(c.code, y, team, g, sq.resolved_title or sq.title) for g in got]
    links = sorted({g["link"] for _, _, _, g, _ in rows if g["link"]})
    qids = club_qids(wp, links) if links else {}
    con.execute("BEGIN")
    try:
        con.execute("DELETE FROM national_title")
        for code, y, team, g, src in rows:
            con.execute("INSERT INTO national_title VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                        [code, y, team, g["name"], g["link"], qids.get(g["link"]) if g["link"] else None, g["no"], g["pos"], src])
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    log(f"  titres en sélection : {len(rows)} joueurs, {len({(r[0], r[1]) for r in rows})} éditions")
    return len(rows)
