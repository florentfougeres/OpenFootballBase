<p align="center"><img src="docs/images/logo.svg" alt="OpenFootballBase" width="88"></p>

<h1 align="center">OpenFootballBase</h1>

<p align="center">
  <strong>The website of OpenFootballBase: an open database of football club squads, season by season, built from Wikipedia and Wikidata.</strong><br>
  This repository is the <b>application</b>. The data and the pipeline that builds it live in <a href="https://github.com/florentfougeres/OpenFootballBase-Data">OpenFootballBase-Data</a>.
</p>

<p align="center">
  <a href="https://florentfougeres.github.io/OpenFootballBase/">Website</a> ·
  <a href="https://github.com/florentfougeres/OpenFootballBase-Data/releases/latest">Download the data</a> ·
  <a href="https://github.com/florentfougeres/OpenFootballBase-Data">Data repository</a> ·
  <a href="docs/README.md">Documentation</a> ·
  <a href="README.fr.md">Français</a>
</p>

<p align="center">
  <a href="https://github.com/florentfougeres/OpenFootballBase/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/florentfougeres/OpenFootballBase/actions/workflows/ci.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="Code: MIT" src="https://img.shields.io/badge/code-MIT-blue.svg"></a>
  <img alt="Data: CC BY-SA 4.0" src="https://img.shields.io/badge/data-CC%20BY--SA%204.0-lightgrey.svg">
</p>

---

## What this repository is

A static [Svelte](https://svelte.dev) 5 + Vite + Tailwind site, bilingual (English / French): league dashboards, club pages with squad and movements between seasons, player pages with career timeline, competitions with results and standings, a coverage heat map, a player search with filters and CSV export. [DuckDB-WASM](https://duckdb.org/docs/api/wasm/overview) reads the Parquet files over HTTP range requests, so there is no backend, no analytics and no cookies. The DuckDB engine is served from the site itself, and a Content-Security-Policy restricts what the page can load.

The site shows **the data of the latest release of [OpenFootballBase-Data](https://github.com/florentfougeres/OpenFootballBase-Data)**: the data is not stored here.

## Develop the site

Requirements: **Node.js ≥ 22**, **git** and the `gh` CLI (to download the data).

```bash
git clone https://github.com/florentfougeres/OpenFootballBase.git && cd OpenFootballBase/web
npm install
npm run data        # downloads the latest data release into web/public/data (npm run data -- data-1.21.0 for a given one)
npm run dev         # http://localhost:5173
npm run check       # type check (svelte-check), also run by the CI
```

## How the site is deployed

Publishing a release in the data repository starts the deployment by itself (`notify-site.yml` there starts [`deploy.yml`](.github/workflows/deploy.yml) here, with the tag of the release). A push of `web/**` to `main` redeploys with the latest release. The token that allows the first step, its rights and its expiration are described in the [data repository's guide](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/publishing-a-release.md).

To redeploy by hand:

```bash
gh workflow run deploy.yml --repo florentfougeres/OpenFootballBase --ref main -f tag=data-X.Y.Z   # without the tag: the latest release
```

## Documentation

The documentation is available in English and French ([index](docs/en/README.md)); every page exists in both languages. The data dictionary, the commands, the weekly refresh, the releases, the design log and the roadmap are in the [data repository](https://github.com/florentfougeres/OpenFootballBase-Data/tree/main/docs/en).

| Page | What it covers |
|---|---|
| [getting-started.md](docs/en/getting-started.md) | Where to begin |
| [website.md](docs/en/website.md) | Code map, data loading, security headers |
| [architecture.md](docs/en/architecture.md) | How the two repositories fit together |
| [security.md](docs/en/security.md) | Reporting, controls in place |
| [changelog.md](docs/en/changelog.md) | Site and tooling changes (data releases: [data changelog](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/changelog.md)) |
| [migration-two-repos.md](docs/en/migration-two-repos.md) | The split between this repository and the data repository |

## Sources, licences and limits

- **Sources of the data**: [Wikipedia](https://www.wikipedia.org) (text under CC BY-SA 4.0; each squad cites its page and revision), [Wikidata](https://www.wikidata.org) (CC0) and the open [OpenFootball](https://github.com/openfootball) data (CC0, match results).
- **Code**: [MIT](LICENSE). **Data**: derived from Wikipedia, so shared under **CC BY-SA 4.0** with attribution to Wikipedia contributors.
- **Club logos** are Wikimedia images, often not free, displayed for illustration only; they are not part of the data licence.
- **Limits**: squads are as good as the Wikipedia pages they come from; gaps are reported, never filled with guesses. See the [FAQ](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/faq.md).

## Contributing

Issues and pull requests are welcome. Data corrections are best made upstream on Wikipedia or Wikidata; pipeline contributions go to the [data repository](https://github.com/florentfougeres/OpenFootballBase-Data). Please run `npm run check` before opening a pull request. Documentation changes must be made in **both English and French** ([contributing guide](docs/en/contributing.md)).
