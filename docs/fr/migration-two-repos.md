# Plan de migration : dépôt application et dépôt données

[English](../en/migration-two-repos.md)

**État : plan seulement, rien n'est encore migré.** Décisions prises : l'historique git des fichiers de données est conservé (`git filter-repo`) ; le paquet Python garde le nom `openfootball` ; le nouveau dépôt repart de la dernière release (Data 1.21.0, republiée à l'identique), les anciennes releases restent dans le dépôt actuel ; le site est redéployé par un jeton (voir plus bas).

## Cible

| Dépôt | Rôle | Contenu |
|---|---|---|
| `OpenFootballBase` (actuel, **application**) | Le site | `web/`, `deploy.yml`, `PRODUCT.md`, la documentation du site (`website.md`, `getting-started.md`, `faq.md`), les entrées « site » du changelog. Son adresse (`florentfougeres.github.io/OpenFootballBase/`) ne change pas. |
| `OpenFootballBase-Data` (nouveau, **données**) | Le pipeline et les releases | `openfootball/` (code, migrations, périmètres), `tests/`, `scripts/`, `tools/`, `pyproject.toml`, `PROGRESS.md`, les releases `data-X.Y.Z`, la documentation des données (`data-model`, `commands`, `weekly-refresh`, `update-*`, `publishing-a-release`, `restoring-a-database`, `spec`, `roadmap`, les entrées « données » du changelog), la mention de licence des données (CC BY-SA 4.0 pour la part Wikipedia). |
| Non migré | | `dist_old_0959`, `dist_v1_1402`, `site/data`, `openfootball.egg-info` (ignorés ou obsolètes). |

`architecture.md` et `changelog.md` sont répartis entre les deux dépôts. La documentation reste bilingue dans les deux ([contributing.md](contributing.md)) ; chaque dépôt a son propre `CLAUDE.md` avec les règles qui le concernent.

## Points à modifier

- **`deploy.yml`** : `gh release download --repo "$GITHUB_REPOSITORY"` devient `--repo florentfougeres/OpenFootballBase-Data`. Le dépôt est public, le jeton par défaut suffit pour le lire. Le workflow reçoit une entrée `tag` pour `workflow_dispatch` ; son déclencheur `release` est retiré (la release d'un autre dépôt ne le lance pas).
- **Liens en dur** : `openfootball/restore.py` (`REPO`) et `web/src/lib/download.ts` (`RELEASES_URL`) pointent vers le dépôt données ; les README, `SECURITY.md` et les docs sont ajustés. Les alertes de sécurité sont propres à chaque dépôt.
- **Contrat entre les deux** : `manifest.json` porte `schema_version`. Le site déclare la version de schéma qu'il sait lire et le CI de l'application échoue si la dernière release la dépasse : une release MAJEURE des données devient un changement coordonné.
- **Développement du site** : `web/public/data` est aujourd'hui un export de la base locale. Un script `npm run data` télécharge à la place la dernière release du dépôt données.
- **CI** : `ci.yml` est scindé : le job `web` reste côté application, le job `test` (`pytest`) passe côté données.

## Redéployer le site : un jeton

Une release publiée dans le dépôt données ne lance pas seule un workflow du dépôt application. Mécanisme :

1. Une release est publiée dans `OpenFootballBase-Data` (à la main ou par `weekly_refresh.sh`).
2. `notify-site.yml` (dépôt données, déclencheur `release: published`) exécute `gh workflow run deploy.yml --repo florentfougeres/OpenFootballBase --ref main -f tag=<tag>` avec le jeton.
3. `deploy.yml` télécharge cette release précise, construit le site et le publie sur Pages.

`weekly_refresh.sh` perd son `sleep 60` et son contournement `gh workflow run`. Une release publiée à la main depuis l'interface GitHub redéploie aussi le site.

**Jeton à créer (par le propriétaire ; Claude ne le manipule jamais) :**

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token.
2. Repository access : *Only select repositories* → `OpenFootballBase` uniquement.
3. Permissions : *Actions → Read and write*, rien d'autre.
4. Expiration : aucune (choix du propriétaire). Sans expiration, le site ne cesse jamais de se redéployer sans bruit ; révoquez et recréez le jeton s'il a pu fuiter.
5. Le ranger dans le dépôt données :

```bash
gh secret set SITE_DEPLOY_TOKEN --repo florentfougeres/OpenFootballBase-Data
```

## Étapes (ajouter, vérifier, basculer, nettoyer)

| # | Étape | Retour arrière |
|---|---|---|
| 1 | Sauvegarder `data/work` (environ 10 Go) et `cache` (environ 3,5 Go). Créer `OpenFootballBase-Data`, public. | Supprimer le nouveau dépôt. |
| 2 | Cloner le dépôt actuel dans un dossier jetable, lancer `git filter-repo` en ne gardant que les chemins des données, pousser vers le nouveau dépôt. | Le dépôt actuel n'est pas touché. |
| 3 | Republier **Data 1.21.0** dans le nouveau dépôt à partir de l'archive actuelle (`gh release download`, puis `gh release create` avec le même tag, le titre `Data 1.21.0` et les notes). Les anciennes releases restent où elles sont. | Supprimer la nouvelle release. |
| 4 | **Vérifier avant toute bascule** : `openfootball restore-db --release data-1.21.0` depuis le nouveau dépôt redonne les SHA-256 du `manifest.json` ; `pytest -q` passe ; `weekly_refresh.sh` tourne avec `PUBLISH=none` puis `PUBLISH=draft`. | Rien n'a été basculé. |
| 5 | **Basculer** : créer le jeton et le secret ; ajouter `notify-site.yml` ; une pull request sur l'application (`deploy.yml`, `download.ts`, README, docs) ; lancer le déploiement à la main et comparer le site ; basculer le **serveur du cron** (voir ci-dessous). | Annuler la pull request et remettre l'ancien cron : l'ancien dépôt a toujours toutes ses releases. |
| 6 | **Nettoyer** (étape à part, à confirmer) : retirer `openfootball/`, `tests/`, `scripts/`, `tools/` du dépôt application ; ajouter un avis « les données ont déménagé » à son README et à sa dernière release ; déplacer l'issue ouverte. Aucune ancienne release n'est supprimée. | `git revert`. |

## Le clone du serveur (cron du lundi)

Le serveur exécute `scripts/weekly_refresh.sh` depuis un clone de l'ancien dépôt, avec sa base `data/work`, ses caches et son `gh` connecté. À basculer pendant l'étape 5, dans cet ordre :

1. Vérifier que l'ancien cron n'est pas en train de tourner (`data/work/weekly.lock` absent), puis le **désactiver** (`crontab -e`, ligne commentée).
2. Cloner `OpenFootballBase-Data` à côté de l'ancien dossier, créer le `.venv` et installer le paquet (`pip install -e .`).
3. Copier `data/work` et `cache` de l'ancien clone vers le nouveau (ou laisser le script reconstruire la base depuis la dernière release : il le fait à chaque passage, seul le cache Wikipedia vaut la peine d'être copié).
4. Vérifier `gh auth status` sur le serveur : le script a besoin de `gh release list`, `gh release download` et `gh release create` sur le dépôt données.
5. Lancer une fois à la main `PUBLISH=none scripts/weekly_refresh.sh`, puis `PUBLISH=draft`.
6. Mettre à jour la ligne du cron (chemin du nouveau dossier, ou `REPO_DIR`) et la réactiver.
7. Garder l'ancien clone une quinzaine de jours comme retour arrière, puis le supprimer.

## Risques

- Les liens vers d'anciennes releases ne sont pas redirigés entre deux dépôts distincts : les anciennes restent en ligne.
- Deux crons simultanés publieraient deux fois la même version : l'ancien est arrêté avant de lancer le nouveau (le verrou est local).
- La garde `--previous` du premier export a besoin du manifeste de la dernière release dans le nouveau dépôt : l'étape 3 le fournit.
- Jeton expiré : voir plus haut.
