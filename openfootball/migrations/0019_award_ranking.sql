-- 0019 : classements de récompenses individuelles (Ballon d'Or). Une ligne par joueur classé d'une édition (page Wikipedia « <année> Ballon d'Or »).
-- `player_qid` relie le joueur à `player_wikidata` quand la page du joueur a un élément Wikidata ; `club_id` relie son club à la base quand c'est possible.
CREATE TABLE award_ranking (
  award         VARCHAR NOT NULL,         -- BALLON_DOR
  year          INTEGER NOT NULL,         -- année de la cérémonie (édition)
  rank          INTEGER NOT NULL,
  player_name   VARCHAR NOT NULL,
  player_link   VARCHAR,                  -- titre de la page Wikipedia anglaise du joueur
  player_qid    VARCHAR,
  club_name     VARCHAR,
  club_link     VARCHAR,
  club_id       INTEGER,
  points        INTEGER,
  source_title  VARCHAR NOT NULL,         -- page Wikipedia lue
  PRIMARY KEY (award, year, rank, player_name)
);
