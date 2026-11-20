"""
Calculs nutritionnels : Nutri-Score, totaux d'une recette, apports de référence.
"""

# Nutriments manipulés dans toute l'application (clé interne -> libellé, unité)
NUTRIENTS = [
    ("energy", "Énergie", "kcal"),
    ("proteins", "Protéines", "g"),
    ("carbs", "Glucides", "g"),
    ("sugars", "dont sucres", "g"),
    ("fat", "Lipides", "g"),
    ("saturated-fat", "dont acides gras saturés", "g"),
    ("fiber", "Fibres", "g"),
    ("salt", "Sel", "g"),
]

# Apports de référence pour un adulte (Règlement UE 1169/2011 ; fibres : recommandation ANSES)
DAILY_REFERENCE = {
    "energy": 2000,
    "proteins": 50,
    "carbs": 260,
    "sugars": 90,
    "fat": 70,
    "saturated-fat": 20,
    "fiber": 25,
    "salt": 6,
}

GRADES = ["a", "b", "c", "d", "e"]

# Seuils du Nutri-Score (aliments solides, version 2017).
# Un point est attribué pour chaque seuil strictement dépassé.
_ENERGY_KJ = [335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350]
_SUGARS = [4.5, 9, 13.5, 18, 22.5, 27, 31, 36, 40, 45]
_SAT_FAT = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
_SODIUM_MG = [90, 180, 270, 360, 450, 540, 630, 720, 810, 900]
_FIBER = [0.9, 1.9, 2.8, 3.7, 4.7]
_PROTEINS = [1.6, 3.2, 4.8, 6.4, 8.0]


def to_float(value, default=0.0):
    """Convertit une valeur (str, None, nombre) en float sans lever d'exception."""
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _points(value, thresholds):
    return sum(1 for t in thresholds if value > t)


def nutriscore_points(nutrition):
    """Renvoie le score numérique du Nutri-Score pour des valeurs pour 100 g."""
    energy_kj = to_float(nutrition.get("energy")) * 4.184
    sodium_mg = to_float(nutrition.get("salt")) / 2.5 * 1000

    negative = (
        _points(energy_kj, _ENERGY_KJ)
        + _points(to_float(nutrition.get("sugars")), _SUGARS)
        + _points(to_float(nutrition.get("saturated-fat")), _SAT_FAT)
        + _points(sodium_mg, _SODIUM_MG)
    )
    fiber_pts = _points(to_float(nutrition.get("fiber")), _FIBER)
    protein_pts = _points(to_float(nutrition.get("proteins")), _PROTEINS)

    # Règle officielle : au-delà de 11 points négatifs, les protéines ne comptent pas
    # (sauf si fruits/légumes ≥ 80 %, information dont on ne dispose pas ici).
    if negative >= 11:
        return negative - fiber_pts
    return negative - fiber_pts - protein_pts


def calculate_nutriscore(nutrition):
    """Calcule la lettre du Nutri-Score (a à e) à partir de valeurs pour 100 g."""
    score = nutriscore_points(nutrition)
    if score <= -1:
        return "a"
    if score <= 2:
        return "b"
    if score <= 10:
        return "c"
    if score <= 18:
        return "d"
    return "e"


def has_nutrition_data(product):
    """Vrai si le produit contient au moins une valeur nutritionnelle non nulle."""
    return any(to_float(product.get(key)) > 0 for key, _, _ in NUTRIENTS)


def normalize_grade(grade):
    """Renvoie une lettre a-e valide ou une chaîne vide."""
    grade = (grade or "").strip().lower()
    return grade if grade in GRADES else ""


def compute_recipe_totals(ingredients):
    """
    Calcule les totaux nutritionnels d'une recette.

    Chaque ingrédient est un dictionnaire produit (valeurs pour 100 g) contenant
    une clé 'quantity' en grammes.
    """
    totals = {key: 0.0 for key, _, _ in NUTRIENTS}
    total_weight = 0.0

    for ingredient in ingredients:
        quantity = to_float(ingredient.get("quantity"), 100)
        total_weight += quantity
        for key in totals:
            totals[key] += to_float(ingredient.get(key)) * quantity / 100

    if total_weight > 0:
        per_100g = {k: v / total_weight * 100 for k, v in totals.items()}
    else:
        per_100g = {k: 0.0 for k in totals}

    return {"total_weight": total_weight, "totals": totals, "per_100g": per_100g}
