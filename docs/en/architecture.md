# Architecture

[Français](../fr/architecture.md)

OpenFootballBase is split into **two repositories**:

| Repository | Role |
|---|---|
| [`OpenFootballBase-Data`](https://github.com/florentfougeres/OpenFootballBase-Data) | The **Python pipeline** that reads Wikipedia, Wikidata and the open OpenFootball data into a local DuckDB database, the **export** that turns it into versioned Parquet files, and the **releases** (`Data X.Y.Z`) that publish them. Its architecture, data model, design log and guides are there. |
| `OpenFootballBase` (this one) | The **static website** (`web/`): Svelte 5 + Vite + Tailwind 4, DuckDB-WASM reading the Parquet files in the browser, deployed to GitHub Pages. |

## From a release to the site

```
OpenFootballBase-Data                                          OpenFootballBase (this repository)
  weekly_refresh.sh / manual export
        │
        ▼
  GitHub release  Data X.Y.Z  (openfootballbase-data.tar.gz: Parquet + manifest.json + SCHEMA.md)
        │  release published
        ▼
  notify-site.yml ──(token SITE_DEPLOY_TOKEN: gh workflow run)──▶  deploy.yml (input: tag)
                                                                      │ downloads that release, builds web/
                                                                      ▼
                                                                GitHub Pages ──▶ browser: DuckDB-WASM, HTTP range requests
```

- A browser cannot read a release asset directly (no CORS): `deploy.yml` downloads the archive server-side and serves it from the same domain as the page.
- `deploy.yml` also runs on every push of `web/**` to `main`, with the latest release, and by hand (`gh workflow run deploy.yml --ref main -f tag=data-X.Y.Z`).
- The release the site shows is the one named by the tag; without a tag, the latest one. Rolling back the site = redeploy an earlier tag.

## Key ideas

- **No backend.** The site queries the Parquet files in the browser; no analytics, no cookies.
- **The data is not in this repository.** `web/public/data` is a local download (`npm run data`), ignored by git.
- **The site reads the schema that the release publishes** (`manifest.json`: tables, files, `schema_version`). A new table or column is a minor data release; the site must be able to ignore what it does not know.
- **Security by construction**: the DuckDB engine is served by the site with its SHA-384 checked, and a Content-Security-Policy restricts what the page can load ([website.md](website.md)).

## Repository layout

| Path | Role |
|---|---|
| `web/` | The site ([website.md](website.md)). |
| `.github/workflows/` | `ci.yml` (type check and build), `deploy.yml` (publication to GitHub Pages). |
| `docs/` | This documentation (`fr/` and `en/`). |
| `PRODUCT.md` | Product context used for the site's design. |
