-- 0026 : taille et lieu de naissance venus du dépôt `players` d'OpenFootball (CC0), seulement là où Wikipedia (`player_profile`) n'en a pas.
-- Un joueur n'est relié que par SON NOM ET SA DATE DE NAISSANCE EXACTE (jamais le nom seul : les homonymes sont nombreux). Table à part : provenance claire, et le profil Wikipedia reste intact.
CREATE TABLE player_openfootball (
  player_id   INTEGER PRIMARY KEY,
  height_cm   INTEGER,            -- NULL si Wikipedia en a déjà une
  birth_place VARCHAR             -- NULL si Wikipedia en a déjà un
);
