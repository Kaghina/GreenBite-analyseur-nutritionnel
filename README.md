# GreenBite – Analyseur nutritionnel

GreenBite est une application web développée avec **Dash** (Python) qui aide à faire des choix alimentaires plus sains :

- **Analyse de produit** : recherche par nom, par code-barres, par photo ou par webcam. Affiche le Nutri-Score, la composition nutritionnelle pour une portion donnée et le pourcentage des apports de référence.
- **Analyse de recette** : composition d'une recette à partir de produits, calcul des valeurs nutritionnelles (total, pour 100 g, par portion), **Nutri-Score de la recette** et répartition des calories par ingrédient.
- **Alternatives plus saines** : pour chaque ingrédient d'une recette, recherche de produits similaires ayant un meilleur Nutri-Score, puis remplacement en un clic.
- **Idées recettes** : 19 recettes équilibrées avec leur Nutri-Score, leurs ingrédients et leurs étapes.
- **En savoir plus** : principes d'une alimentation équilibrée et lecture d'une étiquette nutritionnelle.

## Installation

### Prérequis

- Python **3.10 ou plus récent**
- Une connexion Internet (API OpenFoodFacts)
- Pour le scan de codes-barres, la bibliothèque **zbar** :
  - Windows : incluse avec `pyzbar`. Si l'import échoue, installez le [Visual C++ Redistributable 2013](https://www.microsoft.com/fr-fr/download/details.aspx?id=40784).
  - macOS : `brew install zbar`
  - Linux (Debian/Ubuntu) : `sudo apt install libzbar0`

### Installer les dépendances

Il est recommandé d'utiliser un environnement virtuel :

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Lancement

```bash
python app.py
```

Puis ouvrez **http://127.0.0.1:8050** dans votre navigateur.

Options (variables d'environnement) :

| Variable          | Défaut | Rôle                                               |
|-------------------|--------|----------------------------------------------------|
| `PORT`            | `8050` | Port du serveur                                    |
| `GREENBITE_DEBUG` | `1`    | `0` pour désactiver le mode debug (rechargement auto, outils Dash) |

> **Webcam** : le bouton « Scanner avec la webcam » ouvre une fenêtre OpenCV **sur la machine qui exécute le serveur**. Présentez le code-barres devant la caméra (30 s maximum). Pour fermer sans scanner : touche `Q` ou `Échap`, ou la croix de la fenêtre. Cette fonction n'a donc de sens qu'en local.

### Exemples pour tester

- Code-barres : `3017620422003` (Nutella), `5449000000996` (Coca-Cola)
- Recherche par nom : `pomme`, `yaourt nature`, `farine`, `huile olive`

## Organisation du code

```
app.py                  Point d'entrée : création de l'application, navbar, footer
components/
  navbar.py             Barre de navigation
  footer.py             Pied de page
  ui.py                 Composants partagés (pastille et échelle Nutri-Score, carte produit, tableau nutritionnel)
pages/                  Une page Dash par fichier (enregistrée avec dash.register_page)
  home.py               /                 Accueil
  analyze_product.py    /analyzer         Analyse d'un produit
  analyze_recipe.py     /recipe-analyzer  Analyse d'une recette + alternatives
  recipe_nutriwi.py     /recipes          Catalogue de recettes
  recipe_details.py     /recipe-details   Détail d'une recette (?recipe=<slug>)
  learn_more.py         /learn-more       Conseils nutritionnels
utils/
  products.py           Recherche de produits (OpenFoodFacts + CIQUAL), format commun, alternatives
  ciqual_data.py        Lecture et recherche dans la table CIQUAL locale
  Table-Ciqual.csv      Table de composition nutritionnelle CIQUAL (ANSES)
  nutrition.py          Calcul du Nutri-Score, totaux d'une recette, apports de référence
  barcode.py            Décodage de codes-barres (image téléversée, webcam)
  recipes_data.py       Données des recettes (ingrédients, étapes, Nutri-Score)
  theme.py              Palette de couleurs
assets/                 CSS (styles.css) et images, servis automatiquement par Dash
```

## Données et calculs

- **OpenFoodFacts** ([API publique](https://openfoodfacts.github.io/openfoodfacts-server/api/)) : produits du commerce (recherche par nom ou par code-barres). Le Nutri-Score officiel du produit est utilisé lorsqu'il est disponible.
- **CIQUAL** ([ANSES](https://ciqual.anses.fr)) : 3 186 aliments de base (fruits, légumes, farines…) stockés dans `utils/Table-Ciqual.csv`.
- **Nutri-Score calculé** : lorsqu'il n'est pas fourni (aliments CIQUAL, recettes), il est calculé selon l'algorithme 2017 pour les aliments solides (points négatifs : énergie, sucres, acides gras saturés, sodium ; points positifs : fibres, protéines). La part de fruits/légumes/légumineuses n'étant pas connue, elle est comptée à 0 : le score est donc une **estimation**, en particulier pour les huiles, fromages et boissons, qui ont des règles spécifiques dans l'algorithme officiel.
- **Nutri-Score d'une recette** : calculé sur la composition moyenne pour 100 g de la recette (somme des nutriments de chaque ingrédient pondérée par sa quantité).
- **Apports de référence (% AR)** : valeurs du règlement UE 1169/2011 pour un adulte (2000 kcal, 50 g de protéines, 70 g de lipides, 20 g d'AGS, 260 g de glucides, 90 g de sucres, 6 g de sel) ; 25 g pour les fibres.

## Limites connues

- La recherche par nom d'OpenFoodFacts est limitée par l'API (~10 requêtes/minute) : en cas de saturation, seuls les résultats CIQUAL s'affichent. Les recherches déjà faites sont mises en cache.
- Les ingrédients d'une recette sont conservés pendant la session du navigateur (ils sont perdus à la fermeture de l'onglet).
