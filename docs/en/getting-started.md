# Getting started

[Français](../fr/getting-started.md)

This repository is the **website**. The data and the pipeline are in [OpenFootballBase-Data](https://github.com/florentfougeres/OpenFootballBase-Data).

## I just want to look at football squads

Open the site: <https://florentfougeres.github.io/OpenFootballBase/>. Search a club or a player, or browse by country → league → season → club. Every squad shows the Wikipedia page it came from; the *Coverage* page shows what is missing. See the [FAQ](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/faq.md) for what the data does and does not contain.

## I want to use the data

Download the latest release from the [data repository's releases](https://github.com/florentfougeres/OpenFootballBase-Data/releases/latest) (`gh release download --repo florentfougeres/OpenFootballBase-Data --pattern "*-data.tar.gz"`), then read the [data dictionary](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/data-model.md). Attribution: Wikipedia text is CC BY-SA 4.0, Wikidata is CC0 ([licences](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/faq.md#licences)).

## I want to run or extend the pipeline

Go to the [data repository](https://github.com/florentfougeres/OpenFootballBase-Data) and its [getting-started guide](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/en/getting-started.md).

## I want to work on the website

Requirements: Node.js ≥ 22, git, the `gh` CLI.

```bash
git clone https://github.com/florentfougeres/OpenFootballBase.git && cd OpenFootballBase/web
npm install
npm run data        # latest data release into web/public/data (npm run data -- data-1.21.0 for a given one)
npm run dev         # http://localhost:5173
npm run check       # type check, also run by the CI
```

See [website.md](website.md) and [architecture.md](architecture.md).

## I want to contribute

Read [contributing.md](contributing.md). In short: small pull requests, and every documentation change in **both languages**.
