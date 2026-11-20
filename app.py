"""
Point d'entrée de l'application GreenBite.

Lancement :  python app.py   puis ouvrir http://127.0.0.1:8050
"""
import logging
import os

import dash
from dash import html
import dash_bootstrap_components as dbc

from components.footer import create_footer
from components.navbar import create_navbar

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = dash.Dash(
    __name__,
    use_pages=True,
    title="GreenBite - Pour des choix alimentaires sains",
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap",
    ],
)
server = app.server  # pour un éventuel déploiement (gunicorn app:server)

app.layout = html.Div([
    create_navbar(),
    html.Main(dash.page_container, id="page-content", className="container"),
    create_footer(),
], className="app-wrapper")


if __name__ == "__main__":
    debug = os.environ.get("GREENBITE_DEBUG", "1") == "1"
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=debug, port=port)
