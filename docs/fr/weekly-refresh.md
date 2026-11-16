# Mise à jour hebdomadaire des joueurs en activité (cron sur serveur)

[English](../en/weekly-refresh.md)

`scripts/weekly_refresh.sh` tient à jour les joueurs **encore en activité** (dans un effectif en cours, ou avec une ligne de carrière ouverte) :

1. restaure la base depuis la dernière release si le serveur n'en a pas, puis la sauvegarde (3 sauvegardes conservées) ;
2. `careers --active --fresh` : relit l'infobox de carrière et le profil, en ignorant le cache ;
3. `reconcile --names --wikidata`, puis `stats --active --fresh` : relit les tableaux « Career statistics » ;
4. `enrich --what players careerclubs labels`, `coaches` (un échec de Wikidata est toléré : la table précédente est conservée), `progress`, `audit` (un problème bloquant arrête le script avant l'export) ;
5. exporte avec `--previous` (refusé si une saison figée a changé) et **publie** une release GitHub `data-X.Y.(Z+1)` (version corrective suivant la dernière), puis relance le déploiement du site.

Un verrou (`data/work/weekly.lock`) empêche deux passages simultanés (DuckDB n'a qu'un écrivain). Journal : `data/work/logs/weekly_AAAAMMJJ.log`.

## Installation sur le serveur (Ubuntu)

```bash
git clone https://github.com/florentfougeres/OpenFootballBase && cd OpenFootballBase
python3 -m venv .venv && .venv/bin/pip install -e .
gh auth login        # jeton aux droits minimaux pour créer des releases ; à garder hors du dépôt
crontab -e           # puis ajouter la ligne ci-dessous : lundi 03:00
```

```cron
0 3 * * 1 /home/USER/OpenFootballBase/scripts/weekly_refresh.sh
```

## Publication

Par défaut la release est **publiée** et le site redéployé (le contrôle `--previous` refuse d'abord un mauvais export). `PUBLISH=draft` crée un brouillon à publier à la main (`gh release edit data-X.Y.Z --draft=false`), `PUBLISH=none` s'arrête après l'export. Les notes sont génériques ; ajoutez l'entrée du journal à la main quand quelque chose de notable change. Le premier passage est long (des milliers de pages) ; les suivants ne relisent que les joueurs en activité.
