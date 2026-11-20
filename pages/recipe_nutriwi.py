"""
Page « Idées recettes » : catalogue paginé de recettes saines avec leur Nutri-Score.
"""
import math

import dash
from dash import Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc

from components.ui import nutriscore_badge
from utils.recipes_data import RECIPES

dash.register_page(__name__, path="/recipes", title="GreenBite - Idées recettes", name="Idées recettes")

PAGE_SIZE = 6
TOTAL_PAGES = math.ceil(len(RECIPES) / PAGE_SIZE)


def _recipe_card(recipe):
    return dbc.Col(dbc.Card([
        dbc.CardImg(src=dash.get_asset_url(recipe["image"]), top=True, className="recipe-card-img"),
        dbc.CardBody([
            html.H5(recipe["title"], className="card-title"),
            html.Div(["Nutri-Score ", nutriscore_badge(recipe["nutriscore"])], className="mb-2"),
            dbc.Button("Voir la recette", href=f"/recipe-details?recipe={recipe['slug']}", color="success"),
        ]),
    ], className="h-100"), md=4, sm=6, className="mb-4")


layout = html.Div([
    html.H1("Idées recettes", className="text-center mb-2"),
    html.P("Des recettes saines et équilibrées, avec leur Nutri-Score.", className="text-center text-muted mb-4"),
    dcc.Store(id="recipes-page", data=0),
    html.Div(id="recipes-grid"),
    html.Div([
        dbc.Button("Précédent", id="recipes-prev", color="primary", className="me-2"),
        html.Span(id="recipes-page-info", className="mx-3"),
        dbc.Button("Suivant", id="recipes-next", color="primary", className="ms-2"),
    ], className="d-flex justify-content-center align-items-center mb-4"),
])


@callback(
    Output("recipes-grid", "children"),
    Output("recipes-prev", "disabled"),
    Output("recipes-next", "disabled"),
    Output("recipes-page-info", "children"),
    Output("recipes-page", "data"),
    Input("recipes-prev", "n_clicks"),
    Input("recipes-next", "n_clicks"),
    State("recipes-page", "data"),
)
def update_page(_, __, page):
    page = page or 0
    if dash.ctx.triggered_id == "recipes-next":
        page = min(page + 1, TOTAL_PAGES - 1)
    elif dash.ctx.triggered_id == "recipes-prev":
        page = max(page - 1, 0)

    subset = RECIPES[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    return (
        dbc.Row([_recipe_card(r) for r in subset]),
        page == 0,
        page >= TOTAL_PAGES - 1,
        f"Page {page + 1} / {TOTAL_PAGES}",
        page,
    )
