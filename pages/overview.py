"""
Executive Overview Page
Economic impact data, portfolio KPIs, and CFR strategic health at a glance.
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

from queries import (
    load_scored_partners, load_strategic_priorities, portfolio_kpis,
    sp_partner_alignment, PPE_STATS, SECTOR_COLORS, TIER_COLORS,
    RELATIONSHIP_METRICS, STRATEGIC_METRICS
)
from charts import (
    UVA_NAVY, UVA_ORANGE, LIGHT_BG, CARD_BG, TEXT_DARK, TEXT_MID,
    TEXT_LIGHT, GRID_COLOR, BORDER, CHART_FONT, chart_layout, make_gauge
)

dash.register_page(__name__, path="/", name="Executive Overview", order=0)


# ── Helper: KPI stat card ──────────────────────────────────────────────────────
def stat_card(value, label, sub=None, color=UVA_NAVY, big=False):
    return html.Div([
        html.Div(value, className="stat-value", style={"color": color,
                 "fontSize": "2.1rem" if big else "1.7rem"}),
        html.Div(label, className="stat-label"),
        html.Div(sub, className="stat-sub") if sub else html.Span(),
    ], className="stat-card")


def ppe_impact_strip():
    stats = [
        ("$11.9B",  "Total Economic Impact", "Direct + Indirect + Induced", UVA_ORANGE),
        ("67,109",  "Jobs Supported",         "1 in every 85 VA jobs",       UVA_NAVY),
        ("$35",     "ROI per $1 State Funding","2024 Economic Impact Study",  UVA_ORANGE),
        ("$455M",   "Government Revenue",      "$191M local · $264M state",   UVA_NAVY),
        ("$1.0B",   "Annual Research Impact",  "10,700 jobs · 55 startups",   UVA_ORANGE),
        ("53%",     "Graduate Salary Premium", "UVA alumni vs. non-grad avg", UVA_NAVY),
    ]
    return dbc.Row([
        dbc.Col(stat_card(v, l, s, c), md=2, sm=4, xs=6)
        for v, l, s, c in stats
    ], className="mb-4 ppe-strip")


def partner_portfolio_kpis(method):
    kpis = portfolio_kpis(method)
    cards = [
        (str(kpis["total_partners"]),         "Total Partners",         None,   UVA_NAVY),
        (str(kpis["strategic_count"]),         "Strategic Tier",         "Score 80-100", "#E57200"),
        (str(kpis["active_count"]),            "Active Tier",            "Score 60-79",  "#1565C0"),
        (f"{kpis['avg_score']:.1f}",           "Avg Partner Score",      "out of 100",   UVA_NAVY),
        (f"${kpis['total_sr_5yr']/1e6:.1f}M",  "Sponsored Research (5yr)", "Portfolio total", UVA_NAVY),
        (f"${kpis['total_phil_5yr']/1e6:.1f}M","Philanthropy (5yr)",       "Portfolio total", UVA_ORANGE),
        (f"${kpis['total_est_value_k']/1e3:.1f}M", "Pipeline Est. Value", "Procurement", "#2E7D32"),
    ]
    return dbc.Row([
        dbc.Col(stat_card(v, l, s, c), md=12//min(len(cards),4), sm=6, xs=6)
        for v, l, s, c in cards
    ], className="mb-4")


def scatter_matrix_chart(scored):
    scored["size"] = (scored["composite_score"] / 100 * 30 + 10).clip(10, 40)
    fig = px.scatter(
        scored, x="relationship_score", y="strategic_score",
        color="tier", color_discrete_map=TIER_COLORS,
        size="size", hover_name="name",
        hover_data={"composite_score": ":.1f", "tier": True,
                    "sector": True, "rank": True, "size": False},
        labels={"relationship_score": "Relationship Score (0–70)",
                "strategic_score": "Strategic Score (0–30)",
                "composite_score": "Total Score"},
    )
    fig.update_layout(**chart_layout("Partner Portfolio Matrix — Relationship vs. Strategic", height=420))
    fig.add_vline(x=scored["relationship_score"].mean(), line_dash="dot",
                  line_color=TEXT_LIGHT, line_width=1)
    fig.add_hline(y=scored["strategic_score"].mean(), line_dash="dot",
                  line_color=TEXT_LIGHT, line_width=1)
    return fig


def tier_donut(scored):
    tiers = scored["tier"].value_counts().reset_index()
    tiers.columns = ["tier", "count"]
    colors = [TIER_COLORS.get(t, "#999") for t in tiers["tier"]]
    fig = go.Figure(go.Pie(
        labels=tiers["tier"], values=tiers["count"],
        hole=0.6, marker_colors=colors,
        textinfo="label+value",
        hovertemplate="%{label}: %{value} partners (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **chart_layout("Tier Distribution", height=320, show_legend=False),
        annotations=[dict(
            text=f"<b>{len(scored)}</b><br><span style='font-size:10px'>Partners</span>",
            x=0.5, y=0.5, font_size=18, showarrow=False,
            font=dict(color=TEXT_DARK, family=CHART_FONT),
        )],
    )
    return fig


def sector_bar(scored):
    grp = scored.groupby("sector")["composite_score"].mean().sort_values(ascending=True)
    colors = [SECTOR_COLORS.get(s, "#999") for s in grp.index]
    fig = go.Figure(go.Bar(
        x=grp.values, y=grp.index, orientation="h",
        marker_color=colors,
        hovertemplate="%{y}: %{x:.1f} avg score<extra></extra>",
        text=[f"{v:.1f}" for v in grp.values],
        textposition="outside",
    ))
    fig.update_layout(**chart_layout("Avg Score by Sector", height=320))
    fig.update_xaxes(range=[0, 100])
    return fig


def sp_progress_chart():
    sp = load_strategic_priorities()
    colors = []
    for s in sp["status"]:
        if s == "Complete":
            colors.append("#2E7D32")
        elif s == "In Progress":
            colors.append(UVA_ORANGE)
        else:
            colors.append("#78909C")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sp["progress_pct"], y=sp["code"],
        orientation="h",
        marker_color=colors,
        text=[f"{p:.0f}%" for p in sp["progress_pct"]],
        textposition="outside",
        hovertemplate="%{y}: %{x:.0f}% complete<extra></extra>",
        customdata=sp["title"],
    ))
    fig.update_layout(**chart_layout("CFR Strategic Plan Progress", height=300))
    fig.update_xaxes(range=[0, 110], title_text="% Complete")
    return fig


def ppe_economic_chart():
    cats = ["Direct Impact", "Indirect Impact", "Induced Impact"]
    vals = [PPE_STATS["direct_b"], PPE_STATS["indirect_b"], PPE_STATS["induced_b"]]
    colors = [UVA_NAVY, UVA_ORANGE, "#4A90D9"]

    fig = go.Figure(go.Bar(
        x=cats, y=vals,
        marker_color=colors,
        text=[f"${v}B" for v in vals],
        textposition="outside",
        hovertemplate="%{x}: $%{y}B<extra></extra>",
    ))
    fig.update_layout(**chart_layout("UVA Economic Impact Breakdown ($B)", height=280))
    fig.update_yaxes(title_text="$ Billions", range=[0, 8])
    return fig


# ── Layout factory (method-dependent) ─────────────────────────────────────────
def build_layout(method="percentile"):
    scored = load_scored_partners(method)

    return html.Div([
        # ── Page Header ────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H2("CFR Partner Engagement Dashboard", className="page-title"),
                html.P(
                    "University of Virginia — Center for Corporate Research · "
                    "Powered by Ahsan's 100-pt scoring methodology",
                    className="page-subtitle"
                ),
            ], className="flex-grow-1"),
            html.Div([
                dbc.Label("Scoring Method", className="dropdown-label me-2"),
                dcc.Dropdown(
                    id="overview-method-dd",
                    options=[
                        {"label": "Percentile (Data-Driven)", "value": "percentile"},
                        {"label": "Judgment (0-10 Scale)",    "value": "judgment"},
                    ],
                    value=method, clearable=False,
                    className="cfr-dropdown",
                    style={"minWidth": "220px"},
                ),
            ], className="d-flex align-items-center"),
        ], className="page-header d-flex align-items-start"),

        # ── PPE Economic Impact Strip ──────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("UVA ECONOMIC IMPACT", className="section-eyebrow"),
                html.Span(" · From PPE Economic Impact Study", style={"color": TEXT_LIGHT, "fontSize": "11px"}),
            ], className="mb-2"),
            ppe_impact_strip(),
        ], className="section-block"),

        # ── Partner Portfolio KPIs ────────────────────────────────────────────
        html.Div([
            html.Div("PARTNER PORTFOLIO", className="section-eyebrow mb-2"),
            html.Div(id="overview-kpis"),
        ], className="section-block"),

        # ── Charts Row 1 ──────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Graph(
                        id="scatter-matrix",
                        figure=scatter_matrix_chart(scored),
                        config={"displayModeBar": False},
                    )
                ], className="chart-card"),
            ], md=8),
            dbc.Col([
                html.Div([dcc.Graph(id="tier-donut", figure=tier_donut(scored),
                                    config={"displayModeBar": False})],
                         className="chart-card mb-3"),
                html.Div([dcc.Graph(id="sector-bar-chart", figure=sector_bar(scored),
                                    config={"displayModeBar": False})],
                         className="chart-card"),
            ], md=4),
        ], className="mb-3"),

        # ── Charts Row 2 ──────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Graph(id="sp-progress", figure=sp_progress_chart(),
                              config={"displayModeBar": False})
                ], className="chart-card"),
            ], md=6),
            dbc.Col([
                html.Div([
                    dcc.Graph(id="ppe-econ-chart", figure=ppe_economic_chart(),
                              config={"displayModeBar": False})
                ], className="chart-card"),
            ], md=6),
        ], className="mb-3"),

        # ── Top Partners Table ────────────────────────────────────────────────
        html.Div([
            html.Div("TOP 10 PARTNERS BY SCORE", className="section-eyebrow mb-3"),
            html.Div(id="top-partners-table"),
        ], className="section-block"),

    ], className="cfr-page")


layout = build_layout()


# ── Callbacks ─────────────────────────────────────────────────────────────────
@callback(
    Output("scatter-matrix",    "figure"),
    Output("tier-donut",        "figure"),
    Output("sector-bar-chart",  "figure"),
    Output("overview-kpis",     "children"),
    Output("top-partners-table","children"),
    Input("overview-method-dd", "value"),
)
def update_overview(method):
    scored = load_scored_partners(method)

    # Top 10 table
    top10 = scored.nsmallest(10, "rank")[
        ["rank", "name", "sector", "composite_score",
         "relationship_score", "strategic_score", "tier"]
    ].copy()
    top10["composite_score"] = top10["composite_score"].round(1)
    top10["relationship_score"] = top10["relationship_score"].round(1)
    top10["strategic_score"] = top10["strategic_score"].round(1)

    rows = []
    for _, r in top10.iterrows():
        tc = TIER_COLORS.get(r["tier"], "#999")
        rows.append(html.Tr([
            html.Td(f"#{int(r['rank'])}", className="rank-cell"),
            html.Td(r["name"], className="partner-name-cell"),
            html.Td(html.Span(r["sector"], className=f"sector-badge sector-{r['sector'].lower()}")),
            html.Td(f"{r['composite_score']:.1f}", className="score-cell",
                    style={"fontWeight": "700", "color": UVA_NAVY}),
            html.Td(f"{r['relationship_score']:.1f}"),
            html.Td(f"{r['strategic_score']:.1f}"),
            html.Td(html.Span(r["tier"], className="tier-badge",
                              style={"background": tc, "color": "#fff"})),
        ]))

    table = dbc.Table(
        [html.Thead(html.Tr([
            html.Th("Rank"), html.Th("Partner"), html.Th("Sector"),
            html.Th("Score / 100"), html.Th("Rel / 70"), html.Th("Strat / 30"), html.Th("Tier"),
        ]))] + [html.Tbody(rows)],
        className="cfr-table", bordered=False, hover=True, striped=False, responsive=True,
    )

    return (
        scatter_matrix_chart(scored),
        tier_donut(scored),
        sector_bar(scored),
        partner_portfolio_kpis(method),
        table,
    )
