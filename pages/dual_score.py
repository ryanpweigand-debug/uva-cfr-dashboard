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


# ── 3. Top-5 per Type spotlight panel ────────────────────────────────────────
def mini_bar(pct, color):
    """Inline HTML progress bar, no Plotly needed."""
    return html.Div(
        html.Div(style={
            "width": f"{max(pct, 2):.1f}%", "height": "100%",
            "background": color, "borderRadius": "2px",
            "transition": "width 0.3s ease",
        }),
        style={
            "background": "rgba(0,0,0,0.07)", "height": "5px",
            "borderRadius": "2px", "overflow": "hidden", "marginTop": "2px",
        }
    )


def spotlight_partner_row(row, type_color):
    return html.Div([
        html.Div(row["name"], style={
            "fontWeight": "600", "fontSize": "0.82rem",
            "color": UVA_NAVY, "marginBottom": "5px",
            "whiteSpace": "nowrap", "overflow": "hidden",
            "textOverflow": "ellipsis",
        }),
        html.Div([
            html.Div([
                html.Div([
                    html.Span("RSI", style={"fontSize": "0.65rem", "color": TEXT_LIGHT,
                                            "fontWeight": "700", "marginRight": "4px"}),
                    html.Span(f"{row['rsi']:.1f}", style={"fontSize": "0.72rem",
                                                           "color": UVA_NAVY, "fontWeight": "700"}),
                ], style={"display": "flex", "alignItems": "center"}),
                mini_bar(row["rsi_pct"], UVA_NAVY),
            ], style={"marginBottom": "5px"}),
            html.Div([
                html.Div([
                    html.Span("SOI", style={"fontSize": "0.65rem", "color": TEXT_LIGHT,
                                            "fontWeight": "700", "marginRight": "4px"}),
                    html.Span(f"{row['soi']:.1f}", style={"fontSize": "0.72rem",
                                                           "color": UVA_ORANGE, "fontWeight": "700"}),
                ], style={"display": "flex", "alignItems": "center"}),
                mini_bar(row["soi_pct"], UVA_ORANGE),
            ]),
        ]),
    ], style={
        "padding": "10px 0",
        "borderBottom": f"1px solid rgba(0,0,0,0.07)",
    })


def type_spotlight(df, sector="All"):
    if sector != "All":
        df = df[df["sector"] == sector]

    cols = []
    for type_name, info in DUAL_PARTNER_TYPES.items():
        top5 = df[df["dual_type"] == type_name].sort_values(
            "rsi" if type_name in ("Anchor", "Legacy") else "soi",
            ascending=False
        ).head(5)

        rows = [spotlight_partner_row(row, info["color"])
                for _, row in top5.iterrows()]

        if not rows:
            rows = [html.Div("No partners in this quadrant",
                             style={"fontSize": "0.78rem", "color": TEXT_LIGHT,
                                    "padding": "12px 0"})]

        col = dbc.Col([
            html.Div([
                # Column header
                html.Div([
                    html.Span(info["icon"], style={"fontSize": "1.1rem", "marginRight": "6px"}),
                    html.Span(type_name, style={
                        "fontFamily": "var(--font-brand)", "fontWeight": "700",
                        "fontSize": "0.92rem", "color": info["color"],
                    }),
                ], style={"display": "flex", "alignItems": "center",
                          "marginBottom": "4px"}),
                html.Div(info["action"], style={
                    "fontSize": "0.68rem", "color": TEXT_MID,
                    "marginBottom": "10px", "lineHeight": "1.35",
                }),
                # Partner rows
                html.Div(rows),
            ], style={
                "borderTop": f"3px solid {info['color']}",
                "padding": "14px 16px",
                "background": CARD_BG,
                "borderRadius": "0 0 var(--radius, 8px) var(--radius, 8px)",
                "height": "100%",
            }),
        ], md=3, sm=6, xs=12, className="mb-3")
        cols.append(col)

    return dbc.Row(cols)


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


# ── 5. Partner detail table ───────────────────────────────────────────────────
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

    # ── Top 5 per type spotlight ──────────────────────────────────────────────
    html.Div("TOP 5 PARTNERS BY TYPE", className="section-eyebrow mb-2 px-1"),
    html.Div(id="dual-spotlight", className="mb-3"),

    # ── Full table ────────────────────────────────────────────────────────────
    html.Div("FULL PARTNER DUAL SCORE TABLE", className="section-eyebrow mb-2 px-1"),
    html.Div([
        html.Div(id="dual-table"),
    ], className="chart-card mb-4"),

], className="cfr-page")


# ── Callbacks ──────────────────────────────────────────────────────────────────
@callback(
    Output("dual-kpi-row",   "children"),
    Output("dual-quadrant",  "figure"),
    Output("dual-donut",     "figure"),
    Output("dual-spotlight", "children"),
    Output("dual-table",     "children"),
    Input("dual-method-dd",  "value"),
    Input("dual-sector-dd",  "value"),
)
def update_dual(method, sector):
    df = load_dual_scored_partners(method)
    df_filt = df if sector == "All" else df[df["sector"] == sector]

    # KPI row
    type_counts = df["dual_type"].value_counts()
    kpis = dbc.Row([
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
    ], className="mb-3")

    return (
        kpis,
        quadrant_scatter(df_filt.copy()),
        type_donut(df),
        type_spotlight(df_filt.copy(), sector),
        dual_score_table(df),
    )
