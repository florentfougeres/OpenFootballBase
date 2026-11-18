-- 0022 : matchs. Source : les données ouvertes du projet OpenFootball (github.com/openfootball, licence CC0), PAS Wikipedia/Wikidata.
-- Un match = une ligne ; la table est remplacée par compétition-saison à chaque import (`openfootball matches`).
-- `competition_code` : notre code (ENG-PL…) quand la compétition existe dans `competition`, sinon `OF:<clé du fichier>` (ex. OF:en.3).
-- `home_club_id` / `away_club_id` : club de `club` reconnu par son nom (NULL si aucun club de la compétition ne porte ce nom) ; les noms écrits par la source sont toujours gardés.
-- Scores : ft = temps réglementaire, ht = mi-temps, et = après prolongation (cumul), pen = tirs au but. Aucun score = match non joué (calendrier).
CREATE TABLE match (
  id               INTEGER PRIMARY KEY,
  competition_code VARCHAR NOT NULL,
  season_label     VARCHAR NOT NULL,            -- « 2025/26 » (ou « 2022 » pour un tournoi sur une année civile)
  round            VARCHAR,                     -- « Matchday 1 », « Round of 16 »…
  group_name       VARCHAR,
  match_date       DATE,
  kickoff          VARCHAR,                     -- « 20:00 », heure locale écrite par la source
  home_name        VARCHAR NOT NULL,
  away_name        VARCHAR NOT NULL,
  home_club_id     INTEGER,
  away_club_id     INTEGER,
  ft_home INTEGER, ft_away INTEGER,
  ht_home INTEGER, ht_away INTEGER,
  et_home INTEGER, et_away INTEGER,
  pen_home INTEGER, pen_away INTEGER,
  ground           VARCHAR,
  attendance       INTEGER,
  referee          VARCHAR,
  source_ref       VARCHAR NOT NULL             -- fichier d'origine, pour retrouver la ligne
);
CREATE INDEX match_comp_season ON match (competition_code, season_label);

-- Buteurs d'un match (quand la source les donne) : `side` = équipe qui marque (pour un csc, l'équipe qui en profite).
CREATE TABLE match_goal (
  match_id    INTEGER NOT NULL,
  seq         INTEGER NOT NULL,
  side        VARCHAR NOT NULL,                 -- home | away
  player_name VARCHAR NOT NULL,
  minute      VARCHAR,                          -- « 37 », « 90+4 »
  kind        VARCHAR NOT NULL DEFAULT 'goal',  -- goal | penalty | own_goal
  PRIMARY KEY (match_id, seq)
);
