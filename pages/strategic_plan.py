"""
CFR Strategic Plan Page — 6 priorities scorecard built around the CFR Strategic Plan Framework doc.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "components"))

from queries import (
    load_strategic_priorities, load_scored_partners, sp_partner_alignment,
    SECTOR_COLORS, SP_COLS, SP_LABELS, PRIORITY_FOUNDATIONS,
)
from charts import (
    UVA_NAVY, UVA_ORANGE, LIGHT_BG, CARD_BG, TEXT_DARK, TEXT_MID, TEXT_LIGHT,
    GRID_COLOR, BORDER, CHART_FONT, chart_layout, make_gauge,
)

dash.register_page(__name__, path="/strategic-plan", name="Strategic Plan", order=2)

_TAB  = dict(backgroundColor="transparent", border="none",
             borderBottom="3px solid transparent", color=TEXT_MID,
             fontWeight="600", fontFamily=CHART_FONT, fontSize="0.88rem",
             padding="12px 24px")
_TSEL = {**_TAB, "color": UVA_NAVY,
         "borderBottom": f"3px solid {UVA_ORANGE}", "fontWeight": "700"}

SP_ICONS    = ["🏛️", "🚪", "📊", "👥", "🗄️", "📣"]
SP_COLORS   = [UVA_NAVY, UVA_ORANGE, "#1565C0", "#2E7D32", "#6A1B9A", "#BF360C"]
STATUS_COLORS = {
    "Complete":    "#2E7D32",
    "In Progress": UVA_ORANGE,
    "Not Started": "#78909C",
}


def sp_priority_cards(sp_df):
    cards = []
    for i, (_, row) in enumerate(sp_df.iterrows()):
        color  = SP_COLORS[i % len(SP_COLORS)]
        icon   = SP_ICONS[i % len(SP_ICONS)]
        status = row["status"]
        pct    = row["progress_pct"]
        sc     = STATUS_COLORS.get(status, "#999")

        card = dbc.Col(html.Div([
            html.Div([
                html.Span(icon, style={"fontSize": "1.4rem", "marginRight": "8px"}),
                html.Span(row["code"], className="sp-code", style={"color": color}),
            ], className="sp-card-header"),
            html.Div(row["title"], className="sp-card-title"),
            html.Div(row["description"][:160] + "…" if len(row.get("description","")) > 160 else row.get("description",""),
                     className="sp-card-desc"),
            html.Div([
                html.Div([
                    html.Div(style={"width": f"{pct:.0f}%", "height": "6px",
                                    "background": color, "borderRadius": "3px",
                                    "transition": "width 0.5s ease"}),
                ], className="sp-progress-bg"),
                html.Div([
                    html.Span(f"{pct:.0f}%", style={"fontWeight": "700", "color": color,
                                                    "fontSize": "12px"}),
                    html.Span(f" {status}", style={"color": sc, "fontSize": "11px",
                                                    "marginLeft": "6px"}),
                ], className="d-flex align-items-center mt-1"),
            ], className="mt-2"),
            html.Div([
                html.Span(f"👤 {row.get('owner','TBD')}", className="sp-meta me-2"),
                html.Span(f"🎯 {row.get('target_date','TBD')}", className="sp-meta"),
            ], className="sp-meta-row mt-2"),
        ], className="sp-card", style={"borderTop": f"4px solid {color}"}),
        md=4, sm=6, className="mb-3")
        cards.append(card)
    return dbc.Row(cards)


def sp_radar_chart(sp_df):
    labels = [row["code"] for _, row in sp_df.iterrows()]
    vals   = [row["progress_pct"] for _, row in sp_df.iterrows()]
    cats_c = labels + [labels[0]]
    vals_c = vals   + [vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_c, theta=cats_c,
        fill="toself",
        fillcolor="rgba(35,45,75,0.15)",
        line=dict(color=UVA_NAVY, width=2),
        hovertemplate="%{theta}: %{r:.0f}% complete<extra></extra>",
        name="Current Progress",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[100]*len(labels)+[100],
        theta=cats_c,
        fill="toself",
        fillcolor="rgba(229,114,0,0.05)",
        line=dict(color=UVA_ORANGE, width=1, dash="dot"),
        name="Target (100%)",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=LIGHT_BG,
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=9, color=TEXT_LIGHT),
                            gridcolor=GRID_COLOR),
            angularaxis=dict(tickfont=dict(size=12, color=TEXT_DARK, family=CHART_FONT),
                             gridcolor=GRID_COLOR),
        ),
        paper_bgcolor=CARD_BG,
        height=380,
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center",
                    font=dict(size=10)),
        margin=dict(l=60, r=60, t=40, b=60),
        font=dict(family=CHART_FONT),
        title=dict(text="<span style='font-size:13px;font-weight:700'>Strategic Plan Progress Radar</span>",
                   x=0.5, xanchor="center"),
    )
    return fig


def sp_partner_alignment_chart():
    """Which SP priorities do partners score highest on? (avg bar — kept for radar row)"""
    df = sp_partner_alignment()
    colors = SP_COLORS[:len(df)]
    fig = go.Figure(go.Bar(
        x=df["mean_score"], y=df["priority"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}/10" for v in df["mean_score"]],
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f} avg partner score<extra></extra>",
    ))
    fig.update_layout(**chart_layout("Partner Alignment by SP Priority (avg 0–10)", height=320))
    fig.update_xaxes(range=[0, 11])
    return fig


# ── SP partner spotlight (replaces 30-partner bar chart) ─────────────────────
def sp_mini_bar(score, color):
    pct = score / 10 * 100
    return html.Div(
        html.Div(style={
            "width": f"{max(pct, 2):.1f}%", "height": "100%",
            "background": color, "borderRadius": "2px",
        }),
        style={
            "background": "rgba(0,0,0,0.07)", "height": "5px",
            "borderRadius": "2px", "overflow": "hidden", "marginTop": "3px",
        }
    )


def sp_spotlight_row(name, score, color):
    return html.Div([
        html.Div([
            html.Span(name, style={
                "fontWeight": "600", "fontSize": "0.78rem", "color": UVA_NAVY,
                "whiteSpace": "nowrap", "overflow": "hidden",
                "textOverflow": "ellipsis", "flex": "1",
            }),
            html.Span(f"{score:.1f}", style={
                "fontWeight": "700", "fontSize": "0.75rem",
                "color": color, "marginLeft": "8px", "flexShrink": "0",
            }),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "2px"}),
        sp_mini_bar(score, color),
    ], style={"padding": "7px 0", "borderBottom": "1px solid rgba(0,0,0,0.06)"})


def sp_partner_spotlight(method="percentile", partner_type="Corporate"):
    df = load_scored_partners(method, partner_type)

    cols = []
    for i, (sp_col, label, icon, color) in enumerate(
        zip(SP_COLS, SP_LABELS, SP_ICONS, SP_COLORS)
    ):
        top5 = df.nlargest(5, sp_col)[["name", sp_col]]
        code = f"SP-0{i+1}"

        rows = [sp_spotlight_row(r["name"], r[sp_col], color)
                for _, r in top5.iterrows()]

        cols.append(dbc.Col([
            html.Div([
                html.Div([
                    html.Span(icon, style={"fontSize": "1rem", "marginRight": "5px"}),
                    html.Span(code, style={
                        "fontFamily": "var(--font-brand)", "fontWeight": "800",
                        "fontSize": "0.78rem", "color": color, "marginRight": "5px",
                    }),
                    html.Span(SP_LABELS[i].split(" ", 1)[-1], style={
                        "fontSize": "0.68rem", "color": TEXT_MID,
                        "fontWeight": "600", "lineHeight": "1.2",
                    }),
                ], style={"display": "flex", "alignItems": "flex-start",
                          "marginBottom": "10px", "flexWrap": "wrap", "gap": "2px"}),
                html.Div(rows),
            ], style={
                "borderTop": f"3px solid {color}",
                "padding": "12px 14px",
                "background": CARD_BG,
                "borderRadius": "0 0 8px 8px",
                "height": "100%",
            }),
        ], md=4, sm=6, xs=12, className="mb-3"))

    # Two rows of 3
    return html.Div([
        dbc.Row(cols[:3]),
        dbc.Row(cols[3:]),
    ])


def foundation_sp_summary():
    """
    Foundation-specific strategic plan view:
    Shows how foundation partners map to SP priorities, with a priority watch strip.
    """
    df = load_scored_partners("percentile", "Foundation")

    # SP alignment bars (avg score per priority, foundation partners only)
    sp_rows = []
    for i, (sp_col, label, icon, color) in enumerate(
        zip(SP_COLS, SP_LABELS, SP_ICONS, SP_COLORS)
    ):
        avg = df[sp_col].mean() if not df.empty else 0
        pct = avg / 10 * 100
        sp_rows.append(html.Div([
            html.Div([
                html.Span(icon, style={"marginRight": "6px", "fontSize": "0.85rem"}),
                html.Span(f"SP-0{i+1}", style={
                    "fontFamily": "var(--font-brand)", "fontWeight": "800",
                    "fontSize": "0.72rem", "color": color, "marginRight": "6px",
                }),
                html.Span(label.split(" ", 1)[-1], style={
                    "fontSize": "0.7rem", "color": TEXT_MID, "fontWeight": "600",
                }),
            ], style={"display": "flex", "alignItems": "center",
                      "marginBottom": "4px", "flexWrap": "wrap"}),
            html.Div([
                html.Div(
                    html.Div(style={
                        "width": f"{max(pct, 2):.1f}%", "height": "100%",
                        "background": color, "borderRadius": "3px",
                        "transition": "width 0.5s ease",
                    }),
                    style={
                        "flex": "1", "height": "8px",
                        "background": "rgba(0,0,0,0.07)",
                        "borderRadius": "3px", "overflow": "hidden",
                    }
                ),
                html.Span(f"{avg:.1f}/10", style={
                    "fontSize": "0.68rem", "fontWeight": "700",
                    "color": color, "marginLeft": "8px", "flexShrink": "0",
                }),
            ], style={"display": "flex", "alignItems": "center"}),
        ], style={"marginBottom": "12px"}))

    # Top 5 foundations by composite score
    top5 = df.nlargest(5, "composite_score")[["name", "composite_score", "tier", "tier_color"]]
    top_rows = []
    for _, r in top5.iterrows():
        top_rows.append(html.Div([
            html.Div([
                html.Span(r["name"], style={
                    "fontWeight": "600", "fontSize": "0.78rem",
                    "color": UVA_NAVY, "flex": "1",
                    "whiteSpace": "nowrap", "overflow": "hidden",
                    "textOverflow": "ellipsis",
                }),
                html.Span(r["tier"], style={
                    "background": r["tier_color"], "color": "#fff",
                    "fontSize": "0.55rem", "fontWeight": "700",
                    "padding": "1px 6px", "borderRadius": "3px",
                    "marginLeft": "8px", "flexShrink": "0",
                }),
                html.Span(f"{r['composite_score']:.0f}pt", style={
                    "fontSize": "0.68rem", "color": r["tier_color"],
                    "fontWeight": "700", "marginLeft": "6px", "flexShrink": "0",
                }),
            ], style={"display": "flex", "alignItems": "center"}),
        ], style={
            "padding": "7px 0",
            "borderBottom": f"1px solid {BORDER}",
        }))

    # Priority coverage — how many of 16 priority foundations are active
    priority_names_lower = {n.strip().lower() for n in PRIORITY_FOUNDATIONS}
    active_names_lower   = set(df["name"].str.strip().str.lower())
    covered = len(priority_names_lower & active_names_lower)
    total_priority = len(PRIORITY_FOUNDATIONS)

    return dbc.Row([
        dbc.Col([
            html.Div([
                html.Div("SP PRIORITY ALIGNMENT", className="section-eyebrow mb-3"),
                html.Div(sp_rows),
                html.Div(
                    "Average SP alignment score across all active foundation partners (0–10).",
                    style={"fontSize": "0.62rem", "color": TEXT_LIGHT,
                           "marginTop": "8px", "fontStyle": "italic"},
                ),
            ], style={
                "background": CARD_BG, "border": f"1px solid {BORDER}",
                "borderRadius": "8px", "padding": "16px 18px", "height": "100%",
            }),
        ], md=6, className="mb-3"),

        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div([
                    html.Div(str(len(df)), className="stat-value",
                             style={"color": UVA_NAVY}),
                    html.Div("Active Foundations", className="stat-label"),
                ], className="stat-card"), md=6, className="mb-3"),
                dbc.Col(html.Div([
                    html.Div(f"{covered}/{total_priority}", className="stat-value",
                             style={"color": UVA_ORANGE}),
                    html.Div("Priority Foundations", className="stat-label"),
                    html.Div("in active pipeline", className="stat-sub"),
                ], className="stat-card"), md=6, className="mb-3"),
            ]),
            html.Div([
                html.Div("TOP FOUNDATIONS BY SCORE", className="section-eyebrow mb-2"),
                html.Div(top_rows),
            ], style={
                "background": CARD_BG, "border": f"1px solid {BORDER}",
                "borderRadius": "8px", "padding": "14px 16px",
            }),
        ], md=6, className="mb-3"),
    ])


def sp_bubble_chart():
    """Importance (weight) vs. progress scatter."""
    sp = load_strategic_priorities()
    fig = go.Figure()
    for i, (_, row) in enumerate(sp.iterrows()):
        color = SP_COLORS[i % len(SP_COLORS)]
        fig.add_trace(go.Scatter(
            x=[row["priority_weight"]],
            y=[row["progress_pct"]],
            mode="markers+text",
            marker=dict(size=40, color=color, opacity=0.85,
                        line=dict(width=2, color="#fff")),
            text=[row["code"]],
            textposition="middle center",
            textfont=dict(color="#fff", size=10, family=CHART_FONT),
            name=row["code"],
            hovertemplate=(
                f"<b>{row['code']}: {row['title']}</b><br>"
                f"Progress: {row['progress_pct']:.0f}%<br>"
                f"Priority Weight: {row['priority_weight']}<br>"
                f"Status: {row['status']}<extra></extra>"
            ),
        ))
    lo = chart_layout("Priority Importance vs. Completion", height=360)
    lo["xaxis"]["title"] = "Priority Weight (relative importance)"
    lo["yaxis"]["title"] = "% Complete"
    lo["yaxis"]["range"] = [0, 110]
    lo["showlegend"] = False
    fig.update_layout(**lo)
    fig.add_hline(y=50, line_dash="dot", line_color=TEXT_LIGHT, line_width=1,
                  annotation_text="50% milestone", annotation_position="left")
    return fig


# ── Layout ─────────────────────────────────────────────────────────────────────
def build_layout():
    sp = load_strategic_priorities()

    # Overall progress gauge
    avg_pct = sp["progress_pct"].mean()
    gauge_fig = make_gauge(avg_pct, "Overall CFR Plan Progress", max_val=100,
                           color=UVA_NAVY, height=200)

    # Completion summary
    complete  = (sp["status"] == "Complete").sum()
    in_prog   = (sp["status"] == "In Progress").sum()
    not_start = (sp["status"] == "Not Started").sum()

    return html.Div([
        html.Div([
            html.H2("CFR Strategic Plan", className="page-title"),
            html.P(
                "Six strategic priorities driving CFR's transformation into a "
                "specialist-led, data-driven corporate engagement function. "
                "Aligned with peer benchmarks from Georgia Tech, UT-Austin, and UNC-Chapel Hill.",
                className="page-subtitle"
            ),
        ], className="page-header"),

        # ── Summary Strip ─────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(html.Div([
                dcc.Graph(figure=gauge_fig, config={"displayModeBar": False}),
            ], className="chart-card text-center"), md=3),
            dbc.Col([
                dbc.Row([
                    dbc.Col(html.Div([
                        html.Div("6", className="stat-value", style={"color": UVA_NAVY}),
                        html.Div("Strategic Priorities", className="stat-label"),
                    ], className="stat-card"), md=4),
                    dbc.Col(html.Div([
                        html.Div(str(in_prog), className="stat-value",
                                 style={"color": UVA_ORANGE}),
                        html.Div("In Progress", className="stat-label"),
                    ], className="stat-card"), md=4),
                    dbc.Col(html.Div([
                        html.Div(str(not_start), className="stat-value",
                                 style={"color": "#78909C"}),
                        html.Div("Not Started", className="stat-label"),
                    ], className="stat-card"), md=4),
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col(html.Div([
                        html.Div(str(complete), className="stat-value",
                                 style={"color": "#2E7D32"}),
                        html.Div("Complete", className="stat-label"),
                    ], className="stat-card"), md=4),
                    dbc.Col(html.Div([
                        html.Div(f"{avg_pct:.0f}%", className="stat-value",
                                 style={"color": UVA_NAVY}),
                        html.Div("Avg Completion", className="stat-label"),
                    ], className="stat-card"), md=4),
                    dbc.Col(html.Div([
                        html.Div("2026", className="stat-value",
                                 style={"color": UVA_ORANGE}),
                        html.Div("Target Complete", className="stat-label"),
                    ], className="stat-card"), md=4),
                ]),
            ], md=9),
        ], className="mb-4"),

        # ── Priority Cards ─────────────────────────────────────────────────────
        html.Div("STRATEGIC PRIORITIES", className="section-eyebrow mb-3"),
        sp_priority_cards(sp),

        # ── Charts Row ─────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Graph(id="sp-radar", figure=sp_radar_chart(sp),
                              config={"displayModeBar": False}),
                ], className="chart-card"),
            ], md=4),
            dbc.Col([
                html.Div([
                    dcc.Graph(id="sp-partner-align", figure=sp_partner_alignment_chart(),
                              config={"displayModeBar": False}),
                ], className="chart-card"),
            ], md=4),
            dbc.Col([
                html.Div([
                    dcc.Graph(id="sp-bubble", figure=sp_bubble_chart(),
                              config={"displayModeBar": False}),
                ], className="chart-card"),
            ], md=4),
        ], className="mb-3"),

        # ── SP Partner Spotlight — top 5 partners per priority ────────────────
        html.Div([
            html.Div("PARTNER ALIGNMENT BY STRATEGIC PRIORITY", className="section-eyebrow mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Scoring Method", className="dropdown-label"),
                    dcc.Dropdown(
                        id="sp-method-dd",
                        options=[
                            {"label": "Percentile (Method 2)", "value": "percentile"},
                            {"label": "Judgment (Method 1)",   "value": "judgment"},
                        ],
                        value="percentile", clearable=False, className="cfr-dropdown",
                    ),
                ], md=3),
            ], className="mb-3"),
            dcc.Tabs(
                id="sp-type-tabs", value="Corporate",
                style={"borderBottom": f"1px solid {BORDER}", "marginBottom": "20px",
                       "backgroundColor": CARD_BG},
                children=[
                    dcc.Tab(label="🏢  Corporate Relations", value="Corporate",
                            style=_TAB, selected_style=_TSEL),
                    dcc.Tab(label="🏛️  Foundation Relations", value="Foundation",
                            style=_TAB, selected_style=_TSEL),
                ],
            ),
            html.Div(id="sp-partner-spotlight"),
        ], className="section-block"),

    ], className="cfr-page")


layout = build_layout  # callable — Dash calls this lazily at request time


@callback(
    Output("sp-partner-spotlight", "children"),
    Input("sp-method-dd",   "value"),
    Input("sp-type-tabs",   "value"),
)
def sp_partner_chart(method, tab):
    if tab == "Foundation":
        return foundation_sp_summary()
    return sp_partner_spotlight(method, "Corporate")
