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
    PRIORITY_FOUNDATIONS, load_foundation_grants,
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


# ── CFR Priority Foundation Watch Panel ───────────────────────────────────────
def scoring_priority_watch(scored_df):
    """
    Compact priority watch strip for the Partner Scoring Foundation tab.
    Shows tier badge for active foundations; dashed for prospects.
    """
    active_names = set(scored_df["name"].str.strip().str.lower())

    badges = []
    for name in PRIORITY_FOUNDATIONS:
        is_active = name.strip().lower() in active_names
        if is_active:
            row = scored_df[scored_df["name"].str.strip().str.lower() == name.strip().lower()].iloc[0]
            score = row["composite_score"]
            tier  = row["tier"]
            color = row["tier_color"]
            short = name.split()[-1] if len(name) > 22 else name  # last word as abbreviation
            badge = html.Div([
                html.Div(name, style={
                    "fontWeight": "700", "fontSize": "0.7rem",
                    "color": UVA_NAVY, "lineHeight": "1.2",
                    "marginBottom": "5px",
                    "whiteSpace": "nowrap", "overflow": "hidden",
                    "textOverflow": "ellipsis",
                }),
                html.Div([
                    html.Span(tier, style={
                        "background": color, "color": "#fff",
                        "fontSize": "0.58rem", "fontWeight": "700",
                        "padding": "1px 6px", "borderRadius": "3px",
                        "marginRight": "5px",
                    }),
                    html.Span(f"{score:.0f}pt", style={
                        "fontSize": "0.68rem", "color": color, "fontWeight": "700",
                    }),
                ], style={"display": "flex", "alignItems": "center"}),
            ], style={
                "border": f"1px solid {color}",
                "borderTop": f"3px solid {color}",
                "borderRadius": "6px",
                "padding": "8px 12px",
                "background": CARD_BG,
                "minWidth": "140px",
                "maxWidth": "200px",
                "flex": "1",
            })
        else:
            badge = html.Div([
                html.Div(name, style={
                    "fontWeight": "600", "fontSize": "0.7rem",
                    "color": TEXT_MID, "lineHeight": "1.2",
                    "marginBottom": "5px",
                    "whiteSpace": "nowrap", "overflow": "hidden",
                    "textOverflow": "ellipsis",
                }),
                html.Div("Prospect", style={
                    "fontSize": "0.62rem", "color": TEXT_LIGHT, "fontStyle": "italic",
                }),
            ], style={
                "border": f"1px dashed {BORDER}",
                "borderTop": f"3px dashed {BORDER}",
                "borderRadius": "6px",
                "padding": "8px 12px",
                "background": LIGHT_BG,
                "minWidth": "140px",
                "maxWidth": "200px",
                "flex": "1",
                "opacity": "0.7",
            })
        badges.append(badge)

    active_ct  = sum(1 for n in PRIORITY_FOUNDATIONS if n.strip().lower() in active_names)
    prospect_ct = len(PRIORITY_FOUNDATIONS) - active_ct

    return html.Div([
        html.Div([
            html.Div([
                html.Span("★", style={"color": UVA_ORANGE, "marginRight": "6px",
                                      "fontSize": "0.9rem"}),
                html.Span("CFR PRIORITY FOUNDATION WATCH", style={
                    "fontFamily": "var(--font-brand)", "fontWeight": "800",
                    "fontSize": "0.72rem", "color": UVA_NAVY, "letterSpacing": "0.08em",
                }),
            ], style={"display": "flex", "alignItems": "center"}),
            html.Div([
                html.Span(f"{active_ct} active", style={
                    "fontSize": "0.7rem", "color": "#2E7D32",
                    "fontWeight": "700", "marginRight": "10px",
                }),
                html.Span(f"{prospect_ct} prospects", style={
                    "fontSize": "0.7rem", "color": TEXT_MID, "fontWeight": "600",
                }),
            ]),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "marginBottom": "12px"}),
        html.Div(badges, style={
            "display": "flex", "flexWrap": "wrap", "gap": "8px",
        }),
        html.Div(
            "Dashed gray = priority foundation not yet in active pipeline.",
            style={"fontSize": "0.63rem", "color": TEXT_LIGHT,
                   "marginTop": "8px", "fontStyle": "italic"},
        ),
    ], style={
        "background": "linear-gradient(135deg, rgba(35,45,75,0.03) 0%, rgba(229,114,0,0.03) 100%)",
        "border": f"1px solid {BORDER}",
        "borderRadius": "10px",
        "padding": "16px 20px",
        "marginBottom": "20px",
    })


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


# ── Foundation profile panel ───────────────────────────────────────────────────
def _grant_history_section(partner_row):
    """
    Renders a collapsible grant history table for a foundation partner.
    Shows UVA-received grants sorted by year desc, then national context grants.
    """
    pid = partner_row.get("id")
    if not pid:
        return html.Span()

    try:
        grants_df = load_foundation_grants(int(pid))
    except Exception:
        return html.Span()

    nat_grants = grants_df[grants_df["grant_type"] == "National Context"]

    if nat_grants.empty:
        return html.Span()

    def _fmt_k(val):
        if val is None:
            return "—"
        v = float(val)
        if v >= 1000:
            return f"${v/1000:.1f}M"
        return f"${v:,.0f}K"

    def _grant_rows(df, row_bg):
        rows = []
        for _, g in df.iterrows():
            yr   = str(int(g["fiscal_year"])) if g["fiscal_year"] else "—"
            amt  = _fmt_k(g["amount_k"])
            title = g["grant_title"] or "—"
            area  = g["program_area"] or "—"
            school = g["recipient_school"] or "—"
            rows.append(html.Tr([
                html.Td(yr,    style={"padding": "5px 8px", "whiteSpace": "nowrap",
                                       "fontWeight": "700", "color": UVA_NAVY,
                                       "fontSize": "0.72rem"}),
                html.Td(amt,   style={"padding": "5px 8px", "whiteSpace": "nowrap",
                                       "fontWeight": "700", "color": UVA_ORANGE,
                                       "fontSize": "0.72rem", "textAlign": "right"}),
                html.Td(title, style={"padding": "5px 8px", "fontSize": "0.72rem",
                                       "color": TEXT_DARK}),
                html.Td(area,  style={"padding": "5px 8px", "fontSize": "0.7rem",
                                       "color": TEXT_MID}),
                html.Td(school if school != "None" else "—",
                               style={"padding": "5px 8px", "fontSize": "0.7rem",
                                       "color": TEXT_MID, "fontStyle": "italic"}),
            ], style={"background": row_bg, "borderBottom": f"1px solid {BORDER}"}))
        return rows

    col_header = lambda label: html.Th(label, style={
        "padding": "5px 8px", "background": UVA_NAVY, "color": "#FFFFFF",
        "fontSize": "0.68rem", "fontWeight": "700", "textTransform": "uppercase",
        "letterSpacing": "0.05em", "whiteSpace": "nowrap",
    })

    def _table_block(df, section_label, accent_color):
        if df.empty:
            return html.Span()
        rows = _grant_rows(df, CARD_BG)
        total_k = df["amount_k"].sum()
        return html.Div([
            html.Div([
                html.Span(section_label, style={
                    "fontSize": "0.68rem", "fontWeight": "700",
                    "color": accent_color, "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                }),
                html.Span(f"  {len(df)} grant{'s' if len(df) != 1 else ''}  •  {_fmt_k(total_k)} total",
                          style={"fontSize": "0.67rem", "color": TEXT_MID, "marginLeft": "8px"}),
            ], style={"marginBottom": "6px"}),
            html.Div(
                html.Table([
                    html.Thead(html.Tr([
                        col_header("Year"),
                        col_header("Amount"),
                        col_header("Grant Title"),
                        col_header("Program Area"),
                        col_header("School / Unit"),
                    ])),
                    html.Tbody(rows),
                ], style={"width": "100%", "borderCollapse": "collapse",
                          "fontSize": "0.72rem"}),
                style={"overflowX": "auto", "borderRadius": "6px",
                       "border": f"1px solid {BORDER}"},
            ),
        ], style={"marginBottom": "12px"})

    nat_block = _table_block(nat_grants, "National Giving Context", TEXT_MID)

    return html.Div([
        html.Div([
            html.Span("📋", style={"fontSize": "0.85rem", "marginRight": "6px"}),
            html.Span("GRANT HISTORY", style={
                "fontFamily": "var(--font-brand)", "fontWeight": "800",
                "fontSize": "0.72rem", "color": UVA_NAVY, "letterSpacing": "0.08em",
            }),
        ], style={"marginBottom": "10px", "marginTop": "14px",
                  "borderTop": f"1px solid {BORDER}", "paddingTop": "12px"}),
        nat_block,
    ])


def _foundation_profile_panel(partner_row):
    """
    Structured 990/financial profile for foundation partners.
    Parses key data from revenue_b, philanthropy_5yr, employees_k, and notes.
    """
    name    = partner_row.get("name", "")
    notes   = partner_row.get("notes", "") or ""
    rev_b   = partner_row.get("revenue_b", 0) or 0      # total assets / endowment proxy $B
    p5yr    = partner_row.get("philanthropy_5yr", 0) or 0  # giving received by UVA (5yr) $
    emp_k   = partner_row.get("employees_k", 0) or 0    # staff FTE (thousands)
    city    = partner_row.get("hq_city", "") or ""
    state   = partner_row.get("hq_state", "") or ""
    sector  = partner_row.get("sector", "") or ""

    # Parse EIN from notes field (pattern: "EIN: XX-XXXXXXX")
    import re
    ein_match = re.search(r"EIN[:\s]+(\d{2}-\d{7})", notes)
    ein = ein_match.group(1) if ein_match else None

    # Parse annual giving from notes (pattern: "~$XXM annual giving" or "$XB+ annual giving")
    annual_match = re.search(r"\$(\d+\.?\d*)[MBK]\+?\s*annual giving", notes, re.IGNORECASE)
    annual_giving_str = None
    if annual_match:
        unit_char = notes[annual_match.start() + len(annual_match.group(0)) - len("annual giving") - 2]
        # Just grab the full match text
        annual_giving_str = re.search(r"(\~?\$[\d\.]+[MBK]\+?)\s*annual giving", notes, re.IGNORECASE)
        if annual_giving_str:
            annual_giving_str = annual_giving_str.group(1)

    # UVA giving received — format nicely
    if p5yr >= 1_000_000:
        p5yr_fmt = f"${p5yr/1_000_000:.1f}M"
    elif p5yr >= 1_000:
        p5yr_fmt = f"${p5yr/1_000:.0f}K"
    else:
        p5yr_fmt = f"${p5yr:,.0f}" if p5yr > 0 else "—"

    # Endowment / assets
    if rev_b >= 1:
        assets_fmt = f"${rev_b:.1f}B"
    elif rev_b > 0:
        assets_fmt = f"${rev_b*1000:.0f}M"
    else:
        assets_fmt = "—"

    # Staff
    if emp_k >= 1:
        staff_fmt = f"{emp_k:.1f}K staff"
    elif emp_k > 0:
        staff_fmt = f"{int(emp_k*1000)} staff"
    else:
        staff_fmt = "—"

    # Build KPI pills
    pills = []
    pill_data = [
        ("Endowment / Assets", assets_fmt, UVA_NAVY),
        ("Annual Giving", annual_giving_str or "See notes", UVA_ORANGE),
        ("UVA Gifts Recv'd (5yr)", p5yr_fmt, "#2E7D32"),
        ("Staff", staff_fmt, "#6A1B9A"),
    ]
    for label, val, color in pill_data:
        pills.append(html.Div([
            html.Div(val, style={
                "fontFamily": "var(--font-brand)", "fontWeight": "800",
                "fontSize": "1.1rem", "color": color, "lineHeight": "1.1",
            }),
            html.Div(label, style={
                "fontSize": "0.67rem", "color": TEXT_MID,
                "fontWeight": "600", "marginTop": "2px",
                "textTransform": "uppercase", "letterSpacing": "0.04em",
            }),
        ], style={
            "background": CARD_BG,
            "border": f"1px solid {BORDER}",
            "borderTop": f"3px solid {color}",
            "borderRadius": "6px",
            "padding": "10px 14px",
            "flex": "1",
            "minWidth": "110px",
        }))

    # EIN + location row
    meta_items = []
    if ein:
        meta_items.append(html.Span([
            html.Span("EIN ", style={"fontWeight": "700", "color": TEXT_MID}),
            html.Span(ein, style={"fontFamily": "monospace", "color": UVA_NAVY}),
        ], style={"marginRight": "16px"}))
    if city or state:
        meta_items.append(html.Span([
            html.Span("HQ ", style={"fontWeight": "700", "color": TEXT_MID}),
            html.Span(f"{city}, {state}".strip(", "), style={"color": UVA_NAVY}),
        ], style={"marginRight": "16px"}))
    if sector:
        sector_color = SECTOR_COLORS.get(sector, TEXT_MID)
        meta_items.append(html.Span([
            html.Span("Focus ", style={"fontWeight": "700", "color": TEXT_MID}),
            html.Span(sector, style={"color": sector_color, "fontWeight": "700"}),
        ]))

    # Priority flag
    is_priority = name in PRIORITY_FOUNDATIONS
    priority_badge = html.Span([
        html.Span("★", style={"color": UVA_ORANGE, "marginRight": "4px"}),
        html.Span("CFR Priority Foundation", style={
            "fontSize": "0.65rem", "fontWeight": "700",
            "color": UVA_ORANGE, "letterSpacing": "0.05em",
        }),
    ], style={
        "background": "rgba(229,114,0,0.08)",
        "border": f"1px solid rgba(229,114,0,0.3)",
        "borderRadius": "10px", "padding": "2px 10px",
        "display": "inline-flex", "alignItems": "center",
    }) if is_priority else html.Span()

    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.Span("🏛️", style={"fontSize": "0.9rem", "marginRight": "6px"}),
                html.Span("FOUNDATION PROFILE", style={
                    "fontFamily": "var(--font-brand)", "fontWeight": "800",
                    "fontSize": "0.72rem", "color": UVA_NAVY, "letterSpacing": "0.08em",
                }),
            ], style={"display": "flex", "alignItems": "center"}),
            priority_badge,
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "marginBottom": "12px"}),

        # KPI pills
        html.Div(pills, style={
            "display": "flex", "flexWrap": "wrap", "gap": "8px",
            "marginBottom": "12px",
        }),

        # Meta row
        html.Div(meta_items, style={
            "fontSize": "0.75rem", "marginBottom": "10px",
            "display": "flex", "flexWrap": "wrap", "gap": "4px",
        }) if meta_items else html.Span(),

        # Notes excerpt (stripped of EIN — already shown above)
        html.Div([
            html.Span("990 / Profile Notes: ", style={
                "fontWeight": "700", "fontSize": "0.72rem",
                "color": TEXT_MID, "marginRight": "4px",
            }),
            html.Span(notes, style={
                "fontSize": "0.72rem", "color": TEXT_DARK, "lineHeight": "1.5",
            }),
        ], style={
            "background": LIGHT_BG, "borderRadius": "6px",
            "padding": "10px 12px", "lineHeight": "1.5",
        }) if notes else html.Span(),

        # ── Grant History ──────────────────────────────────────────────────
        _grant_history_section(partner_row),

    ], style={
        "background": "linear-gradient(135deg, rgba(35,45,75,0.03) 0%, rgba(229,114,0,0.02) 100%)",
        "border": f"1px solid {BORDER}",
        "borderLeft": f"4px solid {UVA_NAVY}",
        "borderRadius": "8px",
        "padding": "16px 18px",
        "marginBottom": "16px",
    })


# ── Partner detail ─────────────────────────────────────────────────────────────
def partner_detail_card(partner_row, scored_row):
    score = scored_row["composite_score"]
    rel   = scored_row["relationship_score"]
    strat = scored_row["strategic_score"]
    tier, tier_color, action = get_tier(score)
    rank  = int(scored_row["rank"])
    is_foundation = partner_row.get("partner_type") == "Foundation"

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
            # Est. Annual Value pill — corporate partners only (procurement metric)
            dbc.Col(html.Div([
                html.Div(f"${partner_row.get('est_annual_value_k',0)/1000:.1f}M" if partner_row.get('est_annual_value_k',0) >= 1000 else f"${partner_row.get('est_annual_value_k',0):.0f}K",
                         className="score-pill-value", style={"color": "#2E7D32"}),
                html.Div("Est. Annual Value", className="score-pill-label"),
            ], className="score-pill"), md=4) if not is_foundation else html.Span(),
        ], className="mb-3"),

        # Foundation Profile panel (foundation partners only)
        _foundation_profile_panel(partner_row) if is_foundation else html.Span(),

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

        # Notes (corporate only — foundations show notes in profile panel above)
        html.Div([
            html.Strong("CFR Notes: "),
            html.Span(partner_row.get("notes", "No notes on file.")),
        ], className="detail-notes mt-3") if (partner_row.get("notes") and not is_foundation) else html.Span(),

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

    # ── Priority Foundation Watch (Foundation tab only) ────────────────────────
    html.Div(id="scoring-priority-watch"),

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
    Output("scoring-priority-watch", "children"),
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
    watch  = scoring_priority_watch(scored) if tab == "Foundation" else html.Span()
    partner_opts = [{"label": f"#{int(r['rank'])} {r['name']}", "value": r['name']}
                    for _, r in scored.sort_values("rank").iterrows()]
    return (
        watch,
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
