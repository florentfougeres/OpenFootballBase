#!/usr/bin/env bash
# Mise à jour hebdomadaire (cron) : relit les joueurs encore en activité (infobox de carrière + tableaux de statistiques Wikipedia),
# réconcilie, exporte et PUBLIE une release GitHub `data-X.Y.(Z+1)` puis redéploie le site.
# Usage : scripts/weekly_refresh.sh          (variables : REPO_DIR, PUBLISH=release|draft|none, défaut release ; draft = brouillon à publier à la main)
set -euo pipefail
cd "${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
export OPENFOOTBALL_CONTACT="https://github.com/florentfougeres/OpenFootballBase"
OF=.venv/bin/openfootball
DB=data/work/openfootball.duckdb
STAMP=$(date +%Y%m%d)
mkdir -p data/work/logs data/work/backups dist
exec > >(tee -a "data/work/logs/weekly_$STAMP.log") 2>&1

LOCK=data/work/weekly.lock                              # un seul passage à la fois (la base DuckDB n'a qu'un écrivain) ; mkdir est atomique, sans flock (absent de macOS)
mkdir "$LOCK" 2>/dev/null || { echo "déjà en cours (ou verrou périmé : rmdir $LOCK), abandon"; exit 0; }
trap 'rmdir "$LOCK"' EXIT

echo "##### début $(date +%FT%T)"
LAST=$(gh release list --limit 1 --json tagName -q '.[0].tagName')
# Base de travail reconstruite à chaque passage depuis la dernière release publiée : on repart toujours de ce que le site affiche, sans dérive ni reste d'un essai.
if [ -f "$DB" ]; then mv "$DB" "data/work/backups/openfootball_avant_$STAMP.duckdb"; fi   # l'ancienne base est gardée (3 dernières)
ls -1t data/work/backups/*.duckdb | tail -n +4 | xargs -r rm -f
$OF restore-db --release "$LAST" --db "$DB"

$OF careers --active --fresh                           # infobox de carrière + profil
$OF reconcile --names --wikidata
$OF stats --active --fresh --cache cache/wikipedia_stats_v2   # tableaux « Career statistics » des joueurs en activité, relus
$OF enrich --what players careerclubs labels
$OF coaches || echo "entraîneurs : échec ignoré (Wikidata indisponible), table de la release précédente conservée"   # mandats d'entraîneurs (Wikidata)
$OF progress
$OF audit                                               # cohérence de toute la base : un problème bloquant arrête avant l'export

mkdir -p /tmp/prev && gh release download "$LAST" --pattern "*-data.tar.gz" --dir /tmp/prev --clobber
tar -xzOf /tmp/prev/*-data.tar.gz manifest.json > /tmp/prev/manifest.json
rm -rf dist/data && $OF export --out dist/data --archive dist/openfootballbase-data.tar.gz --previous /tmp/prev/manifest.json   # refuse si une saison figée a changé

if [ "${PUBLISH:-release}" != none ]; then
  IFS=. read -r MA MI PA <<<"${LAST#data-}"
  NEXT="$MA.$MI.$((PA + 1))"
  printf '# Data %s — %s\n**Weekly refresh**\nType: Patch release (data fixes)\n\n## Changed\n- Players still active: career infobox and statistics tables re-read.\n\n---\n\n# Data %s — %s\n**Mise à jour hebdomadaire**\nType : Correctif (corrections de données)\n\n## Modifié\n- Joueurs encore en activité : infobox de carrière et tableaux de statistiques relus.\n' \
    "$NEXT" "$(date +%F)" "$NEXT" "$(date +%F)" > dist/notes.md
  if [ "${PUBLISH:-release}" = draft ]; then DRAFT=--draft; else DRAFT=; fi
  gh release create "data-$NEXT" dist/openfootballbase-data.tar.gz $DRAFT --target main --title "Data $NEXT" --notes-file dist/notes.md
  if [ -z "$DRAFT" ]; then sleep 60; gh workflow run deploy.yml --ref main; fi   # le déploiement déclenché par la release n'aboutit pas toujours : on relance
fi
echo "##### fin $(date +%FT%T)"
