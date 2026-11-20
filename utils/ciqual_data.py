"""
Accès à la table de composition nutritionnelle CIQUAL (ANSES), fournie en CSV local.
"""
import logging
import os
import unicodedata
from functools import lru_cache

import pandas as pd

logger = logging.getLogger("greenbite.ciqual")

CSV_PATH = os.path.join(os.path.dirname(__file__), "Table-Ciqual.csv")

# Colonnes du CSV CIQUAL -> clés internes
COLUMNS = {
    "energy": "Energie, Règlement UE N° 1169/2011 (kcal/100 g)",
    "proteins": "Protéines, N x facteur de Jones (g/100 g)",
    "carbs": "Glucides (g/100 g)",
    "sugars": "Sucres (g/100 g)",
    "fat": "Lipides (g/100 g)",
    "saturated-fat": "AG saturés (g/100 g)",
    "fiber": "Fibres alimentaires (g/100 g)",
    "salt": "Sel chlorure de sodium (g/100 g)",
}
ENERGY_KJ_COLUMN = "Energie, Règlement UE N° 1169/2011 (kJ/100 g)"
ENERGY_JONES_COLUMN = "Energie, N x facteur Jones, avec fibres  (kcal/100 g)"


def _strip_accents(text):
    text = unicodedata.normalize("NFD", str(text).lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _parse_value(raw):
    """
    Convertit une valeur CIQUAL en float.
    Le fichier utilise la virgule décimale, '-' pour « non disponible »,
    '< 0,3' pour « inférieur à » et 'traces'.
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return 0.0
    text = str(raw).strip().replace(",", ".").replace("<", "").strip()
    if text in ("", "-") or text.lower() == "traces":
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


@lru_cache(maxsize=1)
def load_ciqual():
    """Charge le CSV une seule fois et renvoie un DataFrame normalisé."""
    df = pd.read_csv(CSV_PATH, sep=",", dtype=str, encoding="utf-8")
    data = pd.DataFrame({
        "code": df["alim_code"].astype(str),
        "name": df["alim_nom_fr"].fillna(""),
        "group": df["alim_grp_nom_fr"].fillna(""),
    })
    for key, column in COLUMNS.items():
        data[key] = df[column].map(_parse_value)

    # L'énergie réglementaire manque pour de nombreux aliments bruts : on la complète
    # avec la valeur en kJ, puis l'énergie « Jones », puis un calcul depuis les macronutriments.
    fallbacks = [
        df[ENERGY_KJ_COLUMN].map(_parse_value) / 4.184,
        df[ENERGY_JONES_COLUMN].map(_parse_value),
        4 * data["proteins"] + 4 * data["carbs"] + 9 * data["fat"] + 2 * data["fiber"],
    ]
    for fallback in fallbacks:
        data["energy"] = data["energy"].where(data["energy"] > 0, fallback)
    data["energy"] = data["energy"].round(1)
    data["search_key"] = data["name"].map(_strip_accents)
    logger.info("Table CIQUAL chargée : %d aliments", len(data))
    return data


def _row_to_product(row):
    # Import local pour éviter une dépendance circulaire
    from utils.nutrition import calculate_nutriscore

    product = {
        "code": f"CIQUAL_{row['code']}",
        "product_name": row["name"],
        "brands": "CIQUAL",
        "categories": row["group"] or "Aliment de base",
        "image_url": "",
        "source": "CIQUAL",
    }
    for key in COLUMNS:
        product[key] = round(float(row[key]), 3)
    product["nutriscore_grade"] = calculate_nutriscore(product)
    return product


def search_ciqual(query, limit=10):
    """Recherche des aliments CIQUAL dont le nom contient tous les mots de la requête."""
    if not query:
        return []
    try:
        data = load_ciqual()
        words = _strip_accents(query).split()
        mask = pd.Series(True, index=data.index)
        for word in words:
            mask &= data["search_key"].str.contains(word, regex=False)
        matches = data[mask]
        # Les noms les plus courts sont en général les aliments les plus « bruts »
        matches = matches.loc[matches["name"].str.len().sort_values().index].head(limit)
        return [_row_to_product(row) for _, row in matches.iterrows()]
    except Exception:
        logger.exception("Erreur lors de la recherche CIQUAL")
        return []


def get_ciqual_by_code(code):
    """Renvoie l'aliment CIQUAL correspondant au code (avec ou sans préfixe CIQUAL_)."""
    code = str(code).replace("CIQUAL_", "")
    try:
        data = load_ciqual()
        matches = data[data["code"] == code]
        if matches.empty:
            return None
        return _row_to_product(matches.iloc[0])
    except Exception:
        logger.exception("Erreur lors de la lecture CIQUAL")
        return None
