-- 0021 : entraîneurs. Un mandat = un entraîneur à la tête d'un club entre deux dates (propriété Wikidata P286 « entraîneur », avec début P580 et fin P582).
-- `end_date` vide : mandat en cours (ou fin non renseignée). Les mandats sans date de début ne sont pas gardés : on ne saurait pas les placer.
CREATE TABLE club_coach (
  club_id     INTEGER NOT NULL REFERENCES club(id),
  coach_qid   VARCHAR NOT NULL,
  coach_name  VARCHAR NOT NULL,         -- libellé anglais Wikidata (un nom de personne, le même dans les deux langues du site)
  start_date  DATE NOT NULL,
  end_date    DATE,
  PRIMARY KEY (club_id, coach_qid, start_date)
);
