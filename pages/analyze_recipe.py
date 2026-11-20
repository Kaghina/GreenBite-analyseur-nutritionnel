"""
Page « Analyse Recette » : composition d'une recette à partir de produits,
calcul des apports nutritionnels, du Nutri-Score de la recette et
recherche d'alternatives plus saines pour chaque ingrédient.
"""
import json

import dash
from dash import ALL, MATCH, Input, Output, State, callback, dcc, html, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from components.ui import (clicked_index, error_alert, nutriscore_badge,
                           nutriscore_scale, nutrition_table,
                           product_summary_card, search_results_list)
from utils.barcode import decode_barcode_from_upload, scan_barcode_with_webcam
from utils.nutrition import (calculate_nutriscore, compute_recipe_totals,
                             has_nutrition_data, to_float)
from utils.products import (find_healthier_alternatives, product_option,
                            search_by_barcode, search_by_name)

dash.register_page(__name__, path="/recipe-analyzer", title="GreenBite - Analyse Recette", name="Analyse Recette")


def _search_tabs():
    return dbc.Tabs([
        dbc.Tab(label="Par nom", tab_id="name", children=html.Div([
            dbc.InputGroup([
                dbc.Input(id="rec-name-input", placeholder="Ex : farine, beurre, tomate…", debounce=True),
                dbc.Button([html.I(className="fas fa-search me-2"), "Rechercher"],
                           id="rec-name-btn", color="success"),
            ]),
            dcc.Loading([
                dcc.Store(id="rec-search-results"),
                html.Div(id="rec-name-status"),
                html.Div(id="rec-name-results"),
            ]),
        ], className="p-3")),
        dbc.Tab(label="Par code-barres", tab_id="barcode", children=html.Div([
            dbc.InputGroup([
                dbc.Input(id="rec-barcode-input", placeholder="Ex : 3017620422003"),
                dbc.Button("Rechercher", id="rec-barcode-btn", color="success"),
            ]),
            dcc.Loading(html.Div(id="rec-barcode-status")),
        ], className="p-3")),
        dbc.Tab(label="Par image / webcam", tab_id="image", children=html.Div([
            dcc.Upload(
                id="rec-upload",
                children=html.Div([html.I(className="fas fa-upload me-2"),
                                   "Cliquez ou déposez une photo de code-barres"]),
                className="upload-box", multiple=False, accept="image/*",
            ),
            html.Div("ou", className="text-center text-muted my-2"),
            dbc.Button([html.I(className="fas fa-camera me-2"), "Scanner avec la webcam"],
                       id="rec-webcam-btn", color="success", className="w-100"),
            dcc.Loading(html.Div(id="rec-image-status")),
        ], className="p-3")),
    ], active_tab="name")


layout = html.Div([
    html.H1("Analyse de recette", className="text-center mb-4"),
    dcc.Store(id="rec-candidate"),
    # Conservé pendant la session du navigateur (navigation entre pages)
    dcc.Store(id="rec-ingredients", data=[], storage_type="session"),

    dbc.Card([
        dbc.CardHeader(html.H3("Créer votre recette", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([dbc.Label("Nom de la recette"),
                         dbc.Input(id="rec-title", placeholder="Ma recette", persistence=True,
                                   persistence_type="session")], md=8),
                dbc.Col([dbc.Label("Nombre de portions"),
                         dbc.Input(id="rec-servings", type="number", min=1, max=50, value=4,
                                   persistence=True, persistence_type="session")], md=4),
            ], className="mb-4"),
            html.H4("Ajouter un ingrédient"),
            _search_tabs(),
            html.Div(id="rec-preview", className="mt-3"),
            dbc.Row([
                dbc.Col([dbc.Label("Quantité (g)"),
                         dbc.Input(id="rec-quantity", type="number", min=1, value=100)], md=4),
                dbc.Col(dbc.Button([html.I(className="fas fa-plus me-2"), "Ajouter à la recette"],
                                   id="rec-add-btn", color="success", className="w-100", disabled=True),
                        md=8, className="d-flex align-items-end"),
            ]),
            html.Div(id="rec-add-msg"),
        ]),
    ], className="mb-4"),

    dbc.Card([
        dbc.CardHeader(dbc.Row([
            dbc.Col(html.H3("Ingrédients", className="mb-0")),
            dbc.Col(dbc.Button("Vider la recette", id="rec-clear-btn", color="link",
                               className="text-danger p-0"), width="auto"),
        ], align="center")),
        dbc.CardBody([
            html.Div(id="rec-ingredients-list", className="mb-3"),
            dbc.Button([html.I(className="fas fa-chart-pie me-2"), "Analyser la recette"],
                       id="rec-analyze-btn", color="primary", className="w-100", disabled=True),
        ]),
    ], className="mb-4"),

    dcc.Loading(html.Div(id="rec-results")),
])


# ---------------------------------------------------------------- Sélection d'un ingrédient

@callback(
    Output("rec-search-results", "data"),
    Output("rec-name-status", "children"),
    Input("rec-name-input", "value"),
    Input("rec-name-btn", "n_clicks"),
    prevent_initial_call=True,
)
def search_ingredients(name, _):
    if not name or len(name.strip()) < 2:
        return [], error_alert("Saisissez au moins 2 caractères.", "info")
    results = search_by_name(name)
    if not results:
        return [], error_alert(f"Aucun produit trouvé pour « {name} ».")
    return results, None


@callback(
    Output("rec-name-results", "children"),
    Input("rec-search-results", "data"),
)
def render_search_results(results):
    return search_results_list(results, "rec-result")


@callback(
    Output("rec-candidate", "data", allow_duplicate=True),
    Output({"type": "rec-result", "index": ALL}, "active"),
    Input({"type": "rec-result", "index": ALL}, "n_clicks"),
    State("rec-search-results", "data"),
    prevent_initial_call=True,
)
def select_search_result(clicks, results):
    index = clicked_index()
    if index is None or not results:
        return no_update, [no_update] * len(clicks)
    return results[index], [i == index for i in range(len(clicks))]


@callback(
    Output("rec-candidate", "data", allow_duplicate=True),
    Output("rec-barcode-status", "children"),
    Input("rec-barcode-btn", "n_clicks"),
    Input("rec-barcode-input", "n_submit"),
    State("rec-barcode-input", "value"),
    prevent_initial_call=True,
)
def select_from_barcode(_, __, barcode):
    if not barcode or not barcode.strip():
        return no_update, error_alert("Veuillez saisir un code-barres.", "info")
    product = search_by_barcode(barcode.strip())
    if not product:
        return None, error_alert(f"Aucun produit trouvé pour le code {barcode}.")
    return product, None


@callback(
    Output("rec-candidate", "data", allow_duplicate=True),
    Output("rec-image-status", "children"),
    Input("rec-upload", "contents"),
    Input("rec-webcam-btn", "n_clicks"),
    prevent_initial_call=True,
)
def select_from_image(contents, _):
    if dash.ctx.triggered_id == "rec-webcam-btn":
        barcode, error = scan_barcode_with_webcam()
    else:
        barcode = decode_barcode_from_upload(contents) if contents else None
        error = None if barcode else "Aucun code-barres détecté. Essayez une photo plus nette."
    if not barcode:
        return no_update, error_alert(error)
    product = search_by_barcode(barcode)
    if not product:
        return None, error_alert(f"Code-barres {barcode} détecté, mais produit introuvable.")
    return product, dbc.Alert(f"Code-barres détecté : {barcode}", color="success", className="mt-2 mb-0")


@callback(
    Output("rec-preview", "children"),
    Output("rec-add-btn", "disabled"),
    Input("rec-candidate", "data"),
)
def show_candidate(product):
    return product_summary_card(product), not product


# ---------------------------------------------------------------- Gestion de la liste

@callback(
    Output("rec-ingredients", "data", allow_duplicate=True),
    Output("rec-add-msg", "children"),
    Output("rec-candidate", "data", allow_duplicate=True),
    Input("rec-add-btn", "n_clicks"),
    State("rec-candidate", "data"),
    State("rec-quantity", "value"),
    State("rec-ingredients", "data"),
    prevent_initial_call=True,
)
def add_ingredient(_, product, quantity, ingredients):
    if not product:
        return no_update, no_update, no_update
    quantity = to_float(quantity, 100)
    if quantity <= 0:
        return no_update, error_alert("La quantité doit être positive."), no_update
    ingredient = dict(product, quantity=quantity)
    message = dbc.Alert(f"{product['product_name']} ({quantity:g} g) ajouté à la recette.",
                        color="success", duration=3000, className="mt-2 mb-0")
    return (ingredients or []) + [ingredient], message, None


@callback(
    Output("rec-ingredients", "data", allow_duplicate=True),
    Input("rec-clear-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_recipe(_):
    return []


def _ingredient_card(i, ingredient):
    name = ingredient.get("product_name", "Ingrédient")
    warning = None if has_nutrition_data(ingredient) else html.Small(
        "Pas de données nutritionnelles pour ce produit.", className="text-danger d-block")
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.Button(html.I(className="fas fa-times"), id={"type": "rec-remove", "index": i},
                    className="btn btn-sm btn-outline-danger position-absolute top-0 end-0 m-2",
                    title="Retirer"),
        html.Div(html.Img(src=ingredient["image_url"], className="ingredient-thumb"),
                 className="text-center mb-2") if ingredient.get("image_url") else None,
        html.H6(name, className="pe-4"),
        html.Div([f"{to_float(ingredient.get('quantity')):g} g · Nutri-Score ",
                  nutriscore_badge(ingredient.get("nutriscore_grade"))], className="mb-1"),
        warning,
        html.Details([
            html.Summary("Alternative plus saine", className="small text-success"),
            dbc.InputGroup([
                dbc.Input(id={"type": "rec-alt-keyword", "index": i}, size="sm",
                          value=" ".join(name.split()[:2])),
                dbc.Button("Chercher", id={"type": "rec-alt-search", "index": i}, size="sm",
                           color="success"),
            ], className="mt-2 mb-2"),
            dcc.Loading(dcc.Dropdown(id={"type": "rec-alt-select", "index": i},
                                     placeholder="Choisir une alternative…", optionHeight=50)),
            dbc.Button("Remplacer", id={"type": "rec-alt-replace", "index": i}, size="sm",
                       color="warning", className="mt-2"),
        ], className="mt-2"),
    ]), className="h-100 position-relative"), md=6, lg=4, className="mb-3")


@callback(
    Output("rec-ingredients-list", "children"),
    Output("rec-analyze-btn", "disabled"),
    Input("rec-ingredients", "data"),
)
def render_ingredients(ingredients):
    if not ingredients:
        return html.P("Aucun ingrédient pour le moment.", className="text-muted"), True
    total = sum(to_float(i.get("quantity")) for i in ingredients)
    return html.Div([
        dbc.Row([_ingredient_card(i, ing) for i, ing in enumerate(ingredients)]),
        html.P(f"{len(ingredients)} ingrédient(s) – poids total : {total:g} g", className="text-muted mb-0"),
    ]), False


@callback(
    Output("rec-ingredients", "data", allow_duplicate=True),
    Input({"type": "rec-remove", "index": ALL}, "n_clicks"),
    State("rec-ingredients", "data"),
    prevent_initial_call=True,
)
def remove_ingredient(_, ingredients):
    index = clicked_index()
    if index is None or not ingredients:
        return no_update
    return [ing for i, ing in enumerate(ingredients) if i != index]


@callback(
    Output({"type": "rec-alt-select", "index": MATCH}, "options"),
    Input({"type": "rec-alt-search", "index": MATCH}, "n_clicks"),
    State({"type": "rec-alt-keyword", "index": MATCH}, "value"),
    State("rec-ingredients", "data"),
    prevent_initial_call=True,
)
def search_alternatives(_, keyword, ingredients):
    index = dash.ctx.triggered_id["index"]
    if not keyword or not ingredients or index >= len(ingredients):
        return []
    alternatives = find_healthier_alternatives(ingredients[index], keyword)
    if not alternatives:
        return [{"label": "Aucune alternative mieux notée trouvée", "value": "", "disabled": True}]
    return [product_option(p) for p in alternatives]


@callback(
    Output("rec-ingredients", "data", allow_duplicate=True),
    Input({"type": "rec-alt-replace", "index": ALL}, "n_clicks"),
    State({"type": "rec-alt-select", "index": ALL}, "value"),
    State({"type": "rec-alt-select", "index": ALL}, "id"),
    State("rec-ingredients", "data"),
    prevent_initial_call=True,
)
def replace_ingredient(_, values, ids, ingredients):
    index = clicked_index()
    if index is None or not ingredients:
        return no_update
    selected = {id_["index"]: value for id_, value in zip(ids, values)}.get(index)
    if not selected:
        return no_update
    updated = list(ingredients)
    updated[index] = dict(json.loads(selected), quantity=ingredients[index].get("quantity", 100))
    return updated


# ---------------------------------------------------------------- Analyse

@callback(
    Output("rec-results", "children"),
    Input("rec-analyze-btn", "n_clicks"),
    State("rec-ingredients", "data"),
    State("rec-title", "value"),
    State("rec-servings", "value"),
    prevent_initial_call=True,
)
def analyze_recipe(_, ingredients, title, servings):
    if not ingredients:
        return no_update
    title = title or "Ma recette"
    servings = max(int(to_float(servings, 1)), 1)

    result = compute_recipe_totals(ingredients)
    totals, per_100g = result["totals"], result["per_100g"]
    per_serving = {k: v / servings for k, v in totals.items()}
    grade = calculate_nutriscore(per_100g)

    # Répartition des calories par ingrédient
    labels = [i.get("product_name", "?")[:40] for i in ingredients]
    calories = [to_float(i.get("energy")) * to_float(i.get("quantity")) / 100 for i in ingredients]
    pie = go.Figure(go.Pie(labels=labels, values=calories, hole=0.45, textinfo="percent"))
    pie.update_layout(title="Origine des calories", height=360, margin=dict(l=10, r=10, t=50, b=10),
                      legend=dict(orientation="h", y=-0.1))

    missing = [i.get("product_name") for i in ingredients if not has_nutrition_data(i)]

    return dbc.Card(dbc.CardBody([
        html.H3(f"Analyse de « {title} »", className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.H5("Nutri-Score de la recette"),
                nutriscore_scale(grade),
                html.Small("Calculé sur la composition moyenne pour 100 g de recette.",
                           className="text-muted d-block mb-3"),
                html.Div([html.Span(f"{per_serving['energy']:.0f}", className="display-6 fw-bold"),
                          html.Span(" kcal par portion", className="text-muted")]),
                html.P(f"{servings} portion(s) · {result['total_weight']:g} g au total · "
                       f"{result['total_weight'] / servings:.0f} g par portion", className="text-muted"),
                dbc.Alert(["Données manquantes pour : ", ", ".join(missing)], color="warning")
                if missing else None,
            ], md=5),
            dbc.Col(dcc.Graph(figure=pie, config={"displayModeBar": False}), md=7),
        ]),
        html.H5("Valeurs nutritionnelles", className="mt-3"),
        nutrition_table([("Recette entière", totals), ("Pour 100 g", per_100g),
                         ("Par portion", per_serving)]),
    ]))
