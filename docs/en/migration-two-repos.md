# Migration plan: application repository and data repository

[Français](../fr/migration-two-repos.md)

**Status: plan only, nothing is migrated yet.** Decisions taken: git history of the data files is kept (`git filter-repo`); the Python package keeps the name `openfootball`; the new repository starts from the latest release (Data 1.21.0, republished identically), older releases stay in the current repository; the site is redeployed by a token (see below).

## Target

| Repository | Role | Content |
|---|---|---|
| `OpenFootballBase` (current, **application**) | The site | `web/`, `deploy.yml`, `PRODUCT.md`, the site documentation (`website.md`, `getting-started.md`, `faq.md`), the site entries of the changelog. Its URL (`florentfougeres.github.io/OpenFootballBase/`) does not change. |
| `OpenFootballBase-Data` (new, **data**) | The pipeline and the releases | `openfootball/` (code, migrations, scopes), `tests/`, `scripts/`, `tools/`, `pyproject.toml`, `PROGRESS.md`, the `data-X.Y.Z` releases, the data documentation (`data-model`, `commands`, `weekly-refresh`, `update-*`, `publishing-a-release`, `restoring-a-database`, `spec`, `roadmap`, the data entries of the changelog), the licence notice of the data (CC BY-SA 4.0 for the Wikipedia part). |
| Not migrated | | `dist_old_0959`, `dist_v1_1402`, `site/data`, `openfootball.egg-info` (ignored or obsolete). |

`architecture.md` and `changelog.md` are split between the two repositories. Documentation stays bilingual in both ([contributing.md](contributing.md)); each repository gets its own `CLAUDE.md` with the rules that concern it.

## Points to change

- **`deploy.yml`**: `gh release download --repo "$GITHUB_REPOSITORY"` becomes `--repo florentfougeres/OpenFootballBase-Data`. The repository is public, so the default token can read it. The workflow gets a `tag` input for `workflow_dispatch`; its `release` trigger is removed (a release of another repository does not start it).
- **Hard-coded links**: `openfootball/restore.py` (`REPO`) and `web/src/lib/download.ts` (`RELEASES_URL`) point to the data repository; README files, `SECURITY.md` and the docs are adjusted. Security advisories are per repository.
- **Contract between the two**: `manifest.json` carries `schema_version`. The site declares the schema version it can read and the application CI fails when the latest release exceeds it, so a MAJOR data release becomes a coordinated change.
- **Site development**: `web/public/data` is an export of the local database today. An `npm run data` script downloads the latest release of the data repository instead.
- **CI**: `ci.yml` is split: the `web` job stays in the application repository, the `test` job (`pytest`) moves to the data repository.

## Redeploying the site: a token

A release published in the data repository does not start a workflow of the application repository by itself. Mechanism:

1. A release is published in `OpenFootballBase-Data` (by hand or by `weekly_refresh.sh`).
2. `notify-site.yml` (data repository, trigger `release: published`) runs `gh workflow run deploy.yml --repo florentfougeres/OpenFootballBase --ref main -f tag=<tag>` with the token.
3. `deploy.yml` downloads that exact release, builds the site and publishes it on Pages.

`weekly_refresh.sh` loses its `sleep 60` and its `gh workflow run` workaround. A release published by hand from the GitHub interface also redeploys the site.

**Token to create (by the owner; Claude never handles it):**

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token.
2. Repository access: *Only select repositories* → `OpenFootballBase` only.
3. Permissions: *Actions → Read and write*, nothing else.
4. Expiration: one year at most. **When it expires the site silently stops redeploying**: note the date in the repository and renew it before.
5. Store it in the data repository:

```bash
gh secret set SITE_DEPLOY_TOKEN --repo florentfougeres/OpenFootballBase-Data
```

## Steps (add, verify, switch, clean up)

| # | Step | Rollback |
|---|---|---|
| 1 | Back up `data/work` (about 10 GB) and `cache` (about 3.5 GB). Create `OpenFootballBase-Data`, public. | Delete the new repository. |
| 2 | Clone the current repository to a throw-away folder, run `git filter-repo` keeping only the data paths, push to the new repository. | The current repository is untouched. |
| 3 | Republish **Data 1.21.0** in the new repository from the current archive (`gh release download`, then `gh release create` with the same tag, title `Data 1.21.0` and notes). Older releases stay where they are. | Delete the new release. |
| 4 | **Verify before any switch**: `openfootball restore-db --release data-1.21.0` from the new repository gives the SHA-256 of `manifest.json`; `pytest -q` passes; `weekly_refresh.sh` runs with `PUBLISH=none` then `PUBLISH=draft`. | Nothing was switched. |
| 5 | **Switch**: create the token and the secret; add `notify-site.yml`; one pull request on the application (`deploy.yml`, `download.ts`, README, docs); run the deployment by hand and compare the site; switch the **cron server** (see below). | Revert the pull request and restore the old cron: the old repository still has all its releases. |
| 6 | **Clean up** (separate, confirmed step): remove `openfootball/`, `tests/`, `scripts/`, `tools/` from the application repository; add a "data moved" notice to its README and to its last release; move the open issue. No old release is deleted. | `git revert`. |

## The server clone (Monday cron)

The server runs `scripts/weekly_refresh.sh` from a clone of the old repository, with its `data/work`, its caches and a signed-in `gh`. Switch it during step 5, in this order:

1. Check that the old cron is not running (`data/work/weekly.lock` absent), then **disable** it (`crontab -e`, line commented out).
2. Clone `OpenFootballBase-Data` next to the old folder, create the `.venv` and install the package (`pip install -e .`).
3. Copy `data/work` and `cache` from the old clone to the new one (or let the script rebuild the database from the latest release: it does so on every run, only the Wikipedia cache is worth copying).
4. Check `gh auth status` on the server: the script needs `gh release list`, `gh release download` and `gh release create` on the data repository.
5. Run `PUBLISH=none scripts/weekly_refresh.sh` once by hand, then `PUBLISH=draft`.
6. Update the cron line (path of the new folder, or `REPO_DIR`) and re-enable it.
7. Keep the old clone for about two weeks as a rollback, then delete it.

## Risks

- Links to old releases are not redirected between two separate repositories: the old ones stay online.
- Two crons running at once would publish the same version twice: the old one is stopped before the new one starts (the lock is local).
- The `--previous` guard of the first export needs the manifest of the latest release in the new repository: step 3 provides it.
- Expired token: see above.
