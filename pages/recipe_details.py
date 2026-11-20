"""
Page de détail d'une recette : /recipe-details?recipe=<slug>
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

from components.ui import nutriscore_scale
from utils.recipes_data import RECIPES_BY_SLUG

dash.register_page(__name__, path="/recipe-details", title="GreenBite - Recette", name="Détails de la recette")


def layout(recipe=None, **_):
    """Dash Pages transmet les paramètres de l'URL (?recipe=...) en arguments."""
    data = RECIPES_BY_SLUG.get(recipe or "")
    if not data:
        return html.Div([
            html.H1("Recette introuvable", className="text-center mb-4"),
            html.Div(dbc.Button("Voir toutes les recettes", href="/recipes", color="primary"),
                     className="text-center"),
        ])

    return html.Div([
        dbc.Button([html.I(className="fas fa-arrow-left me-2"), "Toutes les recettes"],
                   href="/recipes", color="link", className="mb-2 p-0"),
        html.H1(data["title"], className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.Img(src=dash.get_asset_url(data["image"]), className="img-fluid rounded mb-3"),
                html.H5("Nutri-Score"),
                nutriscore_scale(data["nutriscore"]),
                html.A([html.I(className="fas fa-external-link-alt me-1"), "Recette originale sur NutriWi"],
                       href=data["source_url"], target="_blank") if data["source_url"] else None,
            ], md=5),
            dbc.Col([
                html.H3("Ingrédients"),
                html.Ul([html.Li(item) for item in data["ingredients"]], className="mb-4"),
                html.H3("Préparation"),
                html.Ol([html.Li(step, className="mb-2") for step in data["steps"]]),
            ], md=7),
        ]),
    ])
