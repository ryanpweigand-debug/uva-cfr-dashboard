"""
Procurement Pipeline Page — Based on Procurement Partnership doc.
3-phase model: Discovery → Design → Implementation.
Holistic partner packages (research + talent + philanthropy + marketing).
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

from queries import load_partners, load_scored_partners, SECTOR_COLORS, TIER_COLORS
from charts import (
    UVA_NAVY, UVA_ORANGE, LIGHT_BG, CARD_BG, TEXT_DARK, TEXT_MID, TEXT_LIGHT,
    GRID_COLOR, BORDER, CHART_FONT, chart_layout,
)

dash.register_page(__name__, path="/procurement", name="Procurement Pipeline", order=4)

STAGES = ["Discovery", "Design", "Implementation", "Active"]
STAGE_COLORS = {
    "Discovery":      "#78909C",
    "Design":         "#F9A825",
    "Implementation": UVA_ORANGE,
    "Active":         UVA_NAVY,
}
STAGE_ICONS = {
    "Discovery":      "🔍",
    "Design":         "📐",
    "Implementation": "⚙️",
    "Active":         "✅",
}


def pipeline_funnel(df):
    counts = df.groupby("procurement_stage").size().reindex(STAGES, fill_value=0)
    values = [df[df["procurement_stage"] == s]["est_annual_value_k"].sum() for s in STAGES]

    fig = go.Figure(go.Funnel(
        name="",
        y=STAGES,
        x=[counts[s] for s in STAGES],
        textinfo="value+percent initial",
        marker=dict(color=[STAGE_COLORS[s] for s in STAGES]),
        hovertemplate="<b>%{y}</b><br>Partners: %{x}<br>Est. Value: $%{customdata:,.0f}k<extra></extra>",
        customdata=values,
    ))
    fig.update_layout(
        **chart_layout("Procurement Pipeline Funnel", height=350),
    )
    return fig


def pipeline_value_bar(df):
    grp = df.groupby("procurement_stage")["est_annual_value_k"].sum().reindex(STAGES, fill_value=0)
    colors = [STAGE_COLORS[s] for s in grp.index]
    fig = go.Figure(go.Bar(
        x=grp.index, y=grp.values / 1000,
        marker_color=colors,
        text=[f"${v/1000:.1f}M" for v in grp.values],
        textposition="outside",
        hovertemplate="%{x}: $%{y:.2f}M<extra></extra>",
    ))
    lo = chart_layout("Estimated Annual Value by Stage ($M)", height=320)
    lo["yaxis"]["title"] = "$ Millions"
    fig.update_layout(**lo)
    return fig


def partner_stage_scatter(df, scored):
    merged = df.merge(scored[["name","composite_score","tier"]], on="name", how="left")
    merged["size"] = (merged["est_annual_value_k"] / merged["est_annual_value_k"].max() * 30 + 8).clip(8, 38)
    colors = [STAGE_COLORS.get(s, "#999") for s in merged["procurement_stage"]]

    fig = px.scatter(
        merged,
        x="composite_score", y="est_annual_value_k",
        color="procurement_stage", color_discrete_map=STAGE_COLORS,
        size="size",
        hover_name="name",
        hover_data={"composite_score": ":.1f", "est_annual_value_k": ":,.0f",
                    "procurement_stage": True, "tier": True, "size": False},
        labels={"composite_score": "Partner Score (0–100)",
                "est_annual_value_k": "Est. Annual Value ($k)"},
    )
    fig.update_layout(**chart_layout("Partner Score vs. Procurement Value", height=380))
    return fig


def sector_pipeline_chart(df):
    grp = df.groupby(["sector","procurement_stage"])["est_annual_value_k"].sum().reset_index()
    fig = px.bar(
        grp, x="sector", y="est_annual_value_k", color="procurement_stage",
        color_discrete_map=STAGE_COLORS,
        labels={"est_annual_value_k": "Est. Annual Value ($k)", "sector": "Sector"},
        barmode="stack",
    )
    lo = chart_layout("Pipeline Value by Sector and Stage ($k)", height=340)
    lo["yaxis"]["title"] = "$ thousands"
    fig.update_layout(**lo)
    return fig


def pipeline_partner_table(df, scored, stage="All", sector="All"):
    merged = df.merge(scored[["name","composite_score","rank","tier"]], on="name", how="left")
    if stage  != "All":
        merged = merged[merged["procurement_stage"] == stage]
    if sector != "All":
        merged = merged[merged["sector"] == sector]
    merged = merged.sort_values("est_annual_value_k", ascending=False)

    rows = []
    for _, r in merged.iterrows():
        sc  = STAGE_COLORS.get(r["procurement_stage"], "#999")
        tc  = TIER_COLORS.get(r.get("tier","Inactive"), "#999")
        val = r["est_annual_value_k"]
        val_str = f"${val/1000:.1f}M" if val >= 1000 else f"${val:.0f}K"
        rows.append(html.Tr([
            html.Td(r["name"], className="partner-name-cell"),
            html.Td(html.Span(r["sector"],
                              className=f"sector-badge sector-{r['sector'].lower()}")),
            html.Td(html.Span(
                f"{STAGE_ICONS.get(r['procurement_stage'],'')} {r['procurement_stage']}",
                className="stage-badge", style={"background": sc, "color": "#fff"},
            )),
            html.Td(html.Span(r.get("tier","—"), className="tier-badge",
                              style={"background": tc, "color": "#fff"})),
            html.Td(f"{r.get('composite_score', 0):.1f}",
                    style={"fontWeight": "700", "color": UVA_NAVY}),
            html.Td(val_str, style={"fontWeight": "700", "color": "#2E7D32"}),
            html.Td(r.get("notes","—"), className="notes-cell"),
        ]))

    return dbc.Table([
        html.Thead(html.Tr([
            html.Th("Partner"), html.Th("Sector"), html.Th("Stage"),
            html.Th("Tier"), html.Th("Score"), html.Th("Est. Value / yr"),
            html.Th("Notes"),
        ])),
        html.Tbody(rows),
    ], className="cfr-table", bordered=False, hover=True, striped=False, responsive=True)


def holistic_model_explainer():
    """Visual explainer of the Coca-Cola holistic procurement model."""
    components = [
        ("📚", "Scholarships",  "$75k/yr",   "Named scholarships at Darden, McIntire, Batten, Engineering",  UVA_NAVY),
        ("💼", "Internships",   "$100k/yr",  "Structured co-op/intern pipeline (10-15 students/yr)",         UVA_ORANGE),
        ("🔬", "Sponsored Res.","Variable",  "Research awards, lab access, joint IP development",            "#1565C0"),
        ("📣", "Marketing",     "$75k+/yr",  "Brand visibility, UVA athletics sponsorship, event naming",    "#2E7D32"),
    ]
    return html.Div([
        html.Div("HOLISTIC PARTNER ENGAGEMENT MODEL", className="section-eyebrow mb-3"),
        html.P([
            "Based on the Coca-Cola case study from the Procurement Partnership framework. "
            "A holistic package bundles four engagement streams into one corporate partnership "
            "agreement — targeting ",
            html.Strong("$200–300k/yr per partner"),
            " vs. siloed one-off transactions."
        ], className="section-lead mb-3"),
        dbc.Row([
            dbc.Col(html.Div([
                html.Div(icon, style={"fontSize": "2rem", "marginBottom": "6px"}),
                html.Div(name, className="holistic-title", style={"color": color}),
                html.Div(value, className="holistic-value"),
                html.Div(desc, className="holistic-desc"),
            ], className="holistic-card", style={"borderTop": f"3px solid {color}"}),
            md=3, sm=6) for icon, name, value, desc, color in components
        ]),
        html.Div([
            html.Strong("3-Phase Implementation: "),
            html.Span("1. Discovery (needs assessment, stakeholder mapping, question bank)  →  "),
            html.Span("2. Design (package structure, pricing, contract terms)  →  "),
            html.Span("3. Implementation (activation, relationship management, annual review)"),
        ], className="phase-explainer mt-3"),
    ], className="section-block")


# ── Layout ─────────────────────────────────────────────────────────────────────
layout = html.Div([
    html.Div([
        html.H2("Procurement Pipeline", className="page-title"),
        html.P(
            "Holistic corporate engagement model: Discovery → Design → Implementation. "
            "Bundled packages targeting $200-300k/yr per partner "
            "(scholarships + internships + research + marketing).",
            className="page-subtitle"
        ),
    ], className="page-header"),

    # ── Pipeline KPIs ─────────────────────────────────────────────────────────
    html.Div(id="proc-kpis"),

    # ── Holistic Model Explainer ───────────────────────────────────────────────
    holistic_model_explainer(),

    # ── Filters ───────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            dbc.Label("Filter by Stage", className="dropdown-label"),
            dcc.Dropdown(
                id="proc-stage-dd",
                options=[{"label": f"{STAGE_ICONS.get(s,'')} {s}", "value": s}
                         for s in ["All"] + STAGES],
                value="All", clearable=False, className="cfr-dropdown",
            ),
        ], md=3),
        dbc.Col([
            dbc.Label("Filter by Sector", className="dropdown-label"),
            dcc.Dropdown(
                id="proc-sector-dd",
                options=[{"label": s, "value": s}
                         for s in ["All"] + sorted(SECTOR_COLORS.keys())],
                value="All", clearable=False, className="cfr-dropdown",
            ),
        ], md=3),
    ], className="filter-row mb-3"),

    # ── Charts Row 1 ──────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            html.Div([dcc.Graph(id="proc-funnel",  config={"displayModeBar": False})],
                     className="chart-card"),
        ], md=4),
        dbc.Col([
            html.Div([dcc.Graph(id="proc-scatter", config={"displayModeBar": False})],
                     className="chart-card"),
        ], md=8),
    ], className="mb-3"),

    # ── Charts Row 2 ──────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            html.Div([dcc.Graph(id="proc-value-bar", config={"displayModeBar": False})],
                     className="chart-card"),
        ], md=6),
        dbc.Col([
            html.Div([dcc.Graph(id="proc-sector-chart", config={"displayModeBar": False})],
                     className="chart-card"),
        ], md=6),
    ], className="mb-3"),

    # ── Partner Table ─────────────────────────────────────────────────────────
    html.Div([
        html.Div("PARTNER PIPELINE DETAIL", className="section-eyebrow mb-3"),
        html.Div(id="proc-table"),
    ], className="section-block"),

], className="cfr-page")


@callback(
    Output("proc-funnel",       "figure"),
    Output("proc-scatter",      "figure"),
    Output("proc-value-bar",    "figure"),
    Output("proc-sector-chart", "figure"),
    Output("proc-table",        "children"),
    Output("proc-kpis",         "children"),
    Input("proc-stage-dd",  "value"),
    Input("proc-sector-dd", "value"),
)
def update_proc(stage, sector):
    df     = load_partners()
    scored = load_scored_partners("percentile")

    # KPIs
    active_v  = df[df["procurement_stage"] == "Active"]["est_annual_value_k"].sum()
    pipeline_v = df[df["procurement_stage"] != "Active"]["est_annual_value_k"].sum()
    total_v   = df["est_annual_value_k"].sum()
    active_ct = (df["procurement_stage"] == "Active").sum()

    kpis = dbc.Row([
        dbc.Col(html.Div([
            html.Div(str(active_ct), className="stat-value", style={"color": UVA_NAVY}),
            html.Div("Active Partners", className="stat-label"),
        ], className="stat-card"), md=3),
        dbc.Col(html.Div([
            html.Div(f"${active_v/1000:.1f}M", className="stat-value", style={"color": UVA_ORANGE}),
            html.Div("Active Annual Value", className="stat-label"),
        ], className="stat-card"), md=3),
        dbc.Col(html.Div([
            html.Div(f"${pipeline_v/1000:.1f}M", className="stat-value", style={"color": "#2E7D32"}),
            html.Div("Pipeline Value (non-active)", className="stat-label"),
        ], className="stat-card"), md=3),
        dbc.Col(html.Div([
            html.Div(f"${total_v/1000:.1f}M", className="stat-value", style={"color": UVA_NAVY}),
            html.Div("Total Portfolio Est. Value", className="stat-label"),
        ], className="stat-card"), md=3),
    ], className="mb-3")

    return (
        pipeline_funnel(df),
        partner_stage_scatter(df, scored),
        pipeline_value_bar(df),
        sector_pipeline_chart(df),
        pipeline_partner_table(df, scored, stage, sector),
        kpis,
    )
