# Changelog

[Français](../fr/changelog.md)

Changes to the website and its tooling, newest first. The data releases (`Data X.Y.Z`, with tag `data-X.Y.Z`) and their notes live in the data repository.

Data releases (`Data X.Y.Z`) are listed in the [data repository's changelog](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/changelog.md).

## Site and tooling

### 2026-11-21
- **Compact filters on the Competitions page (mobile)**: on phones, the Clubs / National teams switch is full width and the confederations fit on a single scrolling line (they took three lines): the list of competitions starts about 200 px higher. Nothing changes on large screens.
- **No more broken images**: a player photo (or a competition logo) deleted from Wikimedia since the data was published no longer shows a broken image with its caption: the photo disappears from the player page, the logo gives way to a trophy or the country flag (as club logos already do with the crest). The data is fixed at the source by `enrich --what imagecheck` (data repository).
- **Pill-shaped mobile tab bar**: on phones, the bottom navigation is now a pill set on a dock (a solid band at the bottom of the screen: the page stops above it, nothing shows through), in the manner of iOS tab bars. A capsule slides under the active tab, including to "More" while its panel is open. Same five entries and labels still always visible; "reduce motion" removes the slide.

### 2026-11-18
- **Two repositories**: the website stays here; the data, the pipeline and the releases moved to [OpenFootballBase-Data](https://github.com/florentfougeres/OpenFootballBase-Data). A release published there starts the site deployment (`notify-site.yml`, token `SITE_DEPLOY_TOKEN`); `deploy.yml` takes the release tag as input; `npm run data` downloads the data for development. Plan: [migration-two-repos.md](migration-two-repos.md).
- **Competitions page**: a Clubs view (by confederation, then a "World" section for intercontinental cups, no longer mixed with UEFA) and a National teams view (finals, qualifiers, friendlies), with icons and the competitions' Wikipedia logos; competitions known only from the match source sit in their continent.
- **Results tab** on every competition page: computed standings with form, matches by matchday with goalscorers; honours tab aligned with the club honours panel. Weekly script: `matches` (results, then current-season completion from Wikipedia) and `enrich --what leaguelogos` after it.

### 2026-11-16
- **Consistency audit** (`audit`): checks the whole database before every publication, run by the weekly script (a blocking problem stops it). Statistics: goal counts that are impossible (more than 3 per match and at least 10, typos in Wikipedia such as "11 matches, 100 goals") are now left empty instead of displayed; tables whose season cell carries a stray `!colspan` no longer shift the columns.
- **Weekly refresh** (`scripts/weekly_refresh.sh`, [weekly-refresh.md](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/weekly-refresh.md)): script for a server cron that re-reads the players still active (career infobox and statistics tables), exports and publishes a release. New option `stats --active`.

### 2026-11-13
- **Security and speed**: Content-Security-Policy; the DuckDB engine is verified by a SHA-384 integrity hash and its Parquet extension is hosted with the site (see [security.md](security.md), [website.md](website.md)); `restore-db` verifies every file's SHA-256; deployment downloads the release that triggered it; GitHub Actions pinned by SHA; Dependabot, secret scanning and push protection enabled.
- **Releases renamed** `Data X.Y.Z` with tag `data-X.Y.Z` (they used to be `data-v1` … `data-v13` with names like "Data v1.10.0 (date)").
- **Bilingual data dictionary** (`SCHEMA.md` in English, `SCHEMA.fr.md` in French) and bilingual documentation under `docs/fr/` and `docs/en/`; bilingual README.
- **Competitions page**: uniform grid grouped by confederation; continental cups appear under their confederation.
- **Site**: Players section (filters, CSV download), league trends dashboard, career timeline, club movements between seasons, unified club + squad page, coverage heat map.
- **Tooling**: `openfootball restore-db`, `openfootball continental`, `--fresh` mode and `tools/refresh.sh --fresh` for the transfer window.

### 2026-11-12
- Site rebuilt with Svelte 5 + Vite + Tailwind 4 (dark app style), generic navigation by country, fast home page, beta notice.
- Mid-season transfers and loan consistency (D13), Wikidata identification of players without links, MIT licence.
- Belgium, Portugal, Netherlands and Türkiye (nl and tr parsers on rendered HTML); current-season squad from the club page; Champions League participants (D14).
- Project renamed OpenFootballBase; first deployment to GitHub Pages.

### 2026-11-11
- Project started from zero (see [spec.md](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/spec.md), §2): pipeline, declarative scopes, frozen seasons, identity by Wikidata QID, careers from infoboxes, world clubs, logos.
