"""
Recherche de produits : API OpenFoodFacts + table CIQUAL locale.

Tous les produits renvoyés ont le même format :
    code, product_name, brands, categories, image_url, nutriscore_grade, source,
    energy (kcal), proteins, carbs, sugars, fat, saturated-fat, fiber, salt  (pour 100 g)
"""
import json
import logging
from functools import lru_cache

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.ciqual_data import get_ciqual_by_code, search_ciqual
from utils.nutrition import (GRADES, calculate_nutriscore, has_nutrition_data,
                             normalize_grade, to_float)

logger = logging.getLogger("greenbite.products")

OFF_BASE_URL = "https://world.openfoodfacts.org"
OFF_FIELDS = ",".join([
    "code", "product_name", "product_name_fr", "brands", "categories",
    "image_front_url", "image_url", "nutriscore_grade", "nutriments",
])
# OpenFoodFacts demande un User-Agent identifiant l'application
HEADERS = {"User-Agent": "GreenBite/1.0 (projet etudiant)"}
TIMEOUT = 10

_session = requests.Session()
_session.headers.update(HEADERS)
# L'API OpenFoodFacts répond parfois 429/503 (limite de débit) : on réessaie automatiquement
_session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=2, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",),
)))


def _normalize_off_product(product, code=None):
    """Convertit un produit OpenFoodFacts au format interne."""
    nutriments = product.get("nutriments", {}) or {}

    energy = nutriments.get("energy-kcal_100g")
    if energy is None and nutriments.get("energy_100g") is not None:
        energy = to_float(nutriments.get("energy_100g")) / 4.184  # kJ -> kcal

    normalized = {
        "code": str(code or product.get("code", "")),
        "product_name": product.get("product_name_fr") or product.get("product_name") or "Produit sans nom",
        "brands": product.get("brands", "") or "",
        "categories": product.get("categories", "") or "",
        "image_url": product.get("image_front_url") or product.get("image_url") or "",
        "source": "OpenFoodFacts",
        "energy": round(to_float(energy), 1),
        "proteins": to_float(nutriments.get("proteins_100g")),
        "carbs": to_float(nutriments.get("carbohydrates_100g")),
        "sugars": to_float(nutriments.get("sugars_100g")),
        "fat": to_float(nutriments.get("fat_100g")),
        "saturated-fat": to_float(nutriments.get("saturated-fat_100g")),
        "fiber": to_float(nutriments.get("fiber_100g")),
        "salt": to_float(nutriments.get("salt_100g")),
    }

    grade = normalize_grade(product.get("nutriscore_grade"))
    if not grade and has_nutrition_data(normalized):
        grade = calculate_nutriscore(normalized)
        normalized["nutriscore_computed"] = True
    normalized["nutriscore_grade"] = grade
    return normalized


def search_by_barcode(barcode):
    """Recherche un produit par code-barres (ou code CIQUAL_xxx). Renvoie None si introuvable."""
    if not barcode:
        return None
    barcode = str(barcode).strip()

    if barcode.startswith("CIQUAL_"):
        return get_ciqual_by_code(barcode)

    try:
        response = _session.get(
            f"{OFF_BASE_URL}/api/v2/product/{barcode}.json",
            params={"fields": OFF_FIELDS},
            timeout=TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                return _normalize_off_product(data.get("product", {}), code=barcode)
    except requests.RequestException as exc:
        logger.warning("OpenFoodFacts injoignable (code-barres %s) : %s", barcode, exc)
    return None


def search_openfoodfacts(name, limit=20):
    """Recherche des produits OpenFoodFacts par nom (seuls les succès sont mis en cache)."""
    try:
        return [dict(p) for p in _search_openfoodfacts_cached(name.lower(), limit)]
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Recherche OpenFoodFacts impossible pour '%s' : %s", name, exc)
        return []


@lru_cache(maxsize=256)
def _search_openfoodfacts_cached(name, limit):
    response = _session.get(
        f"{OFF_BASE_URL}/cgi/search.pl",
        params={
            "search_terms": name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": limit,
            "fields": OFF_FIELDS,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    products = response.json().get("products", [])
    return tuple(
        _normalize_off_product(p)
        for p in products
        if p.get("product_name") or p.get("product_name_fr")
    )


def search_by_name(name, include_ciqual=True, include_off=True):
    """Recherche par nom dans CIQUAL (aliments de base) puis OpenFoodFacts (produits du commerce)."""
    if not name or len(name.strip()) < 2:
        return []
    name = name.strip()
    results = []
    if include_ciqual:
        results.extend(search_ciqual(name, limit=10))
    if include_off:
        results.extend(search_openfoodfacts(name, limit=20))
    return results


def find_healthier_alternatives(product, keyword, limit=10):
    """
    Cherche des produits correspondant à `keyword` ayant un meilleur Nutri-Score
    que `product`, triés du meilleur au moins bon.
    """
    current = normalize_grade(product.get("nutriscore_grade")) or "e"
    current_rank = GRADES.index(current)

    candidates = search_by_name(keyword)
    seen = set()
    better = []
    for candidate in candidates:
        grade = normalize_grade(candidate.get("nutriscore_grade"))
        if not grade or GRADES.index(grade) >= current_rank:
            continue
        key = candidate.get("code") or candidate.get("product_name")
        if key in seen:
            continue
        seen.add(key)
        better.append(candidate)

    better.sort(key=lambda p: GRADES.index(p["nutriscore_grade"]))
    return better[:limit]


def product_option(product):
    """Option de dropdown (label lisible + produit encodé en JSON)."""
    grade = product.get("nutriscore_grade", "")
    label = product.get("product_name", "Produit")
    if product.get("brands") and product.get("source") != "CIQUAL":
        label += f" – {product['brands'].split(',')[0]}"
    label += f"  [{product.get('source')}]"
    if grade:
        label += f"  Nutri-Score {grade.upper()}"
    return {"label": label, "value": json.dumps(product)}
