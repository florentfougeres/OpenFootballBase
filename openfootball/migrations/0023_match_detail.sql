-- 0023 : détail d'un match (fichiers « *-full.txt » d'OpenFootball, 6 championnats, saison 2025/26 et suivantes) : compositions, remplacements, cartons.
-- Les buteurs vont dans `match_goal` (0022) ; l'affluence, l'arbitre et le stade complètent la ligne de `match`.
CREATE TABLE match_lineup (
  match_id    INTEGER NOT NULL,
  side        VARCHAR NOT NULL,                 -- home | away
  seq         INTEGER NOT NULL,                 -- ordre d'écriture de la source (gardien en premier, remplaçants à la suite)
  player_name VARCHAR NOT NULL,                 -- tel qu'écrit par la source (la casse varie)
  role        VARCHAR NOT NULL,                 -- start | sub (entré en cours de match)
  minute      VARCHAR,                          -- minute d'entrée d'un remplaçant ; pour un titulaire remplacé, minute de sa sortie
  captain     BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (match_id, side, seq)
);

CREATE TABLE match_card (
  match_id    INTEGER NOT NULL,
  seq         INTEGER NOT NULL,
  side        VARCHAR NOT NULL,
  player_name VARCHAR NOT NULL,
  minute      VARCHAR,
  kind        VARCHAR NOT NULL,                 -- yellow | red
  PRIMARY KEY (match_id, seq)
);
