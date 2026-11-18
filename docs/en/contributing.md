# Contributing

[Français](../fr/contributing.md)

Thank you for helping. This repository is the **website**; the data pipeline has its own [contributing guide](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/contributing.md) in the [data repository](https://github.com/florentfougeres/OpenFootballBase-Data) (new countries, parser fixes, data corrections: those go there, or upstream on Wikipedia and Wikidata).

## Set up

See [getting-started.md](getting-started.md): Node.js ≥ 22, then `npm install`, `npm run data` and `npm run dev` in `web/`.

## Workflow

1. Open an issue for anything bigger than a small fix, so we can agree on the approach.
2. Branch, make a focused change.
3. Run `npm run check && npm run build` (in `web/`).
4. Open a pull request describing what changes and why. CI runs the same checks.

## Principles to respect

- **No backend, no tracking.** The site stays static: no analytics, no cookies, no third-party request other than the pinned DuckDB engine ([website.md](website.md)).
- **Never display a guess as a fact.** A gap is shown as a gap.
- **No secrets, no personal data** in code, logs or commit messages.
- **SQL is parameterised.** Never build SQL from external text.

## Documentation is bilingual — always

Every change to the documentation or to the README **must be made in both languages**: English and French. Concretely:

- `README.md` (English) and `README.fr.md` (French) are edited together.
- Each guide exists as `docs/en/<name>.md` and `docs/fr/<name>.md` with the same file name, structure and links; each starts with a link to the other language.
- That includes the changelog (`docs/{fr,en}/changelog.md`).
- User-facing strings of the website go in both languages of `web/src/lib/i18n.ts`.
- When you add a doc, add it to both indexes (`docs/en/README.md`, `docs/fr/README.md`).

## Conventions

- Commit messages in English, imperative mood, one logical change per commit.
- Site changes go in the changelog, "Site and tooling" section (both languages). Data releases are named `Data X.Y.Z` and live in the [data repository](https://github.com/florentfougeres/OpenFootballBase-Data).
