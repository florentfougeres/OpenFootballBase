-- 0025 : provenance du score d'un match, à part (modifier `match` est impossible : elle porte un index, et DuckDB plante sur ALTER + index dans la transaction d'une migration).
-- Une ligne = un score lu AILLEURS que dans la source de matchs OpenFootball ; pas de ligne = OpenFootball. `wikipedia` : matrice de résultats de la page Wikipedia de la saison
-- (saison en cours : plus à jour que OpenFootball, dont les mises à jour automatiques peuvent s'arrêter).
CREATE TABLE match_result_source (
  match_id INTEGER PRIMARY KEY,
  source   VARCHAR NOT NULL
);
