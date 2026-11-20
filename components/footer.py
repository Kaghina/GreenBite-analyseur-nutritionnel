"""
Pied de page commun à toutes les pages.
"""
from dash import html


def create_footer():
    return html.Footer(
        html.Div([
            html.Div([
                html.H5("GreenBite", className="text-white"),
                html.P("Pour des choix alimentaires sains et éclairés", className="mb-1"),
                html.Small(
                    "Réalisé par Kahina Ait Kaci Arab, Farid Ait Salem, Ilicia Benaoudia et Leticia Benaoudia",
                    className="d-block",
                ),
            ], className="col-md-6"),
            html.Div([
                html.P([
                    "Données : ",
                    html.A("OpenFoodFacts", href="https://world.openfoodfacts.org", target="_blank"),
                    " et ",
                    html.A("table CIQUAL (ANSES)", href="https://ciqual.anses.fr", target="_blank"),
                ], className="mb-0"),
            ], className="col-md-6 d-flex align-items-center justify-content-md-end"),
        ], className="container row mx-auto"),
        className="footer",
    )
