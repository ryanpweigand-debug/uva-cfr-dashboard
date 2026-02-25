"""
Recommendations Page — CFR action registry with priority, value, and timeline.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "components"))

from queries import load_recommendations, load_partners
from charts import (
    UVA_NAVY, UVA_ORANGE, LIGHT_BG, CARD_BG, TEXT_DARK, TEXT_MID, TEXT_LIGHT,
    GRID_COLOR, BORDER, CHART_FONT, chart_layout,
)

dash.register_page(__name__, path="/recommendations", name="Recommendations", order=5)

PRIORITY_COLORS = {"High": "#C62828", "Medium": UVA_ORANGE, "Low": "#2E7D32"}
STATUS_COLORS   = {"Open": "#1565C0", "In Progress": UVA_ORANGE, "Closed": "#2E7D32"}
CATEGORY_COLORS = {
    "Research":    UVA_NAVY,
    "Philanthropy":"#6A1B9A",
    "Talent":      "#2E7D32",
    "Strategic":   UVA_ORANGE,
    "Procurement": "#C62828",
}
CATEGORIES  = ["All", "Research", "Philanthropy", "Talent", "Strategic", "Procurement"]
PRIORITIES  = ["All", "High", "Medium", "Low"]
STATUSES    = ["All", "Open", "In Progress", "Closed"]


def rec_summary_chart(recs):
    grp = recs.groupby(["category","priority"]).size().reset_index(name="count")
    fig = px.bar(
        grp, x="category", y="count", color="priority",
        color_discrete_map=PRIORITY_COLORS,
        barmode="stack",
        labels={"count": "# Recommendations", "category": "Category"},
    )
    fig.update_layout(**chart_layout("Recommendations by Category and Priority", height=320))
    return fig


def value_by_category_chart(recs):
    grp = recs.groupby("category")["est_value_k"].sum().sort_values(ascending=True)
    colors = [CATEGORY_COLORS.get(c, "#999") for c in grp.index]
    fig = go.Figure(go.Bar(
        x=grp.values / 1000, y=grp.index, orientation="h",
        marker_color=colors,
        text=[f"${v/1000:.1f}M" if v >= 1000 else f"${v:.0f}K" for v in grp.values],
        textposition="outside",
        hovertemplate="%{y}: $%{x:.2f}M<extra></extra>",
    ))
    lo = chart_layout("Estimated Value by Category ($M)", height=280)
    lo["xaxis"]["title"] = "$ Millions"
    fig.update_layout(**lo)
    return fig


def timeline_chart(recs):
    recs_t = recs[recs["timeline"].notna() & (recs["timeline"] != "")].copy()
    fig = go.Figure()
    for pri, color in PRIORITY_COLORS.items():
        sub = recs_t[recs_t["priority"] == pri]
        fig.add_trace(go.Scatter(
            x=sub["timeline"],
            y=sub["title"].str[:40],
            mode="markers",
            marker=dict(size=12, color=color, symbol="circle",
                        line=dict(width=1, color="#fff")),
            name=pri,
            hovertemplate="<b>%{y}</b><br>Timeline: %{x}<extra></extra>",
        ))
    lo = chart_layout("Recommendation Timeline", height=max(300, len(recs_t)*18+80))
    lo["xaxis"]["categoryorder"] = "category ascending"
    fig.update_layout(**lo)
    return fig


def rec_card(row, partners_df):
    partner_name = None
    if pd.notna(row.get("partner_id")) and row["partner_id"]:
        pm = partners_df[partners_df["id"] == int(row["partner_id"])]
        if not pm.empty:
            partner_name = pm.iloc[0]["name"]

    pc = PRIORITY_COLORS.get(row["priority"], "#999")
    sc = STATUS_COLORS.get(row["status"], "#999")
    cc = CATEGORY_COLORS.get(row["category"], "#999")
    val = row["est_value_k"]
    val_str = f"${val/1000:.1f}M" if val >= 1000 else (f"${val:.0f}K" if val > 0 else "—")

    return html.Div([
        html.Div([
            html.Div([
                html.Span(row["category"], className="rec-category",
                          style={"color": cc, "borderColor": cc}),
                html.Span(row["priority"], className="priority-badge ms-2",
                          style={"background": pc, "color": "#fff"}),
                html.Span(row["status"], className="status-badge ms-2",
                          style={"border": f"1px solid {sc}", "color": sc}),
            ]),
            html.Div(val_str, className="rec-value"),
        ], className="rec-header d-flex justify-content-between align-items-start"),
        html.Div(row["title"], className="rec-title"),
        html.Div(row.get("description",""), className="rec-desc"),
        html.Div([
            html.Span(f"🎯 {row.get('timeline','—')}", className="rec-meta me-3"),
            html.Span(f"🏢 {partner_name}", className="rec-meta") if partner_name
            else html.Span("🌐 Portfolio-wide", className="rec-meta text-muted"),
        ], className="mt-2"),
    ], className="rec-card", style={"borderLeft": f"3px solid {pc}"})


# ── Layout ─────────────────────────────────────────────────────────────────────
layout = html.Div([
    html.Div([
        html.H2("Recommendations", className="page-title"),
        html.P(
            "CFR action registry — prioritized recommendations across research, talent, "
            "philanthropy, strategic initiatives, and procurement. Tracked by value, "
            "timeline, and status.",
            className="page-subtitle"
        ),
    ], className="page-header"),

    # KPIs
    html.Div(id="rec-kpis", className="mb-3"),

    # Filters
    dbc.Row([
        dbc.Col([
            dbc.Label("Filter by Category", className="dropdown-label"),
            dcc.Dropdown(
                id="rec-cat-dd",
                options=[{"label": c, "value": c} for c in CATEGORIES],
                value="All", clearable=False, className="cfr-dropdown",
            ),
        ], md=3),
        dbc.Col([
            dbc.Label("Filter by Priority", className="dropdown-label"),
            dcc.Dropdown(
                id="rec-pri-dd",
                options=[{"label": p, "value": p} for p in PRIORITIES],
                value="All", clearable=False, className="cfr-dropdown",
            ),
        ], md=3),
        dbc.Col([
            dbc.Label("Filter by Status", className="dropdown-label"),
            dcc.Dropdown(
                id="rec-status-dd",
                options=[{"label": s, "value": s} for s in STATUSES],
                value="All", clearable=False, className="cfr-dropdown",
            ),
        ], md=3),
    ], className="filter-row mb-3"),

    # Charts
    dbc.Row([
        dbc.Col([
            html.Div([dcc.Graph(id="rec-summary-chart", config={"displayModeBar": False})],
                     className="chart-card"),
        ], md=5),
        dbc.Col([
            html.Div([dcc.Graph(id="rec-value-chart", config={"displayModeBar": False})],
                     className="chart-card"),
        ], md=4),
        dbc.Col([
            html.Div([dcc.Graph(id="rec-timeline", config={"displayModeBar": False})],
                     className="chart-card"),
        ], md=3),
    ], className="mb-3"),

    # Cards
    html.Div("RECOMMENDATION REGISTRY", className="section-eyebrow mb-3"),
    html.Div(id="rec-cards-container"),

], className="cfr-page")


@callback(
    Output("rec-summary-chart",    "figure"),
    Output("rec-value-chart",      "figure"),
    Output("rec-timeline",         "figure"),
    Output("rec-cards-container",  "children"),
    Output("rec-kpis",             "children"),
    Input("rec-cat-dd",    "value"),
    Input("rec-pri-dd",    "value"),
    Input("rec-status-dd", "value"),
)
def update_recs(cat, pri, status):
    recs   = load_recommendations()
    df_raw = load_partners()

    recs_f = recs.copy()
    if cat    != "All": recs_f = recs_f[recs_f["category"] == cat]
    if pri    != "All": recs_f = recs_f[recs_f["priority"] == pri]
    if status != "All": recs_f = recs_f[recs_f["status"]   == status]

    total_val = recs_f["est_value_k"].sum()
    high_ct   = (recs_f["priority"] == "High").sum()
    open_ct   = (recs_f["status"]   == "Open").sum()
    ip_ct     = (recs_f["status"]   == "In Progress").sum()

    kpis = dbc.Row([
        dbc.Col(html.Div([
            html.Div(str(len(recs_f)), className="stat-value", style={"color": UVA_NAVY}),
            html.Div("Total Recommendations", className="stat-label"),
        ], className="stat-card"), md=3),
        dbc.Col(html.Div([
            html.Div(str(high_ct), className="stat-value", style={"color": "#C62828"}),
            html.Div("High Priority", className="stat-label"),
        ], className="stat-card"), md=3),
        dbc.Col(html.Div([
            html.Div(f"${total_val/1000:.1f}M" if total_val >= 1000 else f"${total_val:.0f}K",
                     className="stat-value", style={"color": "#2E7D32"}),
            html.Div("Est. Total Value", className="stat-label"),
        ], className="stat-card"), md=3),
        dbc.Col(html.Div([
            html.Div(str(ip_ct), className="stat-value", style={"color": UVA_ORANGE}),
            html.Div("In Progress", className="stat-label"),
        ], className="stat-card"), md=3),
    ])

    cards = dbc.Row([
        dbc.Col(rec_card(row, df_raw), md=6, className="mb-3")
        for _, row in recs_f.iterrows()
    ]) if not recs_f.empty else html.Div("No recommendations match the selected filters.",
                                         className="placeholder-text")

    return (
        rec_summary_chart(recs),
        value_by_category_chart(recs),
        timeline_chart(recs_f),
        cards,
        kpis,
    )
