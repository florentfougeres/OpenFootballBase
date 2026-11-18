<p align="center"><img src="docs/images/logo.svg" alt="OpenFootballBase" width="88"></p>

<h1 align="center">OpenFootballBase</h1>

<p align="center">
  <strong>Le site d'OpenFootballBase : une base ouverte des effectifs de clubs de football, saison par saison, construite à partir de Wikipedia et de Wikidata.</strong><br>
  Ce dépôt est l'<b>application</b>. Les données et le pipeline qui les construit sont dans <a href="https://github.com/florentfougeres/OpenFootballBase-Data">OpenFootballBase-Data</a>.
</p>

<p align="center">
  <a href="https://florentfougeres.github.io/OpenFootballBase/">Site</a> ·
  <a href="https://github.com/florentfougeres/OpenFootballBase-Data/releases/latest">Télécharger les données</a> ·
  <a href="https://github.com/florentfougeres/OpenFootballBase-Data">Dépôt des données</a> ·
  <a href="docs/README.md">Documentation</a> ·
  <a href="README.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/florentfougeres/OpenFootballBase/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/florentfougeres/OpenFootballBase/actions/workflows/ci.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="Code : MIT" src="https://img.shields.io/badge/code-MIT-blue.svg"></a>
  <img alt="Données : CC BY-SA 4.0" src="https://img.shields.io/badge/donn%C3%A9es-CC%20BY--SA%204.0-lightgrey.svg">
</p>

---

## Ce qu'est ce dépôt

Un site statique [Svelte](https://svelte.dev) 5 + Vite + Tailwind, bilingue (français / anglais) : tableaux de bord de championnats, pages de clubs avec effectif et mouvements entre saisons, pages de joueurs avec frise de carrière, compétitions avec résultats et classements, une carte de couverture, une recherche de joueurs avec filtres et export CSV. [DuckDB-WASM](https://duckdb.org/docs/api/wasm/overview) lit les fichiers Parquet par requêtes HTTP à plages : pas de serveur, pas de mesure d'audience, pas de cookies. Le moteur DuckDB est servi par le site lui-même, et une Content-Security-Policy limite ce que la page peut charger.

Le site affiche **les données de la dernière release d'[OpenFootballBase-Data](https://github.com/florentfougeres/OpenFootballBase-Data)** : les données ne sont pas stockées ici.

## Développer le site

Prérequis : **Node.js ≥ 22**, **git** et la commande `gh` (pour télécharger les données).

```bash
git clone https://github.com/florentfougeres/OpenFootballBase.git && cd OpenFootballBase/web
npm install
npm run data        # télécharge la dernière release de données dans web/public/data (npm run data -- data-1.21.0 pour une précise)
npm run dev         # http://localhost:5173
npm run check       # vérification des types (svelte-check), aussi lancée par le CI
```

## Comment le site est déployé

Publier une release dans le dépôt des données lance le déploiement toute seule (`notify-site.yml` là-bas lance [`deploy.yml`](.github/workflows/deploy.yml) ici, avec le tag de la release). Un push de `web/**` sur `main` redéploie avec la dernière release. Le jeton qui autorise la première étape, ses droits et son expiration sont décrits dans le [guide du dépôt des données](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/publishing-a-release.md).

Pour redéployer à la main :

```bash
gh workflow run deploy.yml --repo florentfougeres/OpenFootballBase --ref main -f tag=data-X.Y.Z   # sans le tag : la dernière release
```

## Documentation

La documentation est disponible en français et en anglais ([index](docs/fr/README.md)) ; chaque page existe dans les deux langues. Le dictionnaire de données, les commandes, la mise à jour hebdomadaire, les releases, le journal de conception et la feuille de route sont dans le [dépôt des données](https://github.com/florentfougeres/OpenFootballBase-Data/tree/main/docs/fr).

| Page | Contenu |
|---|---|
| [getting-started.md](docs/fr/getting-started.md) | Par où commencer |
| [website.md](docs/fr/website.md) | Plan du code, chargement des données, en-têtes de sécurité |
| [architecture.md](docs/fr/architecture.md) | Comment les deux dépôts s'articulent |
| [security.md](docs/fr/security.md) | Signalement, protections en place |
| [changelog.md](docs/fr/changelog.md) | Changements du site et des outils (releases de données : [changelog des données](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/changelog.md)) |
| [migration-two-repos.md](docs/fr/migration-two-repos.md) | La séparation entre ce dépôt et le dépôt des données |

## Sources, licences et limites

- **Sources des données** : [Wikipedia](https://www.wikipedia.org) (texte sous CC BY-SA 4.0 ; chaque effectif cite sa page et sa révision), [Wikidata](https://www.wikidata.org) (CC0) et les données ouvertes d'[OpenFootball](https://github.com/openfootball) (CC0, résultats de matchs).
- **Code** : [MIT](LICENSE). **Données** : dérivées de Wikipedia, donc partagées sous **CC BY-SA 4.0** avec attribution aux contributeurs de Wikipedia.
- **Les logos de clubs** sont des images Wikimedia, souvent non libres, affichées à titre d'illustration ; ils ne font pas partie de la licence des données.
- **Limites** : les effectifs valent ce que valent les pages Wikipedia dont ils viennent ; les trous sont signalés, jamais comblés par des suppositions. Voir la [FAQ](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/faq.md).

## Contribuer

Issues et pull requests sont bienvenues. Les corrections de données se font de préférence à la source, sur Wikipedia ou Wikidata ; les contributions au pipeline vont dans le [dépôt des données](https://github.com/florentfougeres/OpenFootballBase-Data). Lancez `npm run check` avant d'ouvrir une pull request. Les modifications de documentation se font en **français et en anglais** ([guide de contribution](docs/fr/contributing.md)).
