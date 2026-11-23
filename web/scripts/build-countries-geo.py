#!/usr/bin/env python3
"""Fond de carte des pays : simplifie datasets/geo-countries (Natural Earth, domaine public) en un fichier léger, `public/geo/countries.json`.
Usage : python scripts/build-countries-geo.py countries.geojson   (nécessite `shapely`)
Chaque entité porte `c` (code pays de la base, ex. FRA) et `cx`/`cy` (un point à l'intérieur du plus grand polygone, pour le cercle de comptage).
Le Royaume-Uni n'a qu'un polygone : il porte `c = "GBR"` et la carte propose les quatre nations."""
import json, sys
from shapely.geometry import shape, mapping

TOL = 0.04                     # degrés (≈ 4 km) : la carte zoome jusqu'à l'échelle d'une région, pas d'une ville
MIN_AREA = 0.05                # carrés de degré : on garde les îlots d'un pays minuscule seulement s'il n'a rien d'autre
FIX = {"-99": None}            # entités sans code ISO : seul le Kosovo nous intéresse (XKS)

src = json.load(open(sys.argv[1]))
out = []
for f in src["features"]:
    p = f["properties"]; code = p["ISO3166-1-Alpha-3"]
    if code == "-99":
        if p["name"] != "Kosovo": continue
        code = "XKS"
    g = shape(f["geometry"])
    parts = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    big = max(parts, key=lambda x: x.area)
    keep = [x for x in parts if x.area >= MIN_AREA] or [big]
    s = type(g)(keep) if len(keep) > 1 else keep[0]
    s = s.simplify(TOL, preserve_topology=True)
    if s.is_empty: continue
    pt = big.representative_point()
    geom = json.loads(json.dumps(mapping(s)))
    def rnd(c): return [round(c[0], 2), round(c[1], 2)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]
    geom["coordinates"] = rnd(geom["coordinates"])
    out.append({"type": "Feature", "properties": {"c": code, "n": p["name"], "cx": round(pt.x, 2), "cy": round(pt.y, 2)}, "geometry": geom})
json.dump({"type": "FeatureCollection", "features": out}, open("public/geo/countries.json", "w"), separators=(",", ":"))
print(len(out), "entités")
