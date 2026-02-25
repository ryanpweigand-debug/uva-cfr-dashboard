"""
UVA CFR Partner Engagement Dashboard
Standalone Dash multi-page application — uses use_pages=True auto-discovery.
Login: admin / CFRDashboard
Port:  8052
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "data"))
sys.path.insert(0, os.path.join(BASE_DIR, "components"))

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
# ── App — must be created BEFORE pages auto-discover ──────────────────────────
app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder=os.path.join(BASE_DIR, "pages"),
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@300;400;600;700"
        "&family=Montserrat:wght@400;600;700;800&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="UVA CFR Partner Engagement Dashboard",
    assets_folder=os.path.join(BASE_DIR, "assets"),
)

# ── Navbar ────────────────────────────────────────────────────────────────────
NAV_LINKS = [
    {"label": "Overview",       "href": "/"},
    {"label": "Partner Scoring","href": "/scoring"},
    {"label": "Strategic Plan", "href": "/strategic-plan"},
    {"label": "Benchmarking",   "href": "/benchmarking"},
    {"label": "Procurement",    "href": "/procurement"},
    {"label": "Recommendations","href": "/recommendations"},
]

navbar = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Div("UVA", className="brand-uva"),
                    html.Div([
                        html.Span("CFR", className="brand-cfr"),
                        html.Span(" Partner Engagement", className="brand-sub"),
                    ], className="ms-2"),
                ], className="brand-block d-flex align-items-center"),
                width="auto",
            ),
            dbc.Col(
                dbc.Nav([
                    dbc.NavItem(
                        dbc.NavLink(
                            lnk["label"], href=lnk["href"],
                            active="partial",
                            className="nav-link-cfr",
                        )
                    )
                    for lnk in NAV_LINKS
                ], navbar=True, className="ms-auto nav-cfr"),
                className="d-flex align-items-center",
            ),
        ], align="center", className="w-100 flex-nowrap"),
    ], fluid=True),
    className="cfr-navbar",
    sticky="top",
)

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    navbar,
    html.Div(
        dash.page_container,
        className="page-wrapper",
    ),
], id="app-root")


# ── DB init & server export (runs on gunicorn import AND local run) ───────────
from data.seed_data import ensure_db
ensure_db()
server = app.server  # gunicorn references this as: gunicorn app:server

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8052))
    app.run(debug=False, port=port, host="0.0.0.0")
