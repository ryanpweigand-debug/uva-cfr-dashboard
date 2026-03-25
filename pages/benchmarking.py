"""
CFR Benchmarking Page — 2025 CFR Benchmarking doc data.
Peer institution analysis with dropdowns and infographic-style comparisons.
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

from queries import load_benchmarks, PPE_STATS
from charts import (
    UVA_NAVY, UVA_ORANGE, LIGHT_BG, CARD_BG, TEXT_DARK, TEXT_MID, TEXT_LIGHT,
    GRID_COLOR, BORDER, CHART_FONT, chart_layout,
)

dash.register_page(__name__, path="/benchmarking", name="CFR Benchmarking", order=3)

MATURITY_COLS = [
    ("specialist_model",       "Specialist Model"),
    ("holistic_front_door",    "Holistic Front Door"),
    ("modern_metrics",         "Modern Metrics"),
    ("crm_infrastructure",     "CRM Infrastructure"),
    ("executive_engagement",   "Executive Engagement"),
    ("cross_campus_alignment", "Cross-Campus Alignment"),
]

TIER_ORDER   = {"Aspirational": 0, "Peer": 1, "Self": 2, "Emerging": 3}
TIER_COLORS  = {
    "Aspirational": UVA_NAVY,
    "Peer":         UVA_ORANGE,
    "Emerging":     "#2E7D32",
    "Self":         "#1565C0",
}


def peer_overview_chart(df):
    df = df[df["tier"] != "Self"].copy()
    df = df.sort_values("annual_research_m", ascending=True)
    colors = [TIER_COLORS.get(t, "#999") for t in df["tier"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Sponsored Research ($M)",
        x=df["annual_research_m"], y=df["institution"],
        orientation="h", marker_color=colors,
        text=[f"${v:.0f}M" for v in df["annual_research_m"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Research: $%{x:.0f}M<extra></extra>",
    ))
    lo = chart_layout("Peer Institutions — Annual Sponsored Research ($M)", height=360)
    lo["xaxis"]["range"] = [0, 380]
    fig.update_layout(**lo)
    return fig


def maturity_radar_chart(df, institutions):
    if not institutions:
        institutions = df["institution"].tolist()
    df_sel = df[df["institution"].isin(institutions)]

    fig = go.Figure()
    colors = [UVA_NAVY, UVA_ORANGE, "#1565C0", "#2E7D32", "#6A1B9A", "#BF360C",
              "#00838F", "#558B2F"]

    labels_full = [l for _, l in MATURITY_COLS]
    cols        = [c for c, _ in MATURITY_COLS]
    cats_closed = labels_full + [labels_full[0]]

    for i, (_, row) in enumerate(df_sel.iterrows()):
        vals = [row[c] for c in cols] + [row[cols[0]]]
        is_uva = "UVA" in row["institution"]
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=cats_closed,
            fill="toself" if is_uva else None,
            fillcolor="rgba(35,45,75,0.1)" if is_uva else None,
            line=dict(color=colors[i % len(colors)],
                      width=3 if is_uva else 1.5,
                      dash="solid" if is_uva else "solid"),
            name=row["institution"],
            hovertemplate=f"{row['institution']}<br>%{{theta}}: %{{r:.1f}}<extra></extra>",
        ))

    fig.update_layout(
        polar=dict(
            bgcolor=LIGHT_BG,
            radialaxis=dict(visible=True, range=[0, 10],
                            tickfont=dict(size=9, color=TEXT_LIGHT),
                            gridcolor=GRID_COLOR),
            angularaxis=dict(tickfont=dict(size=10, color=TEXT_DARK, family=CHART_FONT),
                             gridcolor=GRID_COLOR),
        ),
        paper_bgcolor=CARD_BG, height=420,
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center",
                    font=dict(size=10, family=CHART_FONT)),
        margin=dict(l=60, r=60, t=40, b=80),
        font=dict(family=CHART_FONT),
        title=dict(text="<span style='font-size:13px;font-weight:700'>Corporate Relations Maturity Model</span>",
                   x=0.5, xanchor="center"),
    )
    return fig


def fte_comparison_chart(df):
    fig = go.Figure()
    colors = [TIER_COLORS.get(t, "#999") for t in df["tier"]]
    df_s = df.sort_values("cfr_fte", ascending=True)

    fig.add_trace(go.Bar(
        x=df_s["cfr_fte"], y=df_s["institution"],
        orientation="h",
        marker_color=[TIER_COLORS.get(t, "#999") for t in df_s["tier"]],
        text=[f"{v:.0f} FTE" for v in df_s["cfr_fte"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>CFR FTE: %{x:.0f}<extra></extra>",
    ))
    lo = chart_layout("Corporate Relations Team Size (FTE)", height=340)
    lo["xaxis"]["range"] = [0, 15]
    fig.update_layout(**lo)
    return fig


def maturity_heatmap(df):
    institutions = df["institution"].tolist()
    cols  = [c for c, _ in MATURITY_COLS]
    lbls  = [l for _, l in MATURITY_COLS]
    z = df[cols].values.tolist()

    fig = go.Figure(go.Heatmap(
        z=z, x=lbls, y=institutions,
        colorscale=[[0, "#F7F8FA"], [0.5, "#90CAF9"], [1.0, UVA_NAVY]],
        zmin=0, zmax=10,
        text=[[f"{v:.0f}" for v in row] for row in z],
        texttemplate="%{text}",
        hovertemplate="%{y}<br>%{x}: %{z:.1f}/10<extra></extra>",
        colorbar=dict(title="Score /10", len=0.7, tickfont=dict(size=9)),
    ))
    lo = chart_layout("Maturity Heatmap — All Dimensions (Score / 10)", height=340)
    lo["xaxis"]["tickangle"] = -25
    lo["margin"]["b"] = 100
    fig.update_layout(**lo)
    return fig


def uva_gap_chart(df):
    uva_cur = df[df["institution"] == "UVA (Current)"].iloc[0]
    uva_tar = df[df["institution"] == "UVA (Target)"].iloc[0]
    gt      = df[df["institution"] == "Georgia Tech"].iloc[0]

    cols  = [c for c, _ in MATURITY_COLS]
    lbls  = [l for _, l in MATURITY_COLS]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="UVA Current", x=lbls,
                         y=[uva_cur[c] for c in cols],
                         marker_color=TEXT_LIGHT, opacity=0.8))
    fig.add_trace(go.Bar(name="UVA 3yr Target", x=lbls,
                         y=[uva_tar[c] for c in cols],
                         marker_color=UVA_NAVY))
    fig.add_trace(go.Scatter(name="Georgia Tech (Best-in-Class)", x=lbls,
                              y=[gt[c] for c in cols],
                              mode="lines+markers",
                              line=dict(color=UVA_ORANGE, width=2, dash="dot"),
                              marker=dict(size=8, color=UVA_ORANGE)))

    lo = chart_layout("UVA Gap Analysis vs. Aspirational Benchmark (Georgia Tech)", height=360)
    lo["barmode"] = "group"
    lo["yaxis"]["range"] = [0, 11]
    fig.update_layout(**lo)
    return fig


# ── Layout ─────────────────────────────────────────────────────────────────────
def build_layout():
    df = load_benchmarks()
    all_institutions = df["institution"].tolist()

    return html.Div([
        html.Div([
            html.H2("CFR Benchmarking", className="page-title"),
            html.P(
                "2025 peer institution analysis across 6 maturity dimensions. "
                "Aspirational benchmarks: Georgia Tech (specialist model) and UT-Austin. "
                "Peer benchmark: UNC-Chapel Hill.",
                className="page-subtitle"
            ),
        ], className="page-header"),

        # ── Summary KPIs ───────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(html.Div([
                html.Div("6", className="stat-value", style={"color": UVA_NAVY}),
                html.Div("Peer Institutions", className="stat-label"),
                html.Div("Analyzed 2025", className="stat-sub"),
            ], className="stat-card"), md=2),
            dbc.Col(html.Div([
                html.Div("Georgia Tech", className="stat-value", style={"color": UVA_ORANGE, "fontSize":"1.3rem"}),
                html.Div("Best-in-Class", className="stat-label"),
                html.Div("Specialist-driven model", className="stat-sub"),
            ], className="stat-card"), md=3),
            dbc.Col(html.Div([
                html.Div("12 FTE", className="stat-value", style={"color": UVA_NAVY}),
                html.Div("GT Corporate Relations", className="stat-label"),
                html.Div("vs. UVA current: 6 FTE", className="stat-sub"),
            ], className="stat-card"), md=3),
            dbc.Col(html.Div([
                html.Div("$285M", className="stat-value", style={"color": UVA_ORANGE}),
                html.Div("GT Annual Sponsored Research", className="stat-label"),
                html.Div("UVA Target: $260M (3yr)", className="stat-sub"),
            ], className="stat-card"), md=4),
        ], className="mb-4"),

        # ── Institution Selector ───────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Institutions for Radar", className="dropdown-label"),
                dcc.Dropdown(
                    id="bench-institutions-dd",
                    options=[{"label": i, "value": i} for i in all_institutions],
                    value=all_institutions,
                    multi=True,
                    className="cfr-dropdown",
                    placeholder="Select institutions…",
                ),
            ], md=8),
            dbc.Col([
                dbc.Label("Filter by Tier", className="dropdown-label"),
                dcc.Dropdown(
                    id="bench-tier-dd",
                    options=[{"label": t, "value": t}
                             for t in ["All", "Aspirational", "Peer", "Self", "Emerging"]],
                    value="All", clearable=False, className="cfr-dropdown",
                ),
            ], md=4),
        ], className="filter-row mb-3"),

        # ── Maturity Radar ─────────────────────────────────────────────────────
        html.Div([
            dcc.Graph(id="maturity-radar", config={"displayModeBar": False}),
        ], className="chart-card mb-3"),

        # ── Gap Analysis ───────────────────────────────────────────────────────
        html.Div([
            dcc.Graph(figure=uva_gap_chart(df), config={"displayModeBar": False}),
        ], className="chart-card mb-3"),

        # ── Row: Research bar + FTE comparison ────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Graph(figure=peer_overview_chart(df), config={"displayModeBar": False}),
                ], className="chart-card"),
            ], md=6),
            dbc.Col([
                html.Div([
                    dcc.Graph(figure=fte_comparison_chart(df), config={"displayModeBar": False}),
                ], className="chart-card"),
            ], md=6),
        ], className="mb-3"),

        # ── Maturity Heatmap ──────────────────────────────────────────────────
        html.Div([
            dcc.Graph(figure=maturity_heatmap(df), config={"displayModeBar": False}),
        ], className="chart-card mb-3"),

        # ── Key Insights ─────────────────────────────────────────────────────
        html.Div([
            html.Div("KEY INSIGHTS FROM 2025 BENCHMARKING", className="section-eyebrow mb-3"),
            dbc.Row([
                dbc.Col(insight_card(
                    "🎯", "Specialist-Driven Model",
                    "Georgia Tech and UT-Austin lead with dedicated sector specialists "
                    "(Tech, Defense, Healthcare). UVA CFR opportunity: hire 4 sector leads "
                    "to mirror best-in-class structure (SP-04).",
                    UVA_NAVY,
                ), md=4),
                dbc.Col(insight_card(
                    "🚪", "Holistic Front Door",
                    "Top performers offer a single corporate entry point that coordinates "
                    "research, talent, philanthropy, and marketing simultaneously — eliminating "
                    "fragmented outreach from individual schools (SP-02).",
                    UVA_ORANGE,
                ), md=4),
                dbc.Col(insight_card(
                    "📊", "Modern Metrics",
                    "Peers have moved beyond activity tracking to outcome-based KPIs: "
                    "institutional partnerships, research commercialization, talent placement "
                    "rates, and cross-campus engagement breadth (SP-03).",
                    "#1565C0",
                ), md=4),
            ]),
        ], className="section-block"),

    ], className="cfr-page")


def insight_card(icon, title, body, color):
    return html.Div([
        html.Div([
            html.Span(icon, style={"fontSize": "1.5rem", "marginRight": "8px"}),
            html.Span(title, className="insight-title", style={"color": color}),
        ], className="insight-header"),
        html.Div(body, className="insight-body"),
    ], className="insight-card", style={"borderLeft": f"4px solid {color}"})


layout = build_layout  # callable — Dash calls this lazily at request time


@callback(
    Output("maturity-radar", "figure"),
    Input("bench-institutions-dd", "value"),
    Input("bench-tier-dd", "value"),
)
def update_radar(institutions, tier):
    df = load_benchmarks()
    if tier != "All":
        df = df[df["tier"] == tier]
    return maturity_radar_chart(df, institutions or df["institution"].tolist())
