# Changelog

[Français](../fr/changelog.md)

Changes to the website and its tooling, newest first. The data releases (`Data X.Y.Z`, with tag `data-X.Y.Z`) and their notes live in the data repository.

Data releases (`Data X.Y.Z`) are listed in the [data repository's changelog](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/changelog.md).

## Site and tooling

### 2026-11-22
- **Player page in three tabs**: Career (clubs as a table or timeline, then national-team caps), Stats and Honours, under an unchanged header. A tab with nothing to show does not appear (and the bar disappears when only Career is left); Honours appears once its content is loaded. The tab is in the address (`?tab=`), so it can be shared and the back button restores it; left and right arrows, Home and End move between tabs. On mobile the header is more compact (photo next to the name, the two totals side by side) so the tabs are reachable without scrolling.

### 2026-11-21
- **Lighter, clearer Squad tab**: three levels clearly separated. The *view* (Players | Movements) and the *display* (list or cards, two icons on the right, players only) fit on one line; the four large figures become one summary line; the *filters* (nationality, on loan) are grouped below (no more position filter: the squad is already grouped by position), and the "11 / 42 players" counter with "Reset" only appears when a filter is active. The first player is visible without scrolling on mobile.
- **Club page in three tabs**: Overview (the club's profile: city, founding, stadium, league, links, coaches, and a shortcut to the season's squad), Squad (with a Players | Movements switch to see arrivals and departures from one season to the next) and Honours. Title chips no longer sit under the club name: honours have their own tab. The tab is in the address (`?tab=`): it can be shared and the browser's back button restores it. Without `?tab=`, the squad opens when the address carries a season (from a table or a season's list) and the overview otherwise (from the club list, search or a player's career). The side column is gone: honours and the profile each have their own tab.
- **Compact club page on mobile**: the header goes from a large tinted block of over 300 px to a card of about 150 px (logo and name side by side, country and division on one line, the club's colour band on a neutral background; the near-identical second name no longer appears). The season strip runs edge to edge, without arrows on touch. The first player is visible without scrolling. Large screens keep their layout; the club tint is lightened there (11%) so the text stays readable.
- **Interface audit, three passes**:
  - *Accessibility*: every page has its own tab title ("Arsenal FC · 2026/27 · OpenFootballBase", the player's name on their page); the light theme's accent is a little darker (`#087245`) so green text on pale green and white text on the accent exceed 4.5:1; field placeholders, the Coverage page heat map (black/white switch point computed for each theme) and active season chips (which had dark text on green because of a global link rule) also meet 4.5:1; "reduce motion" removes smooth scrolling and slides.
  - *Mobile*: the filters of the Players and Coverage pages take half the height (full-width search, season and nationality side by side, position on one line, age and "playing abroad" behind "More filters"; the "squads only" checkbox becomes a toggle chip); header buttons, breadcrumb and home links at 44 px; no functional text under 11 px any more; the player page's career and national-team tables put the years under the club name; club names in the standings wrap onto two lines instead of being cut.
  - *Polish*: no single word on the last line of a paragraph, About page lines capped at 58 characters, Ballon d'Or years no longer cut off with "…".
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
