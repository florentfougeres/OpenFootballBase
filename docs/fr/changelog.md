# Journal des changements

[English](../en/changelog.md)

Changements du site et de ses outils, du plus récent au plus ancien. Les releases de données (`Data X.Y.Z`, tag `data-X.Y.Z`) et leurs notes vivent dans le dépôt des données.

Les releases de données (`Data X.Y.Z`) sont listées dans le [changelog du dépôt des données](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/changelog.md).

## Site et outils

### 2026-11-21
- **Filtres compacts sur la page Compétitions (mobile)** : sur téléphone, le sélecteur Clubs / Équipes nationales est pleine largeur et les confédérations tiennent sur une seule ligne qui défile (elles occupaient trois lignes) : la liste des compétitions commence environ 200 px plus haut. Sur grand écran rien ne change.
- **Plus d'image cassée** : une photo de joueur (ou un logo de compétition) supprimée de Wikimedia depuis la publication des données n'affiche plus une image cassée avec sa légende : la photo disparaît de la page du joueur, le logo cède la place à une coupe ou au drapeau du pays (comme le font déjà les logos de clubs avec l'écusson). Les données sont corrigées à la source par `enrich --what imagecheck` (dépôt des données).
- **Barre d'onglets mobile en pilule** : sur téléphone, la navigation du bas est maintenant une pilule posée sur un dock (une bande pleine en bas de l'écran : la page s'arrête au-dessus, rien ne passe derrière), à la manière des barres d'onglets d'iOS. Une capsule glisse sous l'onglet actif, y compris vers « Plus » quand son panneau est ouvert. Mêmes cinq entrées et mêmes libellés toujours visibles ; « réduire les animations » supprime le glissement.

### 2026-11-18
- **Deux dépôts** : le site reste ici ; les données, le pipeline et les releases ont déménagé dans [OpenFootballBase-Data](https://github.com/florentfougeres/OpenFootballBase-Data). Une release publiée là-bas lance le déploiement du site (`notify-site.yml`, jeton `SITE_DEPLOY_TOKEN`) ; `deploy.yml` prend le tag de la release en entrée ; `npm run data` télécharge les données pour le développement. Plan : [migration-two-repos.md](migration-two-repos.md).
- **Page Compétitions** : une vue Clubs (par confédération, puis une rubrique « Monde » pour les coupes intercontinentales, qui ne sont plus mélangées à l'UEFA) et une vue Équipes nationales (phases finales, qualifications, amicaux), avec des icônes et les logos Wikipedia des compétitions ; celles que seule la source de matchs connaît sont dans leur continent.
- **Onglet Résultats** sur chaque page de compétition : classement calculé avec la forme, matchs par journée avec les buteurs ; onglet Palmarès aligné sur le palmarès des clubs. Script hebdomadaire : `matches` (résultats, puis complément de la saison en cours depuis Wikipedia) et `enrich --what leaguelogos` à sa suite.

### 2026-11-16
- **Audit de cohérence** (`audit`) : contrôle toute la base avant chaque publication, lancé par le script hebdomadaire (un problème bloquant l'arrête). Statistiques : les nombres de buts impossibles (plus de 3 par match et au moins 10, fautes de frappe de Wikipedia comme « 11 matchs, 100 buts ») sont désormais laissés vides au lieu d'être affichés ; les tableaux dont la cellule de saison porte un `!colspan` parasite ne décalent plus les colonnes.
- **Mise à jour hebdomadaire** (`scripts/weekly_refresh.sh`, [weekly-refresh.md](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/weekly-refresh.md)) : script pour un cron sur serveur qui relit les joueurs encore en activité (infobox de carrière et tableaux de statistiques), exporte et publie une release. Nouvelle option `stats --active`.

### 2026-11-13
- **Sécurité et vitesse** : politique de sécurité de contenu (CSP) ; le moteur DuckDB est vérifié par une empreinte SHA-384 et son extension Parquet est hébergée avec le site (voir [security.md](security.md), [website.md](website.md)) ; `restore-db` vérifie le SHA-256 de chaque fichier ; le déploiement télécharge la release qui l'a déclenché ; actions GitHub figées par SHA ; Dependabot, analyse de secrets et protection au push activés.
- **Releases renommées** `Data X.Y.Z` avec le tag `data-X.Y.Z` (elles s'appelaient `data-v1` … `data-v13`, avec des noms comme « Data v1.10.0 (date) »).
- **Dictionnaire de données bilingue** (`SCHEMA.md` en anglais, `SCHEMA.fr.md` en français) et documentation bilingue sous `docs/fr/` et `docs/en/` ; README bilingue.
- **Page Compétitions** : grille uniforme groupée par confédération ; les coupes continentales apparaissent dans leur confédération.
- **Site** : section Joueurs (filtres, téléchargement CSV), tableau de bord des tendances d'un championnat, frise de carrière, mouvements d'un club d'une saison à l'autre, page club + effectif unifiée, couverture en grille de chaleur.
- **Outils** : `openfootball restore-db`, `openfootball continental`, mode `--fresh` et `tools/refresh.sh --fresh` pour le mercato.

### 2026-11-12
- Site refait en Svelte 5 + Vite + Tailwind 4 (style d'application sombre), navigation générique par pays, accueil rapide, bandeau bêta.
- Transferts en cours de saison et cohérence des prêts (D13), identification Wikidata des joueurs sans lien, licence MIT.
- Belgique, Portugal, Pays-Bas et Turquie (analyseurs nl et tr sur le HTML rendu) ; effectif de la saison en cours depuis la page du club ; participants de la Ligue des champions (D14).
- Projet renommé OpenFootballBase ; premier déploiement sur GitHub Pages.

### 2026-11-11
- Projet démarré de zéro (voir [spec.md](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/spec.md), §2) : pipeline, périmètres déclaratifs, saisons figées, identité par QID Wikidata, carrières depuis les infoboxes, clubs du monde, logos.
