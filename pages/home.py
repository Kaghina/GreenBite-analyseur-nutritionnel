"""
Page d'accueil de l'application GreenBite
"""
import dash
from dash import html
import dash_bootstrap_components as dbc
from utils.theme import GREENBITE_COLORS

# Enregistrement de la page
dash.register_page(
    __name__,
    path="/",
    title="GreenBite - Accueil",
    name="Accueil"
)

# Layout de la page d'accueil
layout = html.Div([
    # En-tête/bannière
    html.Div([
        html.H1("Bienvenue sur GreenBite", className="text-center"),
        html.P("Votre assistant pour des choix alimentaires sains et éclairés", className="lead text-center")
    ], className="container mt-4 mb-5"),
    
    # Section des fonctionnalités principales
    html.Div([
        html.H2("Nos fonctionnalités", className="text-center mb-4"),
        
        dbc.Row([
            # Carte pour l'analyse de produit
            dbc.Col([
                dbc.Card([
                    html.Div(
                        dbc.CardImg(src=dash.get_asset_url("analyse-produit.jpg"), className="img-fluid"),
                        className="feature-image-container"
                    ),
                    dbc.CardBody([
                        html.H4("Analyse de Produit", className="card-title"),
                        html.P(
                            "Scannez un code-barres ou recherchez un produit et obtenez une analyse "
                            "nutritionnelle détaillée avec son Nutri-Score.",
                            className="card-text"
                        ),
                        dbc.Button("Analyser un produit", color="primary", href="/analyzer", className="mt-3")
                    ])
                ], className="h-100")
            ], md=4, className="mb-4"),
            
            # Carte pour l'analyse de recette
            dbc.Col([
                dbc.Card([
                    html.Div(
                        dbc.CardImg(src=dash.get_asset_url("analyse-recette.jpg"), className="img-fluid"),
                        className="feature-image-container"
                    ),
                    dbc.CardBody([
                        html.H4("Analyse de Recette", className="card-title"),
                        html.P(
                            "Composez votre recette et obtenez une analyse nutritionnelle complète "
                            "de l'ensemble des ingrédients.",
                            className="card-text"
                        ),
                        dbc.Button("Analyser une recette", color="primary", href="/recipe-analyzer", className="mt-3")
                    ])
                ], className="h-100")
            ], md=4, className="mb-4"),
            
            # Carte pour les ressources
            dbc.Col([
                dbc.Card([
                    html.Div(
                        dbc.CardImg(src=dash.get_asset_url("nutrition.webp"), className="img-fluid"),
                        className="feature-image-container"
                    ),
                    dbc.CardBody([
                        html.H4("Comprendre la Nutrition", className="card-title"),
                        html.P(
                            "Découvrez les principes d'une alimentation saine et équilibrée, "
                            "et comment interpréter les analyses nutritionnelles.",
                            className="card-text"
                        ),
                        dbc.Button(
                            "En savoir plus",
                            color="primary",
                            href="/learn-more",
                            className="mt-3"
                        )
                    ])
                ], className="h-100")
            ], md=4, className="mb-4")
        ])
    ], className="container mb-5 feature-cards-container"),
    
    # Section "Comment ça marche"
    html.Div([
        dbc.Row([
            dbc.Col([
                html.H2("Comment ça marche ?", className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-barcode fa-2x mb-3", style={"color": GREENBITE_COLORS['primary']}),
                            html.H4("Scannez", className="mb-3"),
                            html.P("Utilisez votre caméra pour scanner un code-barres ou recherchez un produit par son nom")
                        ], className="text-center")
                    ], md=4),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-chart-pie fa-2x mb-3", style={"color": GREENBITE_COLORS['primary']}),
                            html.H4("Analysez", className="mb-3"),
                            html.P("Notre système calcule automatiquement les valeurs nutritionnelles et le Nutri-Score")
                        ], className="text-center")
                    ], md=4),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-check-circle fa-2x mb-3", style={"color": GREENBITE_COLORS['primary']}),
                            html.H4("Décidez", className="mb-3"),
                            html.P("Faites des choix alimentaires éclairés grâce à nos informations nutritionnelles détaillées")
                        ], className="text-center")
                    ], md=4)
                ])
            ], width=12)
        ])
    ], className="container bg-light p-5 mb-5"),
    
], className="pb-5")