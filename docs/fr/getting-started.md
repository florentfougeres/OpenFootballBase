# Par où commencer

[English](../en/getting-started.md)

Ce dépôt est le **site**. Les données et le pipeline sont dans [OpenFootballBase-Data](https://github.com/florentfougeres/OpenFootballBase-Data).

## Je veux juste regarder des effectifs de football

Ouvrez le site : <https://florentfougeres.github.io/OpenFootballBase/>. Cherchez un club ou un joueur, ou parcourez pays → championnat → saison → club. Chaque effectif indique la page Wikipedia dont il vient ; la page *Couverture* montre ce qui manque. Voir la [FAQ](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/faq.md) pour ce que les données contiennent ou non.

## Je veux utiliser les données

Téléchargez la dernière release depuis les [releases du dépôt des données](https://github.com/florentfougeres/OpenFootballBase-Data/releases/latest) (`gh release download --repo florentfougeres/OpenFootballBase-Data --pattern "*-data.tar.gz"`), puis lisez le [dictionnaire de données](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/data-model.md). Attribution : le texte de Wikipedia est sous CC BY-SA 4.0, Wikidata est sous CC0 ([licences](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/faq.md#licences)).

## Je veux lancer ou étendre le pipeline

Rendez-vous dans le [dépôt des données](https://github.com/florentfougeres/OpenFootballBase-Data) et son [guide de démarrage](https://github.com/florentfougeres/OpenFootballBase-Data/blob/main/docs/fr/getting-started.md).

## Je veux travailler sur le site

Prérequis : Node.js ≥ 22, git, la commande `gh`.

```bash
git clone https://github.com/florentfougeres/OpenFootballBase.git && cd OpenFootballBase/web
npm install
npm run data        # dernière release de données dans web/public/data (npm run data -- data-1.21.0 pour une précise)
npm run dev         # http://localhost:5173
npm run check       # vérification des types, aussi lancée par le CI
```

Voir [website.md](website.md) et [architecture.md](architecture.md).

## Je veux contribuer

Lisez [contributing.md](contributing.md). En bref : petites pull requests, et toute modification de documentation dans **les deux langues**.
