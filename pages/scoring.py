"""
Partner Scoring Page — Ahsan's 100-pt methodology with dropdowns and detail views.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "components"))

from queries import (
    load_scored_partners, load_partners,
    RELATIONSHIP_METRICS, STRATEGIC_METRICS, ALL_METRICS,
    PARTNER_TIERS, TIER_COLORS, SECTOR_COLORS, get_tier,
    CORPORATE_SECTORS, FOUNDATION_SECTORS,
)
from charts import (
    UVA_NAVY, UVA_ORANGE, LIGHT_BG, CARD_BG, TEXT_DARK, TEXT_MID, TEXT_LIGHT,
    GRID_COLOR, BORDER, CHART_FONT, chart_layout, make_gauge, make_radar,
)

dash.register_page(__name__, path="/scoring", name="Partner Scoring", order=1)

ALL_SECTORS = ["All"] + sorted(SECTOR_COLORS.keys())
ALL_TIERS   = ["All", "Strategic", "Active", "Developing", "Prospect", "Inactive"]

_TAB  = dict(backgroundColor="transparent", border="none",
             borderBottom="3px solid transparent", color=TEXT_MID,
             fontWeight="600", fontFamily=CHART_FONT, fontSize="0.88rem",
             padding="12px 24px")
_TSEL = {**_TAB, "color": UVA_NAVY,
         "borderBottom": f"3px solid {UVA_ORANGE}", "fontWeight": "700"}


# ── Ranking bar chart ─────────────────────────────────────────────────────────
def rankings_bar(scored, sector="All", tier="All"):
    df = scored.copy()
    if sector != "All":
        df = df[df["sector"] == sector]
    if tier != "All":
        df = df[df["tier"] == tier]
    df = df.sort_values("composite_score", ascending=True).tail(30)
    colors = [TIER_COLORS.get(t, "#999") for t in df["tier"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["composite_score"], y=df["name"],
        orientation="h", marker_color=colors,
        text=[f"{v:.1f}" for v in df["composite_score"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}/100<extra></extra>",
        customdata=list(zip(df["tier"], df["sector"])),
    ))
    # Tier threshold lines
    for lo, hi, label, color, _ in PARTNER_TIERS[:-1]:
        fig.add_vline(x=lo, line_dash="dot", line_color=color, line_width=1,
                      annotation_text=f"{lo}", annotation_position="top",
                      annotation_font=dict(size=9, color=color))

    fig.update_layout(**chart_layout("Partner Rankings (Partner Score / 100)", height=max(380, len(df)*22+80)))
    fig.update_xaxes(range=[0, 105])
    return fig


# ── Score breakdown stacked bar ───────────────────────────────────────────────
def stacked_breakdown(scored, sector="All", tier="All", n=15):
    df = scored.copy()
    if sector != "All":
        df = df[df["sector"] == sector]
    if tier != "All":
        df = df[df["tier"] == tier]
    df = df.sort_values("composite_score", ascending=False).head(n)

    fig = go.Figure()
    rel_prefix = "pct_" if "pct_sponsored_research_5yr" in df.columns else "jdg_"

    fig.add_trace(go.Bar(
        name="Relationship (70 pts)",
        y=df["name"],
        x=df["relationship_score"],
        orientation="h",
        marker_color=UVA_NAVY,
        hovertemplate="<b>%{y}</b><br>Relationship: %{x:.1f}/70<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Strategic (30 pts)",
        y=df["name"],
        x=df["strategic_score"],
        orientation="h",
        marker_color=UVA_ORANGE,
        hovertemplate="<b>%{y}</b><br>Strategic: %{x:.1f}/30<extra></extra>",
    ))
    lo = chart_layout(f"Score Breakdown — Top {n} Partners", height=max(360, n * 26 + 80))
    lo["barmode"] = "stack"
    lo["xaxis"]["range"] = [0, 105]
    lo["xaxis"]["title"] = "Points"
    fig.update_layout(**lo)
    return fig


# ── Metric heatmap ─────────────────────────────────────────────────────────────
def metric_heatmap(scored, sector="All", n=20):
    df = scored.copy()
    if sector != "All":
        df = df[df["sector"] == sector]
    df = df.sort_values("composite_score", ascending=False).head(n)

    prefix = "pct_" if "pct_sponsored_research_5yr" in df.columns else "jdg_"
    metric_cols  = [f"{prefix}{col}" for col, _, _ in ALL_METRICS]
    metric_labels = [lbl for _, lbl, _ in ALL_METRICS]
    max_pts       = [mp  for _, _, mp  in ALL_METRICS]

    # Normalize each metric to 0–100% of its max
    z = []
    for _, row in df.iterrows():
        row_pct = [row[mc] / mp * 100 if mp > 0 else 0
                   for mc, mp in zip(metric_cols, max_pts)]
        z.append(row_pct)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=metric_labels,
        y=list(df["name"]),
        colorscale=[[0, "#F7F8FA"], [0.5, "#90CAF9"], [1.0, UVA_NAVY]],
        zmin=0, zmax=100,
        hovertemplate="%{y} · %{x}<br>%{z:.1f}% of max pts<extra></extra>",
        colorbar=dict(title="% of Max Pts", tickfont=dict(size=9), len=0.7),
    ))
    lo = chart_layout(f"Metric Heatmap — Top {n} Partners (% of Max Points)", height=max(400, n*22+80))
    lo["xaxis"]["tickangle"] = -35
    lo["xaxis"]["tickfont"] = dict(size=9)
    lo["margin"]["b"] = 120
    fig.update_layout(**lo)
    return fig


# ── Partner detail ─────────────────────────────────────────────────────────────
def partner_detail_card(partner_row, scored_row):
    score = scored_row["composite_score"]
    rel   = scored_row["relationship_score"]
    strat = scored_row["strategic_score"]
    tier, tier_color, action = get_tier(score)
    rank  = int(scored_row["rank"])

    # Metric breakdown
    prefix = "pct_" if "pct_sponsored_research_5yr" in scored_row.index else "jdg_"
    rows = []
    for col, lbl, max_pts in RELATIONSHIP_METRICS:
        pts = scored_row.get(f"{prefix}{col}", 0)
        pct = pts / max_pts * 100 if max_pts > 0 else 0
        rows.append(html.Tr([
            html.Td(lbl, className="metric-label-cell"),
            html.Td(f"{pts:.1f} / {max_pts}", className="metric-pts-cell"),
            html.Td(
                html.Div([
                    html.Div(style={
                        "width": f"{pct:.0f}%", "height": "8px",
                        "background": UVA_NAVY, "borderRadius": "4px",
                        "minWidth": "2px",
                    }),
                ], style={"background": LIGHT_BG, "borderRadius": "4px", "width": "100%"}),
                className="metric-bar-cell",
            ),
        ]))

    for col, lbl, max_pts in STRATEGIC_METRICS:
        pts = scored_row.get(f"{prefix}{col}", 0)
        pct = pts / max_pts * 100 if max_pts > 0 else 0
        rows.append(html.Tr([
            html.Td(lbl, className="metric-label-cell"),
            html.Td(f"{pts:.1f} / {max_pts}", className="metric-pts-cell"),
            html.Td(
                html.Div([
                    html.Div(style={
                        "width": f"{pct:.0f}%", "height": "8px",
                        "background": UVA_ORANGE, "borderRadius": "4px",
                        "minWidth": "2px",
                    }),
                ], style={"background": LIGHT_BG, "borderRadius": "4px", "width": "100%"}),
                className="metric-bar-cell",
            ),
        ]))

    # Radar
    rel_labels = [lbl for _, lbl, _ in RELATIONSHIP_METRICS]
    rel_vals   = [scored_row.get(f"{prefix}{c}", 0) for c, _, _ in RELATIONSHIP_METRICS]
    rel_max    = [mp for _, _, mp in RELATIONSHIP_METRICS]
    strat_labels = [lbl for _, lbl, _ in STRATEGIC_METRICS]
    strat_vals   = [scored_row.get(f"{prefix}{c}", 0) for c, _, _ in STRATEGIC_METRICS]
    strat_max    = [mp for _, _, mp in STRATEGIC_METRICS]

    radar_fig = make_radar(
        rel_labels + strat_labels,
        rel_vals   + strat_vals,
        rel_max    + strat_max,
        partner_name=partner_row["name"],
    )

    return html.Div([
        # Banner
        html.Div([
            html.Div([
                html.Div(partner_row["name"], className="detail-partner-name"),
                html.Div([
                    html.Span(partner_row["sector"], className=f"sector-badge sector-{partner_row['sector'].lower()} me-2"),
                    html.Span(f"{partner_row.get('hq_city','')}, {partner_row.get('hq_state','')}", className="detail-meta"),
                ]),
            ], className="flex-grow-1"),
            html.Div([
                html.Div(f"{score:.1f}", className="detail-score-big"),
                html.Div("out of 100 pts", className="detail-score-sub"),
                html.Div(f"Rank #{rank}", className="detail-rank"),
            ]),
            html.Div([
                html.Span(tier, className="tier-badge-lg",
                          style={"background": tier_color, "color": "#fff"}),
                html.Div(action, className="detail-action-text mt-1"),
            ], className="ms-3 text-end"),
        ], className="detail-banner"),

        # Score pills
        dbc.Row([
            dbc.Col(html.Div([
                html.Div(f"{rel:.1f} / 70", className="score-pill-value",
                         style={"color": UVA_NAVY}),
                html.Div("Relationship Strength", className="score-pill-label"),
            ], className="score-pill"), md=4),
            dbc.Col(html.Div([
                html.Div(f"{strat:.1f} / 30", className="score-pill-value",
                         style={"color": UVA_ORANGE}),
                html.Div("Strategic Opportunity", className="score-pill-label"),
            ], className="score-pill"), md=4),
            dbc.Col(html.Div([
                html.Div(f"${partner_row.get('est_annual_value_k',0)/1000:.1f}M" if partner_row.get('est_annual_value_k',0) >= 1000 else f"${partner_row.get('est_annual_value_k',0):.0f}K",
                         className="score-pill-value", style={"color": "#2E7D32"}),
                html.Div("Est. Annual Value", className="score-pill-label"),
            ], className="score-pill"), md=4),
        ], className="mb-3"),

        # Radar + Breakdown
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=radar_fig, config={"displayModeBar": False}),
            ], md=5),
            dbc.Col([
                html.Div("METRIC BREAKDOWN", className="section-eyebrow mb-2"),
                html.Div([
                    dbc.Table([
                        html.Thead(html.Tr([
                            html.Th("Metric"), html.Th("Points Earned"), html.Th("% of Max"),
                        ])),
                        html.Tbody(rows),
                    ], className="cfr-table cfr-table-sm", hover=True, responsive=True),
                ], style={"maxHeight": "380px", "overflowY": "auto"}),
            ], md=7),
        ]),

        # Notes
        html.Div([
            html.Strong("CFR Notes: "),
            html.Span(partner_row.get("notes", "No notes on file.")),
        ], className="detail-notes mt-3") if partner_row.get("notes") else html.Span(),

    ], className="detail-card")


# ── Page Layout ────────────────────────────────────────────────────────────────
layout = html.Div([
    html.Div([
        html.H2("Partner Scoring", className="page-title"),
        html.P(
            "Ahsan's 100-pt model: 70% Relationship Strength (rearview) + "
            "30% Strategic Opportunity (forward-looking). "
            "Method 2 (percentile) is preferred when full data is available.",
            className="page-subtitle"
        ),
    ], className="page-header"),

    # ── Partner Type Tabs ─────────────────────────────────────────────────
    dcc.Tabs(
        id="scoring-type-tabs", value="Corporate",
        style={"borderBottom": f"1px solid {BORDER}", "marginBottom": "20px",
               "backgroundColor": CARD_BG},
        children=[
            dcc.Tab(label="🏢  Corporate Relations", value="Corporate",
                    style=_TAB, selected_style=_TSEL),
            dcc.Tab(label="🏛️  Foundation Relations", value="Foundation",
                    style=_TAB, selected_style=_TSEL),
        ],
    ),

    # ── Filters ──────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            dbc.Label("Scoring Method", className="dropdown-label"),
            dcc.Dropdown(
                id="scoring-method-dd",
                options=[
                    {"label": "Percentile Ranked (Method 2 — Preferred)", "value": "percentile"},
                    {"label": "Human Judgment / 0-10 (Method 1)",          "value": "judgment"},
                ],
                value="percentile", clearable=False, className="cfr-dropdown",
            ),
        ], md=4),
        dbc.Col([
            dbc.Label("Filter by Sector", className="dropdown-label"),
            dcc.Dropdown(
                id="scoring-sector-dd",
                options=[{"label": s, "value": s} for s in ALL_SECTORS],
                value="All", clearable=False, className="cfr-dropdown",
            ),
        ], md=3),
        dbc.Col([
            dbc.Label("Filter by Tier", className="dropdown-label"),
            dcc.Dropdown(
                id="scoring-tier-dd",
                options=[{"label": t, "value": t} for t in ALL_TIERS],
                value="All", clearable=False, className="cfr-dropdown",
            ),
        ], md=3),
        dbc.Col([
            dbc.Label("Select Partner for Detail", className="dropdown-label"),
            dcc.Dropdown(
                id="scoring-partner-dd",
                options=[], value=None,
                placeholder="Click a bar or select here…",
                clearable=True, className="cfr-dropdown",
            ),
        ], md=2),
    ], className="filter-row mb-3"),

    # ── Tier legend ──────────────────────────────────────────────────────────
    html.Div([
        html.Span("Tier Guide: ", className="fw-semibold me-2",
                  style={"fontSize": "12px", "color": TEXT_MID}),
    ] + [
        html.Span(f"{label} ({lo}–{hi})", className="tier-badge me-2",
                  style={"background": color, "color": "#fff"})
        for lo, hi, label, color, _ in PARTNER_TIERS
    ], className="mb-3"),

    # ── Charts ───────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            html.Div([
                dcc.Graph(id="rankings-bar", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=5),
        dbc.Col([
            html.Div([
                dcc.Graph(id="stacked-breakdown", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=7),
    ], className="mb-3"),

    html.Div([
        dcc.Graph(id="metric-heatmap", config={"displayModeBar": False}),
    ], className="chart-card mb-3"),

    # ── Partner Detail ────────────────────────────────────────────────────────
    html.Div(id="partner-detail-section", className="mb-3"),

], className="cfr-page")


# ── Callbacks ──────────────────────────────────────────────────────────────────
# ── Reset sector options when tab switches ────────────────────────────────────
@callback(
    Output("scoring-sector-dd", "options"),
    Output("scoring-sector-dd", "value"),
    Input("scoring-type-tabs",  "value"),
    State("scoring-sector-dd",  "value"),
)
def _reset_scoring_sector(tab, cur):
    sectors = CORPORATE_SECTORS if tab == "Corporate" else FOUNDATION_SECTORS
    opts = [{"label": s, "value": s} for s in ["All"] + sectors]
    val  = cur if cur in (["All"] + sectors) else "All"
    return opts, val


@callback(
    Output("rankings-bar",       "figure"),
    Output("stacked-breakdown",  "figure"),
    Output("metric-heatmap",     "figure"),
    Output("scoring-partner-dd", "options"),
    Input("scoring-method-dd",   "value"),
    Input("scoring-sector-dd",   "value"),
    Input("scoring-tier-dd",     "value"),
    Input("scoring-type-tabs",   "value"),
)
def update_charts(method, sector, tier, tab):
    scored = load_scored_partners(method, tab)
    partner_opts = [{"label": f"#{int(r['rank'])} {r['name']}", "value": r['name']}
                    for _, r in scored.sort_values("rank").iterrows()]
    return (
        rankings_bar(scored, sector, tier),
        stacked_breakdown(scored, sector, tier),
        metric_heatmap(scored, sector),
        partner_opts,
    )


@callback(
    Output("partner-detail-section", "children"),
    Input("scoring-partner-dd",      "value"),
    Input("scoring-method-dd",       "value"),
    Input("scoring-type-tabs",       "value"),
)
def show_partner_detail(partner_name, method, tab):
    if not partner_name:
        return html.Div(
            "← Select a partner from the dropdown or click a bar to see the full detail view.",
            className="placeholder-text",
        )
    raw    = load_partners(tab)
    scored = load_scored_partners(method, tab)
    pr = raw[raw["name"] == partner_name]
    if pr.empty:
        return html.Div("Partner not found.", className="placeholder-text")
    sr = scored[scored["name"] == partner_name]
    if sr.empty:
        return html.Div("Partner not found.", className="placeholder-text")
    return partner_detail_card(pr.iloc[0], sr.iloc[0])


@callback(
    Output("scoring-partner-dd", "value"),
    Input("rankings-bar",        "clickData"),
)
def select_from_bar(click):
    if click and click.get("points"):
        return click["points"][0].get("y")
    return dash.no_update
