# DESIGN.md — OpenFootballBase

Ce document fixe le système visuel et les conventions d'interface de l'application web (`web/`). Les jetons vivent dans `web/src/app.css` ; ce fichier dit comment s'en servir. Le produit et ses publics sont dans `PRODUCT.md`.

## Principes

1. **Sobre et dense, jamais décoratif.** Une base de données de football : les chiffres et les noms d'abord. Pas de néon, pas de lueur colorée, pas de dégradé de texte.
2. **Un seul accent d'action : le vert de la marque.** La couleur d'un club n'apparaît qu'en bande ou en teinte de fond légère, jamais pour le texte.
3. **App sur mobile, outil sur bureau.** Mobile : navigation du bas, feuilles, transitions glissées. Bureau : barre latérale, deux colonnes, volet de détail.
4. **Le détail ne fait pas quitter la liste.** Un aperçu à côté (bureau) ou une page enfant avec retour (mobile).
5. **Chaque donnée vérifiable.** La source reste visible à côté de l'information.

## Jetons (`web/src/app.css`)

- **Couleurs** : `--bg`, `--surface`, `--surface-2` (trois niveaux), `--fg`, `--muted`, `--line`, `--accent` (+ `--accent-fg`, `--accent-soft`), `--warn`, `--info`. Thèmes sombre (par défaut) et clair définis ensemble, contrastes ≥ 4,5:1.
- **Typographie** : Barlow Condensed (titres, chiffres clés) et Barlow (texte) ; chiffres tabulaires pour les tableaux (`tabular-nums`) ; corps 16 px minimum sur mobile.
- **Formes** : rayons 12 px (contrôles), 16 px (cartes), 24 px et plus (feuilles, barre du bas).
- **Mouvement** : retours d'appui 150 ms, transitions 250 ms, courbe `cubic-bezier(0.2, 0.8, 0.2, 1)` ; la sortie est plus courte que l'entrée ; tout est neutralisé par `prefers-reduced-motion`.
- **Élévation** : filet 1 px (`--line`) plutôt qu'ombre ; ombre douce uniquement pour ce qui flotte (barre du bas, notification, palette de recherche).

## Navigation

| Écran | Mobile (< 1024 px) | Bureau (≥ 1024 px) |
|---|---|---|
| Entrées principales | Barre du bas : Accueil, Explorer, Recherche (bouton central), Compétitions, Suivis | Barre latérale : Accueil, Explorer, Compétitions, Suivis ; Couverture et À propos en bas |
| Recherche | Plein écran | Palette centrée (`/`, Ctrl/⌘ K) |
| Retour | Bouton dans la barre du haut quand la profondeur > 0 | Fil d'Ariane |
| Suivis | Page Suivis (clubs, joueurs, compétitions épinglés) | Liste dans la barre latérale + page Suivis |
| Réglages | Engrenage de la barre du haut → page Réglages (thème, langue, couverture, à propos) | Thème et langue en bas de la barre latérale ; liens secondaires dans la barre latérale |

La profondeur et le sens (avant / arrière) viennent de la pile de navigation de `lib/app.svelte.ts` ; les écrans racines sont l'accueil, Explorer, Compétitions et Suivis.

## Composants communs

- `Segmented` : onglets (flèches, Début, Fin) ou bascule à `aria-pressed` ; hauteur tactile 40 px sur mobile.
- `FollowButton` : suivre / ne plus suivre (stockage local, notification annoncée sans prendre le focus).
- `Sheet` : feuille modale (du bas sur mobile, centrée sur bureau) pour les choix secondaires (saisons, filtres) ; focus géré.
- `FollowAvatar` : écusson, logo ou initiales d'un suivi.
- `PlayerPreview` : volet de détail d'un joueur à côté de l'effectif (≥ 1280 px).
- `SearchOverlay`, `Sidebar`, `BottomNav`, `Header`, `Toast` : la coque.

## Règles

- Cibles tactiles ≥ 44 px ; un geste n'est jamais la seule voie (un bouton existe toujours).
- Focus visible (2 px, `--accent`) et jamais masqué par une barre collante.
- Aucun emoji comme icône ; une seule famille d'icônes en trait de 1,8 px.
- Toute chaîne visible existe en français et en anglais (`lib/i18n.ts`).
