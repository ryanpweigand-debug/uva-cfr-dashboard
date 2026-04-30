"""
Recommendations Page — CFR action registry with priority, value, and timeline.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "components"))

from queries import load_recommendations, load_partners, PRIORITY_FOUNDATIONS
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
    "Foundation":  "#E57200",   # UVA Orange — foundation-specific ask strategy
    "Talent":      "#2E7D32",
    "Strategic":   UVA_ORANGE,
    "Procurement": "#C62828",
}
CATEGORIES  = ["All", "Foundation", "Research", "Philanthropy", "Talent", "Strategic", "Procurement"]
PRIORITIES  = ["All", "High", "Medium", "Low"]
STATUSES    = ["All", "Open", "In Progress", "Closed"]


def rec_status_board(recs):
    """
    Kanban-style 3-column status board replacing the hard-to-read stacked bar.
    Each column = Open / In Progress / Closed.
    Each row = a pill showing priority color + category + title snippet.
    """
    columns = []
    for status, color in STATUS_COLORS.items():
        subset = recs[recs["status"] == status].sort_values("priority",
            key=lambda s: s.map({"High": 0, "Medium": 1, "Low": 2}))

        pills = []
        for _, row in subset.iterrows():
            pc   = PRIORITY_COLORS.get(row["priority"], "#999")
            cc   = CATEGORY_COLORS.get(row["category"], "#999")
            title_short = row["title"][:52] + "…" if len(row["title"]) > 52 else row["title"]
            pills.append(html.Div([
                html.Div([
                    html.Span(row["priority"][0], style={
                        "background": pc, "color": "#fff",
                        "fontSize": "0.58rem", "fontWeight": "800",
                        "width": "16px", "height": "16px",
                        "borderRadius": "3px", "display": "inline-flex",
                        "alignItems": "center", "justifyContent": "center",
                        "flexShrink": "0", "marginRight": "6px",
                    }),
                    html.Span(row["category"], style={
                        "fontSize": "0.6rem", "color": cc,
                        "fontWeight": "700", "marginRight": "4px",
                        "flexShrink": "0",
                    }),
                    html.Span(title_short, style={
                        "fontSize": "0.68rem", "color": TEXT_DARK,
                        "lineHeight": "1.3",
                    }),
                ], style={"display": "flex", "alignItems": "flex-start"}),
            ], style={
                "padding": "7px 10px",
                "marginBottom": "5px",
                "background": LIGHT_BG,
                "borderRadius": "5px",
                "borderLeft": f"3px solid {pc}",
            }))

        if not pills:
            pills = [html.Div("—", style={"fontSize": "0.75rem", "color": TEXT_LIGHT,
                                           "padding": "8px 0"})]

        columns.append(dbc.Col([
            html.Div([
                html.Div([
                    html.Span("●", style={"color": color, "marginRight": "6px",
                                           "fontSize": "0.75rem"}),
                    html.Span(status.upper(), style={
                        "fontFamily": "var(--font-brand)", "fontWeight": "800",
                        "fontSize": "0.68rem", "color": color,
                        "letterSpacing": "0.07em",
                    }),
                    html.Span(f"  {len(subset)}", style={
                        "fontSize": "0.68rem", "color": TEXT_MID,
                        "fontWeight": "600", "marginLeft": "6px",
                    }),
                ], style={"display": "flex", "alignItems": "center",
                          "marginBottom": "10px", "paddingBottom": "8px",
                          "borderBottom": f"2px solid {color}"}),
                html.Div(pills, style={"maxHeight": "280px", "overflowY": "auto"}),
            ], style={
                "background": CARD_BG,
                "border": f"1px solid {BORDER}",
                "borderTop": f"3px solid {color}",
                "borderRadius": "8px",
                "padding": "14px",
                "height": "100%",
            }),
        ], md=4, className="mb-3"))

    return dbc.Row(columns)


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


def foundation_rec_spotlight(recs_df, partners_df):
    """
    Dedicated panel for Foundation-category recommendations, grouped by foundation.
    Shows the UVA ask strategy derived from each foundation's grant history.
    """
    fnd_recs = recs_df[recs_df["category"] == "Foundation"].copy()
    if fnd_recs.empty:
        return html.Span()

    # Sort: High first, then by partner name
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    fnd_recs["_pri_ord"] = fnd_recs["priority"].map(priority_order)

    # Group by partner
    groups = {}
    no_partner = []
    for _, row in fnd_recs.sort_values("_pri_ord").iterrows():
        pid = row.get("partner_id")
        if pd.notna(pid) and pid:
            pm = partners_df[partners_df["id"] == int(pid)]
            pname = pm.iloc[0]["name"] if not pm.empty else "Unknown"
            groups.setdefault(pname, []).append(row)
        else:
            no_partner.append(row)

    cards = []
    for pname, rows in sorted(groups.items()):
        is_priority = pname in PRIORITY_FOUNDATIONS
        priority_badge = html.Span([
            html.Span("★ ", style={"color": UVA_ORANGE}),
            html.Span("Priority Foundation", style={
                "fontSize": "0.6rem", "fontWeight": "700",
                "color": UVA_ORANGE, "letterSpacing": "0.04em",
            }),
        ], style={
            "background": "rgba(229,114,0,0.08)",
            "border": "1px solid rgba(229,114,0,0.3)",
            "borderRadius": "8px", "padding": "1px 7px",
            "display": "inline-flex", "alignItems": "center",
            "marginLeft": "8px",
        }) if is_priority else html.Span()

        rec_rows = []
        for row in rows:
            pc  = PRIORITY_COLORS.get(row["priority"], "#999")
            sc  = STATUS_COLORS.get(row["status"], "#999")
            val = row["est_value_k"]
            val_str = f"${val/1000:.1f}M" if val >= 1000 else (f"${val:.0f}K" if val > 0 else "—")
            rec_rows.append(html.Div([
                html.Div([
                    # Priority dot
                    html.Span(row["priority"][0], style={
                        "background": pc, "color": "#fff",
                        "fontSize": "0.58rem", "fontWeight": "800",
                        "width": "16px", "height": "16px",
                        "borderRadius": "3px", "display": "inline-flex",
                        "alignItems": "center", "justifyContent": "center",
                        "flexShrink": "0", "marginRight": "8px",
                    }),
                    html.Div([
                        html.Div(row["title"], style={
                            "fontWeight": "700", "fontSize": "0.8rem",
                            "color": TEXT_DARK, "marginBottom": "3px",
                        }),
                        html.Div(row.get("description", ""), style={
                            "fontSize": "0.71rem", "color": TEXT_MID,
                            "lineHeight": "1.45",
                        }),
                    ], style={"flex": "1"}),
                    html.Div([
                        html.Div(val_str, style={
                            "fontWeight": "800", "fontSize": "0.82rem",
                            "color": "#2E7D32", "textAlign": "right",
                        }),
                        html.Div([
                            html.Span(row["status"], style={
                                "fontSize": "0.6rem", "fontWeight": "700",
                                "color": sc, "border": f"1px solid {sc}",
                                "borderRadius": "4px", "padding": "1px 5px",
                            }),
                        ], style={"textAlign": "right", "marginTop": "3px"}),
                        html.Div(f"🎯 {row.get('timeline','—')}", style={
                            "fontSize": "0.62rem", "color": TEXT_LIGHT,
                            "marginTop": "3px", "textAlign": "right",
                        }),
                    ], style={"minWidth": "90px", "marginLeft": "12px"}),
                ], style={"display": "flex", "alignItems": "flex-start"}),
            ], style={
                "padding": "10px 12px",
                "marginBottom": "6px",
                "background": LIGHT_BG,
                "borderRadius": "6px",
                "borderLeft": f"3px solid {pc}",
            }))

        top_priority = rows[0]["priority"] if rows else "Low"
        top_color = PRIORITY_COLORS.get(top_priority, "#999")

        cards.append(html.Div([
            html.Div([
                html.Div([
                    html.Span("🏛️ ", style={"fontSize": "0.85rem"}),
                    html.Span(pname, style={
                        "fontFamily": "var(--font-brand)", "fontWeight": "700",
                        "fontSize": "0.9rem", "color": UVA_NAVY,
                    }),
                    priority_badge,
                ], style={"display": "flex", "alignItems": "center", "flex": "1",
                          "flexWrap": "wrap", "gap": "4px"}),
                html.Span(f"{len(rows)} ask{'s' if len(rows)!=1 else ''}", style={
                    "fontSize": "0.65rem", "color": TEXT_MID, "fontWeight": "600",
                }),
            ], style={"display": "flex", "justifyContent": "space-between",
                      "alignItems": "center", "marginBottom": "10px"}),
            html.Div(rec_rows),
        ], style={
            "background": CARD_BG,
            "border": f"1px solid {BORDER}",
            "borderLeft": f"4px solid {top_color}",
            "borderRadius": "8px",
            "padding": "14px 16px",
            "marginBottom": "12px",
        }))

    if not cards:
        return html.Span()

    total_val = fnd_recs["est_value_k"].sum()
    high_ct   = (fnd_recs["priority"] == "High").sum()
    val_str   = f"${total_val/1000:.1f}M" if total_val >= 1000 else f"${total_val:.0f}K"

    return html.Div([
        html.Div([
            html.Div([
                html.Span("🏛️", style={"fontSize": "1rem", "marginRight": "8px"}),
                html.Span("FOUNDATION ASK STRATEGY", style={
                    "fontFamily": "var(--font-brand)", "fontWeight": "800",
                    "fontSize": "0.78rem", "color": UVA_NAVY, "letterSpacing": "0.08em",
                }),
                html.Span("Derived from grant history + UVA institutional strengths",
                          style={"fontSize": "0.65rem", "color": TEXT_MID, "marginLeft": "10px"}),
            ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
            html.Div([
                html.Span(f"{len(fnd_recs)} asks", style={
                    "fontSize": "0.7rem", "fontWeight": "700", "color": UVA_ORANGE,
                    "marginRight": "12px",
                }),
                html.Span(f"{high_ct} high priority", style={
                    "fontSize": "0.7rem", "fontWeight": "700", "color": "#C62828",
                    "marginRight": "12px",
                }),
                html.Span(f"{val_str} pipeline", style={
                    "fontSize": "0.7rem", "fontWeight": "700", "color": "#2E7D32",
                }),
            ]),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "marginBottom": "16px"}),
        html.Div(cards),
    ], style={
        "background": "linear-gradient(135deg, rgba(35,45,75,0.03) 0%, rgba(229,114,0,0.02) 100%)",
        "border": f"1px solid {BORDER}",
        "borderRadius": "10px",
        "padding": "18px 20px",
        "marginBottom": "20px",
    })


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

    # Foundation Ask Strategy spotlight (shown when category = Foundation or All)
    html.Div(id="rec-foundation-spotlight", className="mb-3"),

    # Status board (kanban) + value chart
    html.Div(id="rec-status-board", className="mb-3"),
    dbc.Row([
        dbc.Col([
            html.Div([dcc.Graph(id="rec-value-chart", config={"displayModeBar": False})],
                     className="chart-card"),
        ], md=7),
        dbc.Col([
            html.Div([dcc.Graph(id="rec-timeline", config={"displayModeBar": False})],
                     className="chart-card"),
        ], md=5),
    ], className="mb-3"),

    # Cards
    html.Div("RECOMMENDATION REGISTRY", className="section-eyebrow mb-3"),
    html.Div(id="rec-cards-container"),

], className="cfr-page")


@callback(
    Output("rec-foundation-spotlight", "children"),
    Output("rec-status-board",         "children"),
    Output("rec-value-chart",          "figure"),
    Output("rec-timeline",             "figure"),
    Output("rec-cards-container",      "children"),
    Output("rec-kpis",                 "children"),
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

    # Foundation spotlight — show when viewing All or Foundation category
    fnd_spotlight = foundation_rec_spotlight(recs_f, df_raw) if cat in ("All", "Foundation") else html.Span()

    # Non-foundation recs for kanban/charts (exclude Foundation category from the generic board)
    recs_non_fnd = recs_f[recs_f["category"] != "Foundation"]

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
        for _, row in recs_non_fnd.iterrows()
    ]) if not recs_non_fnd.empty else html.Div(
        "No recommendations match the selected filters.",
        className="placeholder-text"
    )

    return (
        fnd_spotlight,
        rec_status_board(recs_non_fnd),
        value_by_category_chart(recs),
        timeline_chart(recs_non_fnd),
        cards,
        kpis,
    )
