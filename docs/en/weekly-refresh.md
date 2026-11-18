# Weekly refresh of active players (server cron)

[Français](../fr/weekly-refresh.md)

`scripts/weekly_refresh.sh` keeps the players who are **still active** up to date (in a current squad, or with an open career line):

1. **rebuilds the working database from the latest published release** on every run (`restore-db`), so each run starts from exactly what the site shows; the previous database is moved to `data/work/backups/` (3 kept);
2. `careers --active --fresh`: re-reads the career infobox and profile, ignoring the cache;
3. `reconcile --names --wikidata`, then `stats --active --fresh`: re-reads the "Career statistics" tables;
4. `enrich --what players careerclubs labels`, `coaches` (a Wikidata failure is tolerated: the previous table is kept), `matches --fresh-seasons 2` (OpenFootball results and goalscorers, then current-season scores completed from Wikipedia for the 9 first divisions; a network failure is tolerated), `enrich --what leaguelogos` (logos and Wikipedia pages of the competitions, including those of `matches`), `players-data` (OpenFootball height and birthplace), `progress`, `audit` (a blocking problem stops the script before the export);
5. exports with `--previous` (refused if a frozen season changed) and **publishes** a GitHub release `data-X.Y.(Z+1)` (patch bump of the latest one), then reruns the site deployment.

A lock (`data/work/weekly.lock`) prevents two runs at once (DuckDB has a single writer). Log: `data/work/logs/weekly_YYYYMMDD.log`.

## Server setup (Ubuntu)

```bash
git clone https://github.com/florentfougeres/OpenFootballBase && cd OpenFootballBase
python3 -m venv .venv && .venv/bin/pip install -e .
gh auth login        # token with the minimal scope to create releases; keep it outside the repository
crontab -e           # then add the line below: Monday 03:00
```

```cron
0 3 * * 1 /home/USER/OpenFootballBase/scripts/weekly_refresh.sh
```

## Publishing

By default the release is **published** and the site redeployed (the continuity guard `--previous` refuses a bad export first). `PUBLISH=draft` creates a draft to publish by hand (`gh release edit data-X.Y.Z --draft=false`), `PUBLISH=none` stops after the export. Release notes are generic; add the changelog entry by hand when something notable changes. A first run is long (thousands of pages); the following ones only re-read the active players.
