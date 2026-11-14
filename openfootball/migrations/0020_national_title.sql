-- 0020 : titres en équipe nationale. Pour chaque édition d'une compétition de sélections (Coupe du monde, Euro, Copa América…), la liste des joueurs
-- de l'équipe VAINQUEUR, lue sur la page Wikipedia « <édition> squads » (la liste de la compétition, pas les matchs joués).
-- `player_qid` relie le joueur à `player_wikidata` quand sa page a un élément Wikidata.
CREATE TABLE national_title (
  competition   VARCHAR NOT NULL,         -- WORLD_CUP, EURO, COPA_AMERICA, AFCON, ASIAN_CUP, GOLD_CUP, CONFEDERATIONS_CUP
  year          INTEGER NOT NULL,         -- année de l'édition
  team          VARCHAR NOT NULL,         -- sélection victorieuse (nom anglais : « France »)
  player_name   VARCHAR NOT NULL,
  player_link   VARCHAR,
  player_qid    VARCHAR,
  shirt_number  INTEGER,
  position      VARCHAR,
  source_title  VARCHAR NOT NULL,         -- page Wikipedia des effectifs lue
  PRIMARY KEY (competition, year, player_name)
);
