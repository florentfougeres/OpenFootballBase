-- 0024 : liens des matchs avec le reste de la base.
-- `player_id` : joueur de notre base à qui appartient le nom écrit par la source, quand l'effectif du club cette saison-là le désigne SANS ambiguïté
-- (sinon NULL : un nom sans identifiant ne vaut pas un lien). Publié sous forme de `player_qid`.
ALTER TABLE match_goal ADD COLUMN player_id INTEGER;
ALTER TABLE match_lineup ADD COLUMN player_id INTEGER;
ALTER TABLE match_card ADD COLUMN player_id INTEGER;

-- Nom (anglais) des compétitions `OF:*` : lu dans l'en-tête « = Algeria | Ligue 1 2024/25 » du fichier source, sans l'année.
CREATE TABLE match_competition (
  code VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL
);
