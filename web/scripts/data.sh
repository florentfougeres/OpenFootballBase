#!/usr/bin/env bash
# Télécharge les données (Parquet) de la dernière release du dépôt de données dans web/public/data, pour développer le site.
# Usage : npm run data            (dernière release)    npm run data -- data-1.21.0     (une release précise)
set -euo pipefail
cd "$(dirname "$0")/.."
TAG="${1:-}"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
gh release download ${TAG:+"$TAG"} --repo florentfougeres/OpenFootballBase-Data --pattern "*-data.tar.gz" --dir "$tmp"
archive=$(ls "$tmp"/*-data.tar.gz)
if tar -tzf "$archive" | grep -Eq '(^/|(^|/)\.\.(/|$))'; then echo "archive suspecte (chemin absolu ou « .. »)"; exit 1; fi
rm -rf public/data && mkdir -p public/data
tar -xzf "$archive" --no-same-owner -C public/data
test -s public/data/manifest.json && echo "données prêtes dans web/public/data"
