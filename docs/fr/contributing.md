# Contribuer

[English](../en/contributing.md)

Merci de votre aide. Ce dépôt est le **site** ; le pipeline de données a son propre [guide de contribution](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/contributing.md) dans le [dépôt des données](https://github.com/florentfougeres/OpenFootballBase-Data) (nouveaux pays, corrections d'analyseurs, corrections de données : c'est là-bas, ou à la source sur Wikipedia et Wikidata).

## Installer

Voir [getting-started.md](getting-started.md) : Node.js ≥ 22, puis `npm install`, `npm run data` et `npm run dev` dans `web/`.

## Façon de travailler

1. Ouvrez une issue pour tout ce qui dépasse une petite correction, afin de s'accorder sur l'approche.
2. Une branche, un changement ciblé.
3. Lancez `npm run check && npm run build` (dans `web/`).
4. Ouvrez une pull request qui décrit ce qui change et pourquoi. Le CI lance les mêmes vérifications.

## Principes à respecter

- **Pas de serveur, pas de suivi.** Le site reste statique : pas de mesure d'audience, pas de cookies, aucune requête tierce hormis le moteur DuckDB épinglé ([website.md](website.md)).
- **Ne jamais présenter une supposition comme un fait.** Un trou est affiché comme un trou.
- **Pas de secret, pas de donnée personnelle** dans le code, les journaux ou les messages de commit.
- **Le SQL est paramétré.** Ne construisez jamais du SQL à partir d'un texte externe.

## La documentation est bilingue — toujours

Toute modification de la documentation ou du README **se fait dans les deux langues** : français et anglais. Concrètement :

- `README.md` (anglais) et `README.fr.md` (français) se modifient ensemble.
- Chaque guide existe en `docs/en/<nom>.md` et `docs/fr/<nom>.md`, avec le même nom de fichier, la même structure et les mêmes liens ; chacun commence par un lien vers l'autre langue.
- Cela inclut le changelog (`docs/{fr,en}/changelog.md`).
- Les textes visibles du site vont dans les deux langues de `web/src/lib/i18n.ts`.
- Quand vous ajoutez une page, ajoutez-la aux deux index (`docs/en/README.md`, `docs/fr/README.md`).

## Conventions

- Messages de commit en anglais, à l'impératif, un changement logique par commit.
- Les changements du site vont dans le changelog, section « Site et outils » (dans les deux langues). Les releases de données s'appellent `Data X.Y.Z` et vivent dans le [dépôt des données](https://github.com/florentfougeres/OpenFootballBase-Data).
