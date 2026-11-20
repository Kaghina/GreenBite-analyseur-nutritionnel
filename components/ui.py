"""
Composants d'interface réutilisés par plusieurs pages.
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

from utils.nutrition import DAILY_REFERENCE, GRADES, NUTRIENTS, to_float
from utils.theme import GREENBITE_COLORS

NUTRI_COLORS = GREENBITE_COLORS["nutriscore"]


def nutriscore_badge(grade, size="1rem"):
    """Petite pastille colorée affichant la lettre du Nutri-Score."""
    grade = (grade or "").lower()
    if grade not in GRADES:
        return html.Span("?", className="nutri-badge", style={"backgroundColor": "#9e9e9e", "fontSize": size})
    return html.Span(grade.upper(), className="nutri-badge",
                     style={"backgroundColor": NUTRI_COLORS[grade], "fontSize": size})


def nutriscore_scale(grade):
    """Échelle A-E avec la lettre active mise en évidence (style étiquette officielle)."""
    grade = (grade or "").lower()
    if grade not in GRADES:
        return html.P("Nutri-Score non disponible pour ce produit.", className="text-muted")
    return html.Div(
        [
            html.Div(
                g.upper(),
                className="nutri-scale-item" + (" active" if g == grade else ""),
                style={"backgroundColor": NUTRI_COLORS[g]},
            )
            for g in GRADES
        ],
        className="nutri-scale",
        title=f"Nutri-Score {grade.upper()}",
    )


def product_summary_card(product):
    """Carte compacte présentant un produit sélectionné (avant ajout / analyse)."""
    if not product:
        return None
    image_url = product.get("image_url")
    return dbc.Card(
        dbc.Row(
            [
                dbc.Col(
                    html.Img(src=image_url, className="product-thumb") if image_url
                    else html.Div(html.I(className="fas fa-apple-alt fa-3x text-muted"), className="text-center"),
                    width=3, className="d-flex align-items-center justify-content-center p-2",
                ),
                dbc.Col(
                    [
                        html.H5([product.get("product_name", "Produit"), " ",
                                 nutriscore_badge(product.get("nutriscore_grade"))], className="mb-1"),
                        html.Small(
                            " · ".join(filter(None, [product.get("brands"), f"Source : {product.get('source', '?')}"])),
                            className="text-muted",
                        ),
                        html.Div(
                            [
                                dbc.Badge(f"{to_float(product.get('energy')):.0f} kcal", color="info", className="me-1"),
                                dbc.Badge(f"{to_float(product.get('proteins')):.1f} g prot.", color="success", className="me-1"),
                                dbc.Badge(f"{to_float(product.get('carbs')):.1f} g gluc.", color="warning", className="me-1"),
                                dbc.Badge(f"{to_float(product.get('fat')):.1f} g lip.", color="danger", className="me-1"),
                                html.Small(" pour 100 g", className="text-muted"),
                            ],
                            className="mt-2",
                        ),
                    ],
                    width=9, className="p-2",
                ),
            ],
            className="g-0",
        ),
        className="mb-3",
    )


def clicked_index():
    """
    Pour un callback à entrées « pattern-matching » (ALL) : renvoie l'index de
    l'élément réellement cliqué, ou None si le callback a été déclenché par la
    simple (re)création des composants.
    """
    trigger = dash.ctx.triggered[0] if dash.ctx.triggered else None
    if not trigger or not trigger.get("value"):
        return None
    return dash.ctx.triggered_id["index"]


def search_results_list(results, id_type):
    """
    Liste cliquable des résultats de recherche. Chaque ligne a pour id
    {"type": id_type, "index": i} ; un clic sélectionne le produit.
    """
    if not results:
        return None
    items = []
    for i, product in enumerate(results):
        image_url = product.get("image_url")
        details = " · ".join(filter(None, [
            product.get("brands") if product.get("source") != "CIQUAL" else "Aliment de base",
            f"{to_float(product.get('energy')):.0f} kcal/100 g",
        ]))
        items.append(dbc.ListGroupItem(
            html.Div([
                html.Img(src=image_url, className="result-thumb") if image_url
                else html.Div(html.I(className="fas fa-seedling"), className="result-thumb result-thumb-empty"),
                html.Div([
                    html.Div(product.get("product_name", "Produit"), className="fw-semibold"),
                    html.Small(details, className="text-muted"),
                ], className="flex-grow-1 mx-3"),
                nutriscore_badge(product.get("nutriscore_grade"), size="1.1rem"),
            ], className="d-flex align-items-center"),
            id={"type": id_type, "index": i},
            action=True, n_clicks=0, className="result-item",
        ))
    return html.Div([
        html.Small(f"{len(results)} résultat(s) — cliquez sur un produit pour le sélectionner :",
                   className="text-muted d-block mb-2"),
        dbc.ListGroup(items, className="results-list"),
    ], className="mt-2")


def nutrition_table(columns):
    """
    Tableau nutritionnel.

    `columns` est une liste de (titre, dict_valeurs). Une dernière colonne « % AR »
    est calculée à partir de la dernière colonne de valeurs.
    """
    reference_values = columns[-1][1]
    header = html.Thead(html.Tr(
        [html.Th("Nutriment")] + [html.Th(title) for title, _ in columns] + [html.Th("% AR*")]
    ))
    rows = []
    for key, label, unit in NUTRIENTS:
        indent = label.startswith("dont")
        value = to_float(reference_values.get(key))
        rows.append(html.Tr(
            [html.Td(label, className="ps-4 fst-italic" if indent else "fw-semibold")]
            + [html.Td(f"{to_float(values.get(key)):.1f} {unit}") for _, values in columns]
            + [html.Td(f"{value / DAILY_REFERENCE[key] * 100:.0f} %")]
        ))
    return html.Div([
        dbc.Table([header, html.Tbody(rows)], striped=True, hover=True, size="sm", responsive=True),
        html.Small("* AR : apports de référence pour un adulte (2000 kcal/jour).", className="text-muted"),
    ])


def error_alert(message, color="warning"):
    return dbc.Alert(message, color=color, className="mt-2 mb-0")
