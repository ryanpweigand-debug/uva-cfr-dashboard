"""
Dual Score Theory Page
======================
Maintains RSI (Relationship Strength Index, 0-70) and SOI (Strategic
Opportunity Index, 0-30) as *separate* scores rather than collapsing
them into a single composite.  This prevents high-RSI incumbents from
burying high-SOI newcomers in a single ranked list.

Partner Types (quadrant):
  Anchor  — High RSI + High SOI  →  Maintain & expand
  Growth  — Low  RSI + High SOI  →  Business development
  Legacy  — High RSI + Low  SOI  →  Stewardship
  Emerging— Low  RSI + Low  SOI  →  Monitor
"""

import dash
from dash import html, dcc, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "components"))

from queries import (
    load_dual_scored_partners, load_partners,
    RELATIONSHIP_METRICS, STRATEGIC_METRICS,
    SECTOR_COLORS, DUAL_PARTNER_TYPES,
)
from charts import (
    UVA_NAVY, UVA_ORANGE, LIGHT_BG, CARD_BG, TEXT_DARK, TEXT_MID,
    TEXT_LIGHT, GRID_COLOR, BORDER, CHART_FONT, chart_layout,
)

dash.register_page(__name__, path="/dual-score", name="Dual Score Model", order=6)

ALL_SECTORS = ["All"] + sorted(SECTOR_COLORS.keys())
ALL_TYPES   = ["All", "Anchor", "Growth", "Legacy", "Emerging"]

RSI_MID = 35   # midpoint of 0-70
SOI_MID = 15   # midpoint of 0-30


# ── 1. Theory explainer cards ─────────────────────────────────────────────────
def type_card(type_name):
    d = DUAL_PARTNER_TYPES[type_name]
    descriptions = {
        "Anchor":   "High proven relationship + high future opportunity. The crown jewels of the portfolio — deserve executive attention and full engagement resources.",
        "Growth":   "Low historical footprint but high strategic potential. The new pipeline — prioritize for business development and first-mover engagement.",
        "Legacy":   "Strong existing relationship but limited forward opportunity. Stewardship mode — protect and deepen without over-investing in expansion.",
        "Emerging": "Low on both dimensions today. Monitor for strategic shifts — these partners may graduate into Growth or Legacy over time.",
    }
    rsi_label = "High RSI" if type_name in ("Anchor", "Legacy") else "Low RSI"
    soi_label = "High SOI" if type_name in ("Anchor", "Growth") else "Low SOI"
    return html.Div([
        html.Div([
            html.Span(d["icon"], style={"fontSize": "1.6rem", "marginRight": "8px"}),
            html.Span(type_name, style={
                "fontFamily": "var(--font-brand)", "fontWeight": "700",
                "fontSize": "1.1rem", "color": d["color"],
            }),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
        html.Div([
            html.Span(rsi_label, className="dual-badge dual-badge-rsi me-1"),
            html.Span(soi_label, className="dual-badge dual-badge-soi"),
        ], style={"marginBottom": "8px"}),
        html.Div(d["action"], style={
            "fontSize": "0.78rem", "fontWeight": "600",
            "color": d["color"], "marginBottom": "6px",
        }),
        html.Div(descriptions[type_name], style={
            "fontSize": "0.78rem", "color": TEXT_MID, "lineHeight": "1.45",
        }),
    ], className="dual-type-card", style={"borderTop": f"4px solid {d['color']}"}),


# ── 2. Quadrant scatter ───────────────────────────────────────────────────────
def quadrant_scatter(df, sector="All"):
    if sector != "All":
        df = df[df["sector"] == sector]

    # Quadrant background shading
    fig = go.Figure()
    quad_colors = [
        (RSI_MID, 70,  SOI_MID, 30,  "rgba(229,114,0,0.06)",   "Anchor"),
        (0,       RSI_MID, SOI_MID, 30,  "rgba(21,101,192,0.06)",  "Growth"),
        (RSI_MID, 70,  0, SOI_MID,       "rgba(46,125,50,0.06)",   "Legacy"),
        (0,       RSI_MID, 0, SOI_MID,   "rgba(123,31,162,0.06)",  "Emerging"),
    ]
    for x0, x1, y0, y1, fill, label in quad_colors:
        d_info = DUAL_PARTNER_TYPES[label]
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=fill, line=dict(width=0), layer="below")
        fig.add_annotation(
            x=(x0 + x1) / 2, y=(y0 + y1) / 2,
            text=f"{d_info['icon']} {label}",
            showarrow=False,
            font=dict(size=11, color=d_info["color"],
                      family="var(--font-brand, Montserrat)"),
            opacity=0.55,
        )

    # Midpoint dividers
    fig.add_vline(x=RSI_MID, line_dash="dot", line_color=GRID_COLOR, line_width=1.5)
    fig.add_hline(y=SOI_MID, line_dash="dot", line_color=GRID_COLOR, line_width=1.5)

    # Partner scatter
    for ptype, pinfo in DUAL_PARTNER_TYPES.items():
        sub = df[df["dual_type"] == ptype]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["rsi"], y=sub["soi"],
            mode="markers+text",
            name=f"{pinfo['icon']} {ptype}",
            marker=dict(
                color=pinfo["color"], size=11,
                line=dict(color="white", width=1.5),
                opacity=0.88,
            ),
            text=sub["name"].apply(lambda n: n.split()[0]),  # first word only
            textposition="top center",
            textfont=dict(size=8, color=pinfo["color"]),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "RSI: %{x:.1f} / 70<br>"
                "SOI: %{y:.1f} / 30<br>"
                "Type: %{customdata[1]}<br>"
                "Sector: %{customdata[2]}<br>"
                "<i>%{customdata[3]}</i><extra></extra>"
            ),
            customdata=list(zip(sub["name"], sub["dual_type"],
                                sub["sector"], sub["dual_action"])),
        ))

    lo = chart_layout("RSI vs SOI — Partner Quadrant Map", height=520)
    lo["xaxis"].update(title="RSI — Relationship Strength Index (0–70)",
                       range=[-2, 72], gridcolor=GRID_COLOR)
    lo["yaxis"].update(title="SOI — Strategic Opportunity Index (0–30)",
                       range=[-1, 32], gridcolor=GRID_COLOR)
    lo["legend"] = dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=10))
    fig.update_layout(**lo)
    return fig


# ── 3. Dual score bar matrix ──────────────────────────────────────────────────
def dual_bar_matrix(df, sector="All", n=20):
    if sector != "All":
        df = df[df["sector"] == sector]
    df = df.sort_values("rsi", ascending=False).head(n)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="RSI — Relationship Strength (0–70)",
        y=df["name"],
        x=df["rsi"],
        orientation="h",
        marker=dict(
            color=[DUAL_PARTNER_TYPES[t]["color"] for t in df["dual_type"]],
            opacity=0.85,
        ),
        text=[f"RSI {v:.1f}" for v in df["rsi"]],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="white", size=9),
        hovertemplate="<b>%{y}</b><br>RSI: %{x:.1f} / 70<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="SOI — Strategic Opportunity (0–30)",
        y=df["name"],
        x=df["soi"],
        orientation="h",
        marker=dict(color=UVA_ORANGE, opacity=0.55,
                    pattern_shape="/", pattern_fgcolor=UVA_ORANGE),
        text=[f"SOI {v:.1f}" for v in df["soi"]],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color=UVA_ORANGE, size=9),
        hovertemplate="<b>%{y}</b><br>SOI: %{x:.1f} / 30<extra></extra>",
    ))

    lo = chart_layout(f"RSI + SOI Side-by-Side — Top {n} by Relationship Strength",
                      height=max(400, n * 30 + 80))
    lo["barmode"] = "group"
    lo["xaxis"].update(title="Score", range=[0, 75])
    lo["xaxis2"] = dict(range=[0, 35])
    lo["legend"] = dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=10))
    fig.update_layout(**lo)
    return fig


# ── 4. Partner type distribution donut ───────────────────────────────────────
def type_donut(df):
    counts = df["dual_type"].value_counts().reset_index()
    counts.columns = ["type", "count"]
    colors = [DUAL_PARTNER_TYPES[t]["color"] for t in counts["type"]]
    icons  = [DUAL_PARTNER_TYPES[t]["icon"]  for t in counts["type"]]
    labels = [f"{i} {t}" for i, t in zip(icons, counts["type"])]

    fig = go.Figure(go.Pie(
        labels=labels, values=counts["count"],
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>%{value} partners (%{percent})<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>{len(df)}</b><br><span style='font-size:11px'>Partners</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color=UVA_NAVY),
    )
    lo = chart_layout("Portfolio by Partner Type", height=340, show_legend=False)
    lo["margin"] = dict(l=10, r=10, t=50, b=10)
    fig.update_layout(**lo)
    return fig


# ── 5. RSI vs SOI divergence bar ─────────────────────────────────────────────
def divergence_bar(df, n=20):
    """Shows how much each partner 'leans' RSI vs SOI (normalized to same 0-100 scale)."""
    df = df.sort_values("rsi_pct", ascending=False).head(n).copy()
    df["rsi_norm"] = df["rsi_pct"]        # already 0-100
    df["soi_norm"] = df["soi_pct"]        # already 0-100
    df["divergence"] = df["rsi_norm"] - df["soi_norm"]

    fig = go.Figure()
    for _, row in df.iterrows():
        color = DUAL_PARTNER_TYPES[row["dual_type"]]["color"]
        fig.add_trace(go.Bar(
            x=[row["divergence"]],
            y=[row["name"]],
            orientation="h",
            marker_color=color if row["divergence"] >= 0 else UVA_ORANGE,
            marker_opacity=0.8,
            showlegend=False,
            hovertemplate=(
                f"<b>{row['name']}</b><br>"
                f"RSI%: {row['rsi_norm']:.1f}%<br>"
                f"SOI%: {row['soi_norm']:.1f}%<br>"
                f"Divergence: {row['divergence']:+.1f}%<extra></extra>"
            ),
        ))

    fig.add_vline(x=0, line_color=TEXT_MID, line_width=1.5)
    lo = chart_layout(
        "RSI vs SOI Divergence (normalized %) — Relationship-Heavy ← 0 → Opportunity-Heavy",
        height=max(380, n * 26 + 80)
    )
    lo["xaxis"].update(title="RSI% minus SOI% (positive = relationship-heavy)",
                       zeroline=True, zerolinecolor=TEXT_MID)
    lo["margin"]["l"] = 160
    fig.update_layout(**lo)
    return fig


# ── 6. Partner detail table ───────────────────────────────────────────────────
def dual_score_table(df):
    table_df = df[["name", "sector", "rsi", "soi", "rsi_pct", "soi_pct",
                   "dual_type", "dual_action"]].copy()
    table_df["RSI"] = table_df["rsi"].apply(lambda x: f"{x:.1f} / 70")
    table_df["SOI"] = table_df["soi"].apply(lambda x: f"{x:.1f} / 30")
    table_df["RSI %"] = table_df["rsi_pct"].apply(lambda x: f"{x:.0f}%")
    table_df["SOI %"] = table_df["soi_pct"].apply(lambda x: f"{x:.0f}%")
    table_df = table_df.rename(columns={"name": "Partner", "sector": "Sector",
                                         "dual_type": "Type", "dual_action": "Recommended Action"})
    table_df = table_df[["Partner", "Sector", "Type", "RSI", "RSI %",
                          "SOI", "SOI %", "Recommended Action"]]
    table_df = table_df.sort_values(["Type", "Partner"])

    type_colors = {t: d["color"] for t, d in DUAL_PARTNER_TYPES.items()}

    return dash_table.DataTable(
        data=table_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in table_df.columns],
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": UVA_NAVY, "color": "white",
            "fontWeight": "700", "fontSize": "12px",
            "fontFamily": "var(--font-main, sans-serif)",
            "border": "none", "padding": "10px 12px",
        },
        style_cell={
            "fontSize": "12px", "fontFamily": "var(--font-main, sans-serif)",
            "padding": "8px 12px", "border": f"1px solid {BORDER}",
            "color": TEXT_DARK, "backgroundColor": CARD_BG,
        },
        style_data_conditional=[
            {"if": {"filter_query": f'{{Type}} = "{t}"', "column_id": "Type"},
             "color": c, "fontWeight": "700"}
            for t, c in type_colors.items()
        ] + [
            {"if": {"row_index": "odd"}, "backgroundColor": LIGHT_BG},
        ],
        sort_action="native",
        filter_action="native",
        page_size=15,
        style_filter={"backgroundColor": LIGHT_BG, "border": f"1px solid {BORDER}"},
    )


# ── Page Layout ────────────────────────────────────────────────────────────────
layout = html.Div([

    # ── Header ────────────────────────────────────────────────────────────────
    html.Div([
        html.H2("Dual Score Model", className="page-title"),
        html.P(
            "Instead of collapsing everything into one number, the Dual Score Model "
            "maintains RSI (Relationship Strength, 0–70) and SOI (Strategic Opportunity, 0–30) "
            "separately — exposing four distinct partner types and preventing high-opportunity "
            "partners from being buried under incumbent relationships.",
            className="page-subtitle"
        ),
    ], className="page-header"),

    # ── Filters ───────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            dbc.Label("Scoring Method", className="dropdown-label"),
            dcc.Dropdown(
                id="dual-method-dd",
                options=[
                    {"label": "Percentile Ranked (Method 2 — Preferred)", "value": "percentile"},
                    {"label": "Human Judgment / 0-10 (Method 1)",          "value": "judgment"},
                ],
                value="percentile", clearable=False, className="cfr-dropdown",
            ),
        ], md=5),
        dbc.Col([
            dbc.Label("Filter by Sector", className="dropdown-label"),
            dcc.Dropdown(
                id="dual-sector-dd",
                options=[{"label": s, "value": s} for s in ALL_SECTORS],
                value="All", clearable=False, className="cfr-dropdown",
            ),
        ], md=4),
    ], className="filter-row mb-4"),

    # ── Theory explainer ──────────────────────────────────────────────────────
    html.Div([
        html.Div("WHY DUAL SCORING?", className="section-eyebrow mb-2"),
        html.Div(
            "A single composite score hides strategic nuance. "
            "A partner with $50M in historical research (high RSI) and low future opportunity "
            "looks identical to a new partner with no history but huge greenfield potential. "
            "The Dual Score Model surfaces both dimensions — rearview proof and forward opportunity — "
            "so you manage each type differently.",
            className="theory-explainer"
        ),
    ], className="chart-card mb-3"),

    # ── 4 partner type cards ──────────────────────────────────────────────────
    html.Div("THE FOUR PARTNER TYPES", className="section-eyebrow mb-2 px-1"),
    dbc.Row([
        dbc.Col(type_card("Anchor"),   md=3, sm=6, xs=12, className="mb-3"),
        dbc.Col(type_card("Growth"),   md=3, sm=6, xs=12, className="mb-3"),
        dbc.Col(type_card("Legacy"),   md=3, sm=6, xs=12, className="mb-3"),
        dbc.Col(type_card("Emerging"), md=3, sm=6, xs=12, className="mb-3"),
    ], className="mb-2"),

    # ── Score header KPIs ─────────────────────────────────────────────────────
    html.Div(id="dual-kpi-row", className="mb-3"),

    # ── Quadrant scatter + donut ──────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            html.Div([
                dcc.Graph(id="dual-quadrant", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=8),
        dbc.Col([
            html.Div([
                dcc.Graph(id="dual-donut", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=4),
    ], className="mb-3"),

    # ── Dual bar matrix ───────────────────────────────────────────────────────
    html.Div([
        dcc.Graph(id="dual-bar-matrix", config={"displayModeBar": False}),
    ], className="chart-card mb-3"),

    # ── Divergence bar ────────────────────────────────────────────────────────
    html.Div([
        dcc.Graph(id="dual-divergence", config={"displayModeBar": False}),
    ], className="chart-card mb-3"),

    # ── Full table ────────────────────────────────────────────────────────────
    html.Div("FULL PARTNER DUAL SCORE TABLE", className="section-eyebrow mb-2 px-1"),
    html.Div([
        html.Div(id="dual-table"),
    ], className="chart-card mb-4"),

], className="cfr-page")


# ── Callbacks ──────────────────────────────────────────────────────────────────
@callback(
    Output("dual-kpi-row",    "children"),
    Output("dual-quadrant",   "figure"),
    Output("dual-donut",      "figure"),
    Output("dual-bar-matrix", "figure"),
    Output("dual-divergence", "figure"),
    Output("dual-table",      "children"),
    Input("dual-method-dd",   "value"),
    Input("dual-sector-dd",   "value"),
)
def update_dual(method, sector):
    df = load_dual_scored_partners(method)

    # Filter for charts that respect sector
    df_filt = df if sector == "All" else df[df["sector"] == sector]

    # KPI row
    type_counts = df["dual_type"].value_counts()
    kpis = html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Div(f"{type_counts.get('Anchor', 0)}", className="stat-value",
                         style={"color": DUAL_PARTNER_TYPES['Anchor']['color']}),
                html.Div("⚓ Anchor Partners", className="stat-label"),
                html.Div("High RSI + High SOI", className="stat-sub"),
            ], className="stat-card"), md=3, sm=6, xs=6),
            dbc.Col(html.Div([
                html.Div(f"{type_counts.get('Growth', 0)}", className="stat-value",
                         style={"color": DUAL_PARTNER_TYPES['Growth']['color']}),
                html.Div("🚀 Growth Partners", className="stat-label"),
                html.Div("Low RSI + High SOI", className="stat-sub"),
            ], className="stat-card"), md=3, sm=6, xs=6),
            dbc.Col(html.Div([
                html.Div(f"{type_counts.get('Legacy', 0)}", className="stat-value",
                         style={"color": DUAL_PARTNER_TYPES['Legacy']['color']}),
                html.Div("🏛️ Legacy Partners", className="stat-label"),
                html.Div("High RSI + Low SOI", className="stat-sub"),
            ], className="stat-card"), md=3, sm=6, xs=6),
            dbc.Col(html.Div([
                html.Div(f"{type_counts.get('Emerging', 0)}", className="stat-value",
                         style={"color": DUAL_PARTNER_TYPES['Emerging']['color']}),
                html.Div("🌱 Emerging Partners", className="stat-label"),
                html.Div("Low RSI + Low SOI", className="stat-sub"),
            ], className="stat-card"), md=3, sm=6, xs=6),
        ]),
    ])

    return (
        kpis,
        quadrant_scatter(df_filt.copy()),
        type_donut(df),
        dual_bar_matrix(df_filt.copy(), n=20),
        divergence_bar(df_filt.copy(), n=20),
        dual_score_table(df),
    )
