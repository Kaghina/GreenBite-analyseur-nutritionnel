import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    path="/learn-more",
    title="Principes d'une alimentation saine",
    name="En savoir plus"
)

layout = html.Div([
    # Header Section
    html.Div([
        html.H1("🥗 Les principes d'une alimentation saine et équilibrée", className="text-center mb-4"),
        html.P(
            "Adopter une alimentation saine et équilibrée, c’est offrir à son corps l’énergie ⚡ et les nutriments "
            "dont il a besoin pour bien fonctionner au quotidien. Ce mode de vie alimentaire favorise la prévention "
            "de nombreuses maladies 🛡️ (diabète, maladies cardiovasculaires, obésité…) et contribue à une meilleure "
            "forme physique et mentale 🧠💪.",
            className="lead text-center"
        )
    ], className="container mt-4 mb-5"),

    # Main Content Section
    html.Div([
        dbc.Row([
            # Card: Les grands principes
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H3("🍽️ Les grands principes d’une alimentation équilibrée")),
                    dbc.CardBody([
                        html.Ul([
                            html.Li("La variété avant tout 🌈 : Mangez de tout pour obtenir tous les éléments essentiels."),
                            html.Li("Des repas structurés ⏰ : Trois repas principaux et une collation si nécessaire."),
                            html.Li("Fruits et légumes à volonté 🥕🍇 : Remplissez la moitié de votre assiette."),
                            html.Li("Privilégier les bons gras 🐟🌰 : Favorisez les acides gras insaturés."),
                            html.Li("Limiter les sucres ajoutés, le sel et les produits ultra-transformés 🚫🍭."),
                        ], className="mb-0")
                    ])
                ], className="mb-4")
            ], md=6),

            # Card: Comment lire une analyse nutritionnelle
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H3("🔍 Comment lire une analyse nutritionnelle ?")),
                    dbc.CardBody([
                        html.P("L’étiquette nutritionnelle des produits 🏷️ est un outil précieux pour faire des choix éclairés."),
                        html.Ul([
                            html.Li("Énergie (kcal ou kJ) ⚡ : Quantité d’énergie apportée."),
                            html.Li("Lipides (dont acides gras saturés) 🧈 : À consommer avec modération."),
                            html.Li("Glucides (dont sucres) 🍬 : Attention aux sucres simples cachés !"),
                            html.Li("Protéines 🍳 : Essentielles pour les muscles et l’organisme."),
                            html.Li("Fibres 🌿 : Favorisent la digestion et la satiété."),
                            html.Li("Sel (sodium) 🧂 : À surveiller, surtout dans les plats préparés."),
                        ], className="mb-0")
                    ])
                ], className="mb-4")
            ], md=6),
        ])
    ], className="container"),

    # Summary Section
    html.Div([
        dbc.Card([
            dbc.CardHeader(html.H3("✅ En résumé")),
            dbc.CardBody([
                html.P(
                    "Une alimentation saine repose sur la diversité, la modération et le bon sens 🧭. Écoute ton corps 🫀, "
                    "lis les étiquettes 🏷️ et favorise le fait-maison 🍲. L’objectif n’est pas de se priver, mais de construire "
                    "des habitudes durables 🌱, adaptées à ton rythme de vie.",
                    className="mb-0"
                )
            ])
        ], className="mb-5")
    ], className="container"),

    # Footer Section
    html.Div([
        dbc.Button("Retour à l'accueil", href="/", color="primary", className="mt-3")
    ], className="text-center mb-5")
])