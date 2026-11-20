"""
Page « Analyse Produit » : recherche d'un produit (nom, code-barres, image ou webcam)
puis affichage de son Nutri-Score et de sa composition nutritionnelle.
"""
import dash
from dash import ALL, Input, Output, State, callback, dcc, html, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from components.ui import (clicked_index, error_alert, nutriscore_scale,
                           nutrition_table, product_summary_card,
                           search_results_list)
from utils.barcode import decode_barcode_from_upload, scan_barcode_with_webcam
from utils.nutrition import NUTRIENTS, to_float
from utils.products import search_by_barcode, search_by_name
from utils.theme import GREENBITE_COLORS

dash.register_page(__name__, path="/analyzer", title="GreenBite - Analyse Produit", name="Analyse Produit")


def _search_tabs():
    return dbc.Tabs(
        [
            dbc.Tab(label="Par nom", tab_id="name", children=html.Div([
                html.P("Recherche dans OpenFoodFacts (produits du commerce) et CIQUAL (aliments de base).",
                       className="text-muted"),
                dbc.InputGroup([
                    dbc.Input(id="prod-name-input", placeholder="Ex : yaourt nature, pomme, Nutella…",
                              debounce=True, type="text"),
                    dbc.Button([html.I(className="fas fa-search me-2"), "Rechercher"],
                               id="prod-name-btn", color="success"),
                ]),
                dcc.Loading([
                    dcc.Store(id="prod-search-results"),
                    html.Div(id="prod-name-status"),
                    html.Div(id="prod-name-results"),
                ]),
            ], className="p-3")),
            dbc.Tab(label="Par code-barres", tab_id="barcode", children=html.Div([
                html.P("Saisissez le code EAN imprimé sous le code-barres.", className="text-muted"),
                dbc.InputGroup([
                    dbc.Input(id="prod-barcode-input", placeholder="Ex : 3017620422003", type="text"),
                    dbc.Button("Rechercher", id="prod-barcode-btn", color="success"),
                ]),
                dcc.Loading(html.Div(id="prod-barcode-status")),
            ], className="p-3")),
            dbc.Tab(label="Par image / webcam", tab_id="image", children=html.Div([
                dcc.Upload(
                    id="prod-upload",
                    children=html.Div([html.I(className="fas fa-upload me-2"),
                                       "Cliquez ou déposez une photo de code-barres"]),
                    className="upload-box", multiple=False, accept="image/*",
                ),
                html.Div("ou", className="text-center text-muted my-2"),
                dbc.Button([html.I(className="fas fa-camera me-2"), "Scanner avec la webcam"],
                           id="prod-webcam-btn", color="success", className="w-100"),
                html.Small("Une fenêtre de caméra s'ouvre ; présentez le code-barres (Q pour annuler).",
                           className="text-muted d-block mt-1"),
                dcc.Loading(html.Div(id="prod-image-status")),
            ], className="p-3")),
        ],
        active_tab="name",
    )


layout = html.Div([
    html.H1("Analyse de produits", className="text-center mb-4"),
    dcc.Store(id="prod-candidate"),

    dbc.Card(dbc.CardBody([
        _search_tabs(),
        html.Div(id="prod-preview", className="mt-3"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Portion (g)"),
                dbc.Input(id="prod-weight", type="number", min=1, value=100),
            ], md=4),
            dbc.Col(
                dbc.Button([html.I(className="fas fa-chart-bar me-2"), "Analyser le produit"],
                           id="prod-analyze-btn", color="primary", className="w-100", disabled=True),
                md=8, className="d-flex align-items-end",
            ),
        ], className="mt-2"),
    ]), className="mb-4"),

    dcc.Loading(html.Div(id="prod-results")),
])


# ---------------------------------------------------------------- Recherche

@callback(
    Output("prod-search-results", "data"),
    Output("prod-name-status", "children"),
    Input("prod-name-input", "value"),
    Input("prod-name-btn", "n_clicks"),
    prevent_initial_call=True,
)
def search_products_by_name(name, _):
    if not name or len(name.strip()) < 2:
        return [], error_alert("Saisissez au moins 2 caractères.", "info")
    results = search_by_name(name)
    if not results:
        return [], error_alert(f"Aucun produit trouvé pour « {name} ».")
    return results, None


@callback(
    Output("prod-name-results", "children"),
    Input("prod-search-results", "data"),
)
def render_search_results(results):
    return search_results_list(results, "prod-result")


@callback(
    Output("prod-candidate", "data", allow_duplicate=True),
    Output({"type": "prod-result", "index": ALL}, "active"),
    Input({"type": "prod-result", "index": ALL}, "n_clicks"),
    State("prod-search-results", "data"),
    prevent_initial_call=True,
)
def select_search_result(clicks, results):
    index = clicked_index()
    if index is None or not results:
        return no_update, [no_update] * len(clicks)
    return results[index], [i == index for i in range(len(clicks))]


@callback(
    Output("prod-candidate", "data", allow_duplicate=True),
    Output("prod-barcode-status", "children"),
    Input("prod-barcode-btn", "n_clicks"),
    Input("prod-barcode-input", "n_submit"),
    State("prod-barcode-input", "value"),
    prevent_initial_call=True,
)
def select_product_from_barcode(_, __, barcode):
    if not barcode or not barcode.strip():
        return no_update, error_alert("Veuillez saisir un code-barres.", "info")
    product = search_by_barcode(barcode.strip())
    if not product:
        return None, error_alert(f"Aucun produit trouvé pour le code {barcode}.")
    return product, None


@callback(
    Output("prod-candidate", "data", allow_duplicate=True),
    Output("prod-image-status", "children"),
    Input("prod-upload", "contents"),
    Input("prod-webcam-btn", "n_clicks"),
    prevent_initial_call=True,
)
def select_product_from_image(contents, _):
    if dash.ctx.triggered_id == "prod-webcam-btn":
        barcode, error = scan_barcode_with_webcam()
    else:
        barcode = decode_barcode_from_upload(contents) if contents else None
        error = None if barcode else "Aucun code-barres détecté. Essayez une photo plus nette et bien éclairée."
    if not barcode:
        return no_update, error_alert(error)

    product = search_by_barcode(barcode)
    if not product:
        return None, error_alert(f"Code-barres {barcode} détecté, mais produit introuvable.")
    return product, dbc.Alert(f"Code-barres détecté : {barcode}", color="success", className="mt-2 mb-0")


@callback(
    Output("prod-preview", "children"),
    Output("prod-analyze-btn", "disabled"),
    Output("prod-results", "children", allow_duplicate=True),
    Input("prod-candidate", "data"),
    prevent_initial_call=True,
)
def show_candidate(product):
    # Un nouveau produit efface les résultats de l'analyse précédente
    return product_summary_card(product), not product, None


# ---------------------------------------------------------------- Analyse

@callback(
    Output("prod-results", "children"),
    Input("prod-analyze-btn", "n_clicks"),
    State("prod-candidate", "data"),
    State("prod-weight", "value"),
    prevent_initial_call=True,
)
def analyze_product(_, product, weight):
    if not product:
        return no_update
    weight = to_float(weight, 100) or 100
    per_portion = {key: to_float(product.get(key)) * weight / 100 for key, _, _ in NUTRIENTS}

    # Graphique : nutriments en grammes (l'énergie, en kcal, est affichée à part)
    grams = [(label, per_portion[key]) for key, label, unit in NUTRIENTS if unit == "g"]
    fig = go.Figure(go.Bar(
        x=[v for _, v in grams][::-1], y=[label for label, _ in grams][::-1], orientation="h",
        marker_color=GREENBITE_COLORS["success"],
        text=[f"{v:.1f} g" for _, v in grams][::-1], textposition="auto",
    ))
    fig.update_layout(
        title=f"Composition pour {weight:g} g",
        xaxis_title="grammes", height=380, margin=dict(l=10, r=10, t=50, b=40),
        plot_bgcolor="white",
    )

    image = product.get("image_url")
    computed = product.get("nutriscore_computed") or product.get("source") == "CIQUAL"
    return dbc.Card(dbc.CardBody([
        html.H3(product.get("product_name"), className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Img(src=image, className="product-image mb-3") if image else None,
                html.H5("Nutri-Score"),
                nutriscore_scale(product.get("nutriscore_grade")),
                html.Small("Calculé par GreenBite à partir des valeurs nutritionnelles."
                           if computed else "Source : OpenFoodFacts.", className="text-muted d-block mb-3"),
                html.Div([
                    html.Span(f"{per_portion['energy']:.0f}", className="display-6 fw-bold"),
                    html.Span(f" kcal pour {weight:g} g", className="text-muted"),
                ], className="mb-3"),
                html.P([html.Strong("Marque : "), product.get("brands") or "—"], className="mb-1"),
                html.P([html.Strong("Catégorie : "), product.get("categories") or "—"], className="small"),
            ], md=4),
            dbc.Col([
                dcc.Graph(figure=fig, config={"displayModeBar": False}),
                nutrition_table([("Pour 100 g", product), (f"Pour {weight:g} g", per_portion)]),
            ], md=8),
        ]),
    ]))
