# Architecture

[English](../en/architecture.md)

OpenFootballBase est réparti sur **deux dépôts** :

| Dépôt | Rôle |
|---|---|
| [`OpenFootballBase-Data`](https://github.com/florentfougeres/OpenFootballBase-Data) | Le **pipeline Python** qui lit Wikipedia, Wikidata et les données ouvertes OpenFootball dans une base DuckDB locale, l'**export** qui la transforme en fichiers Parquet versionnés, et les **releases** (`Data X.Y.Z`) qui les publient. Son architecture, son modèle de données, son journal de conception et ses guides y sont. |
| `OpenFootballBase` (celui-ci) | Le **site statique** (`web/`) : Svelte 5 + Vite + Tailwind 4, DuckDB-WASM lit les fichiers Parquet dans le navigateur, déployé sur GitHub Pages. |

## De la release au site

```
OpenFootballBase-Data                                          OpenFootballBase (ce dépôt)
  weekly_refresh.sh / export manuel
        │
        ▼
  release GitHub  Data X.Y.Z  (openfootballbase-data.tar.gz : Parquet + manifest.json + SCHEMA.md)
        │  release publiée
        ▼
  notify-site.yml ──(jeton SITE_DEPLOY_TOKEN : gh workflow run)──▶  deploy.yml (entrée : tag)
                                                                      │ télécharge cette release, construit web/
                                                                      ▼
                                                                GitHub Pages ──▶ navigateur : DuckDB-WASM, requêtes HTTP à plages
```

- Un navigateur ne peut pas lire directement un fichier de release (pas de CORS) : `deploy.yml` télécharge l'archive côté serveur et la sert depuis le même domaine que la page.
- `deploy.yml` se lance aussi à chaque push de `web/**` sur `main`, avec la dernière release, et à la main (`gh workflow run deploy.yml --ref main -f tag=data-X.Y.Z`).
- La release affichée est celle que désigne le tag ; sans tag, la dernière. Revenir en arrière = redéployer un tag antérieur.

## Idées directrices

- **Pas de serveur.** Le site interroge les fichiers Parquet dans le navigateur ; pas de mesure d'audience, pas de cookies.
- **Les données ne sont pas dans ce dépôt.** `web/public/data` est un téléchargement local (`npm run data`), ignoré par git.
- **Le site lit le schéma que la release publie** (`manifest.json` : tables, fichiers, `schema_version`). Une nouvelle table ou colonne est une release mineure des données ; le site doit pouvoir ignorer ce qu'il ne connaît pas.
- **Sécurité par construction** : le moteur DuckDB est servi par le site avec son empreinte SHA-384 vérifiée, et une Content-Security-Policy limite ce que la page peut charger ([website.md](website.md)).

## Organisation du dépôt

| Chemin | Rôle |
|---|---|
| `web/` | Le site ([website.md](website.md)). |
| `.github/workflows/` | `ci.yml` (vérification des types et build), `deploy.yml` (publication sur GitHub Pages). |
| `docs/` | Cette documentation (`fr/` et `en/`). |
| `PRODUCT.md` | Contexte produit utilisé pour la conception du site. |
