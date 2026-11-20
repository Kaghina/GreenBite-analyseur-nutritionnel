"""
Barre de navigation commune à toutes les pages.
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

LINKS = [
    ("Accueil", "/"),
    ("Analyse Produit", "/analyzer"),
    ("Analyse Recette", "/recipe-analyzer"),
    ("Idées recettes", "/recipes"),
    ("En savoir plus", "/learn-more"),
]


def create_navbar():
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand(
                [html.Img(src=dash.get_asset_url("greenbite-logo.png"), className="app-logo"), "GreenBite"],
                href="/", className="d-flex align-items-center",
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav([dbc.NavItem(dbc.NavLink(label, href=href, active="exact")) for label, href in LINKS],
                        className="ms-auto", navbar=True),
                id="navbar-collapse", navbar=True,
            ),
        ]),
        dark=True,
        className="navbar mb-4",
    )


# Ouverture/fermeture du menu sur petit écran (sans aller-retour serveur)
dash.clientside_callback(
    "function(n, isOpen) { return n ? !isOpen : isOpen; }",
    dash.Output("navbar-collapse", "is_open"),
    dash.Input("navbar-toggler", "n_clicks"),
    dash.State("navbar-collapse", "is_open"),
    prevent_initial_call=True,
)
