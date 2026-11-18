# Project rules for Claude Code

This repository is the **application** (the website, `web/`). The data pipeline and the releases are in the sibling repository `OpenFootballBase-Data` (`../OpenFootballBase-Data`), which has its own `CLAUDE.md`.

- **Documentation is bilingual — always.** Any change to `README.md` must be mirrored in `README.fr.md`, and any change to a page under `docs/en/` must be mirrored in the same file under `docs/fr/` (and vice versa), including `changelog.md`. New docs go in both indexes (`docs/en/README.md`, `docs/fr/README.md`). Website strings go in both languages of `web/src/lib/i18n.ts`.
- **Commit and push only when the user asks** ("Commit" = commit only, "Commit push" = commit and push). Never commit the Impeccable install folders (`.claude/agents`, `.claude/skills`, `.github/agents`, `.github/hooks`, `.github/skills`), databases or caches.
- **The site shows the data of a release of `OpenFootballBase-Data`** (`deploy.yml` takes the tag as input). Data releases, their naming (`Data X.Y.Z`, tag `data-X.Y.Z`) and their changelog are in that repository; site changes go in this repository's changelog, "Site and tooling" section, in both languages.
- **Contact in the User-Agent** (when a script of this repository calls Wikipedia/Wikidata) is always `OPENFOOTBALL_CONTACT="https://github.com/florentfougeres/OpenFootballBase"`, never a personal e-mail.
- Do not propose `enrich --what photos`.
