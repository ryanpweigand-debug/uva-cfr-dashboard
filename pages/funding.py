"""
Funding Opportunities — CFR Staff Management Hub
=================================================
Phase 1: Consolidated view of all funding opportunities from 3 listservs.
CFR staff can:
  - Browse, filter, and search all opportunities in one place
  - Add new opportunities via inline form
  - See deduplication warnings (same sponsor + similar deadline)
  - Track which source each opportunity came from
  - Archive / expire records
"""

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import datetime
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "components"))

from queries import (
    load_funding_opportunities, add_funding_opportunity,
    delete_funding_opportunity, update_funding_status, funding_summary_kpis,
)
from charts import (
    UVA_NAVY, UVA_ORANGE, LIGHT_BG, CARD_BG, TEXT_DARK, TEXT_MID,
    TEXT_LIGHT, GRID_COLOR, BORDER, CHART_FONT, chart_layout,
)

dash.register_page(__name__, path="/funding", name="Funding Opportunities", order=7)

# ── Constants ─────────────────────────────────────────────────────────────────
STATUS_OPTIONS  = ["All", "Active", "Closing Soon", "Expired", "Archived"]
TYPE_OPTIONS    = ["All", "Grant", "Contract", "Fellowship", "RFP", "LSO"]
SOURCE_OPTIONS  = [
    "All",
    "VPR Federal Digest (Lucy Carr Jones)",
    "Limited Submissions (Matt Dooley)",
    "CFR + School Research Directors",
    "Other",
]
LSO_STATUS_OPTIONS = ["Open", "In Review", "Awarded", "Closed"]
AREA_OPTIONS = [
    "All", "AI", "Aging", "Autonomy", "Chemistry", "Cybersecurity",
    "Cloud Computing", "Commercialization", "Data Science", "Defense",
    "Education", "Energy", "Engineering", "Environment", "Finance",
    "Food Systems", "Global Health", "Health", "Health Equity",
    "Machine Learning", "Materials Science", "Mental Health", "Neuroscience",
    "Oncology", "Physics", "Policy", "Quantum Computing", "Social Sciences",
    "STEM", "Technology Transfer", "Workforce",
]

STATUS_COLORS = {
    "Active":       "#2E7D32",
    "Closing Soon": "#E57200",
    "Expired":      "#78909C",
    "Archived":     "#9E9E9E",
}


# ── Helper: status badge ──────────────────────────────────────────────────────
def status_badge(status):
    color = STATUS_COLORS.get(status, "#999")
    return html.Span(status, style={
        "background": color, "color": "#fff",
        "fontSize": "0.68rem", "fontWeight": "700",
        "padding": "2px 9px", "borderRadius": "10px",
        "textTransform": "uppercase", "letterSpacing": "0.4px",
    })


# ── Helper: days-until-deadline ────────────────────────────────────────────────
def days_until(deadline_str):
    try:
        d = datetime.date.fromisoformat(deadline_str)
        delta = (d - datetime.date.today()).days
        if delta < 0:
            return "Past", "#78909C"
        if delta <= 14:
            return f"{delta}d ⚠️", "#E57200"
        if delta <= 30:
            return f"{delta}d", "#F57C00"
        return f"{delta}d", "#2E7D32"
    except Exception:
        return deadline_str or "—", TEXT_MID


# ── KPI strip ────────────────────────────────────────────────────────────────
def kpi_strip(df):
    kpis = funding_summary_kpis(df)
    lso_count = int(df["is_lso"].sum()) if "is_lso" in df.columns else 0
    cards = [
        (str(kpis["total"]),             "Total Opportunities",  "across all 3 sources",  UVA_NAVY),
        (str(kpis["active"]),            "Active",               "open for applications", "#2E7D32"),
        (str(kpis["closing_soon"]),      "Closing Soon",         "within 30 days",        UVA_ORANGE),
        (str(lso_count),                 "Limited Submissions",  "require internal comp.", "#C62828"),
        (f"${kpis['total_max_m']:.0f}M", "Max Potential Funding","if all awarded",        "#7B1FA2"),
    ]
    return dbc.Row([
        dbc.Col(html.Div([
            html.Div(v, className="stat-value", style={"color": c}),
            html.Div(l, className="stat-label"),
            html.Div(s, className="stat-sub"),
        ], className="stat-card"), md=2, sm=4, xs=6)
        for v, l, s, c in cards
    ], className="mb-4")


# ── Source breakdown bar ──────────────────────────────────────────────────────
def source_bar(df):
    counts = df.groupby("source").size().reset_index(name="count")
    colors = [UVA_NAVY, UVA_ORANGE, "#1565C0", "#2E7D32"]

    fig = go.Figure(go.Bar(
        x=counts["source"].apply(lambda s: s.split("—")[-1].strip() if "—" in s else s),
        y=counts["count"],
        marker_color=colors[:len(counts)],
        text=counts["count"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y} opportunities<extra></extra>",
    ))
    lo = chart_layout("Opportunities by Source List", height=260)
    lo["xaxis"]["title"] = ""
    lo["yaxis"]["title"] = "Count"
    lo["margin"] = dict(l=40, r=20, t=50, b=60)
    fig.update_layout(**lo)
    return fig


# ── Deadline timeline scatter ─────────────────────────────────────────────────
def deadline_timeline(df):
    df = df[df["deadline"].notna() & (df["status"].isin(["Active", "Closing Soon"]))].copy()
    df["deadline_dt"] = pd.to_datetime(df["deadline"], errors="coerce")
    df = df.dropna(subset=["deadline_dt"]).sort_values("deadline_dt")
    colors = [STATUS_COLORS.get(s, "#999") for s in df["status"]]

    fig = go.Figure(go.Scatter(
        x=df["deadline_dt"],
        y=df["sponsor"],
        mode="markers+text",
        text=df["amount_max_k"].apply(lambda x: f"${x/1000:.1f}M" if x >= 1000 else f"${x:.0f}k"),
        textposition="top center",
        textfont=dict(size=8, color=TEXT_MID),
        marker=dict(color=colors, size=14,
                    line=dict(color="white", width=1.5)),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Sponsor: %{y}<br>"
            "Deadline: %{x|%b %d, %Y}<br>"
            "Max: $%{customdata[1]}k<br>"
            "Areas: %{customdata[2]}<extra></extra>"
        ),
        customdata=list(zip(df["title"], df["amount_max_k"],
                            df["research_areas"].fillna("—"))),
    ))
    today = datetime.date.today().isoformat()
    fig.add_vline(x=today, line_dash="dot", line_color=UVA_ORANGE,
                  annotation_text="Today", annotation_position="top",
                  annotation_font=dict(size=9, color=UVA_ORANGE))

    lo = chart_layout("Deadline Timeline — Active Opportunities", height=320)
    lo["xaxis"]["title"] = "Deadline"
    lo["yaxis"]["title"] = ""
    lo["margin"]["l"] = 160
    fig.update_layout(**lo)
    return fig


# ── LSO badge ────────────────────────────────────────────────────────────────
def lso_badge():
    return html.Span("LIMITED SUBMISSION", className="lso-badge")


# ── LSO internal competition block ────────────────────────────────────────────
def lso_block(row):
    slots     = row.get("lso_slots") or "?"
    int_ddl   = row.get("lso_internal_deadline") or "TBD"
    int_status= row.get("lso_internal_status") or "Open"
    nominees  = row.get("lso_nominees") or ""
    status_color = {
        "Open":      "#2E7D32",
        "In Review": "#E57200",
        "Awarded":   "#1565C0",
        "Closed":    "#78909C",
    }.get(int_status, "#999")

    return html.Div([
        html.Div("INTERNAL COMPETITION TRACKING", className="section-eyebrow mb-1"),
        html.Div([
            html.Span([html.Strong("UVA Slots: "), f"{slots}"],
                      style={"marginRight": "20px", "fontSize": "0.82rem"}),
            html.Span([html.Strong("Internal Deadline: "), int_ddl],
                      style={"marginRight": "20px", "fontSize": "0.82rem"}),
            html.Span([html.Strong("Status: ")],
                      style={"fontSize": "0.82rem", "marginRight": "4px"}),
            html.Span(int_status, style={
                "color": status_color, "fontWeight": "700", "fontSize": "0.82rem",
                "marginRight": "20px",
            }),
            html.Span([html.Strong("Nominees: "), nominees or "None yet"],
                      style={"fontSize": "0.82rem", "color": TEXT_MID}),
        ]),
    ], className="lso-tracking-block mt-2")


# ── Opportunity card (expanded detail) ───────────────────────────────────────
def opp_card(row):
    days_txt, days_color = days_until(row.get("deadline", ""))
    amt_min = row.get("amount_min_k", 0) or 0
    amt_max = row.get("amount_max_k", 0) or 0
    amt_str = (f"${amt_min:.0f}k – ${amt_max:.0f}k" if amt_min != amt_max
               else f"${amt_max:.0f}k")
    if amt_max >= 1000:
        amt_str = (f"${amt_min/1000:.1f}M – ${amt_max/1000:.1f}M"
                   if amt_min != amt_max else f"${amt_max/1000:.1f}M")

    is_lso = bool(row.get("is_lso", False))

    area_tags = [
        html.Span(a.strip(), className="funding-area-tag")
        for a in str(row.get("research_areas", "")).split(",") if a.strip()
    ]

    url = row.get("url") or ""
    url_link = html.A("View Full RFP →", href=url, target="_blank",
                      className="funding-rfp-link") if url else html.Span()

    # Source display: show the owner name in parentheses
    source_raw = row.get("source", "") or ""
    source_display = source_raw.split("(")[-1].rstrip(")") if "(" in source_raw else source_raw

    return html.Div([
        # Header row
        html.Div([
            html.Div([
                html.Div([
                    row.get("title", ""),
                    lso_badge() if is_lso else html.Span(),
                ], className="funding-card-title d-flex align-items-center gap-2"),
                html.Div(row.get("sponsor", ""), className="funding-card-sponsor"),
            ], className="flex-grow-1"),
            html.Div([
                status_badge(row.get("status", "Active")),
                html.Div(row.get("opp_type", ""), className="funding-type-label ms-2"),
            ], className="d-flex align-items-center gap-1"),
        ], className="d-flex align-items-start justify-content-between mb-2"),

        # Meta row
        html.Div([
            html.Span([html.Strong("Deadline: "), row.get("deadline", "—")],
                      style={"marginRight": "18px", "fontSize": "0.82rem"}),
            html.Span([html.Strong("Due in: ")],
                      style={"marginRight": "4px", "fontSize": "0.82rem"}),
            html.Span(days_txt, style={"color": days_color, "fontWeight": "700",
                                       "fontSize": "0.82rem", "marginRight": "18px"}),
            html.Span([html.Strong("Award: "), amt_str],
                      style={"marginRight": "18px", "fontSize": "0.82rem"}),
            html.Span([html.Strong("Via: "), source_display],
                      style={"fontSize": "0.82rem", "color": TEXT_MID}),
        ], className="mb-2"),

        # Research area tags
        html.Div(area_tags, className="funding-area-row mb-2") if area_tags else html.Span(),

        # LSO internal competition block (only for LSOs)
        lso_block(row) if is_lso else html.Span(),

        # Description
        html.Div(str(row.get("description", ""))[:400] + ("…" if len(str(row.get("description",""))) > 400 else ""),
                 className="funding-card-desc mt-2"),

        # CFR Notes
        html.Div([html.Strong("CFR Notes: "),
                  html.Span(row.get("notes", ""), style={"color": TEXT_MID})],
                 className="funding-card-notes mt-1") if row.get("notes") else html.Span(),

        # Footer
        html.Div([url_link], className="mt-2"),

    ], className="funding-opp-card")


# ── Add New Opportunity Form ──────────────────────────────────────────────────
add_form = dbc.Collapse(
    html.Div([
        html.Div("ADD NEW OPPORTUNITY", className="section-eyebrow mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Title *", className="dropdown-label"),
                dbc.Input(id="fn-title", placeholder="Full opportunity title…", className="cfr-input"),
            ], md=6),
            dbc.Col([
                dbc.Label("Sponsor *", className="dropdown-label"),
                dbc.Input(id="fn-sponsor", placeholder="e.g. NSF, NIH, Google…", className="cfr-input"),
            ], md=3),
            dbc.Col([
                dbc.Label("Opportunity Type", className="dropdown-label"),
                dcc.Dropdown(id="fn-type",
                             options=[{"label": t, "value": t} for t in TYPE_OPTIONS[1:]],
                             value="Grant", clearable=False, className="cfr-dropdown"),
            ], md=3),
        ], className="mb-2"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Deadline (YYYY-MM-DD)", className="dropdown-label"),
                dbc.Input(id="fn-deadline", placeholder="2025-10-15", className="cfr-input"),
            ], md=2),
            dbc.Col([
                dbc.Label("Min Award ($k)", className="dropdown-label"),
                dbc.Input(id="fn-amt-min", type="number", placeholder="100", className="cfr-input"),
            ], md=2),
            dbc.Col([
                dbc.Label("Max Award ($k)", className="dropdown-label"),
                dbc.Input(id="fn-amt-max", type="number", placeholder="500", className="cfr-input"),
            ], md=2),
            dbc.Col([
                dbc.Label("Source / Owner", className="dropdown-label"),
                dcc.Dropdown(id="fn-source",
                             options=[{"label": s, "value": s} for s in SOURCE_OPTIONS[1:]],
                             value="VPR Federal Digest (Lucy Carr Jones)", clearable=False, className="cfr-dropdown"),
            ], md=3),
            dbc.Col([
                dbc.Label("Status", className="dropdown-label"),
                dcc.Dropdown(id="fn-status",
                             options=[{"label": s, "value": s} for s in STATUS_OPTIONS[1:]],
                             value="Active", clearable=False, className="cfr-dropdown"),
            ], md=3),
        ], className="mb-2"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Research Areas (comma-separated)", className="dropdown-label"),
                dbc.Input(id="fn-areas", placeholder="Health, AI, Energy…", className="cfr-input"),
            ], md=5),
            dbc.Col([
                dbc.Label("Eligibility", className="dropdown-label"),
                dbc.Input(id="fn-eligibility", placeholder="Faculty, Postdoc, All…",
                          value="Faculty", className="cfr-input"),
            ], md=2),
            dbc.Col([
                dbc.Label("RFP URL", className="dropdown-label"),
                dbc.Input(id="fn-url", placeholder="https://…", className="cfr-input"),
            ], md=5),
        ], className="mb-2"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Description", className="dropdown-label"),
                dbc.Textarea(id="fn-desc", placeholder="Brief description of the opportunity…",
                             rows=3, className="cfr-input"),
            ], md=8),
            dbc.Col([
                dbc.Label("CFR Staff Notes", className="dropdown-label"),
                dbc.Textarea(id="fn-notes", placeholder="Internal notes, partner connections, flags…",
                             rows=3, className="cfr-input"),
            ], md=4),
        ], className="mb-3"),
        # LSO fields (shown always — staff fills in only if LSO)
        html.Hr(style={"borderColor": "#DEE2E6", "margin": "8px 0 12px"}),
        html.Div("LIMITED SUBMISSION FIELDS (fill in only if this is an LSO)",
                 className="section-eyebrow mb-2"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Is Limited Submission?", className="dropdown-label"),
                dcc.Dropdown(id="fn-is-lso",
                             options=[{"label": "No", "value": "no"},
                                      {"label": "Yes — LSO", "value": "yes"}],
                             value="no", clearable=False, className="cfr-dropdown"),
            ], md=2),
            dbc.Col([
                dbc.Label("UVA Submission Slots", className="dropdown-label"),
                dbc.Input(id="fn-lso-slots", type="number", placeholder="e.g. 2",
                          className="cfr-input"),
            ], md=2),
            dbc.Col([
                dbc.Label("Internal Deadline (YYYY-MM-DD)", className="dropdown-label"),
                dbc.Input(id="fn-lso-int-deadline", placeholder="2025-08-01",
                          className="cfr-input"),
            ], md=2),
            dbc.Col([
                dbc.Label("Internal Status", className="dropdown-label"),
                dcc.Dropdown(id="fn-lso-int-status",
                             options=[{"label": s, "value": s} for s in LSO_STATUS_OPTIONS],
                             value="Open", clearable=False, className="cfr-dropdown"),
            ], md=2),
            dbc.Col([
                dbc.Label("Current Nominees (comma-separated)", className="dropdown-label"),
                dbc.Input(id="fn-lso-nominees", placeholder="PI Name, PI Name…",
                          className="cfr-input"),
            ], md=4),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Added By", className="dropdown-label"),
                dbc.Input(id="fn-added-by", placeholder="Your name", className="cfr-input"),
            ], md=3),
            dbc.Col([
                dbc.Button("Add Opportunity", id="fn-submit-btn", color="primary",
                           className="cfr-btn mt-4"),
            ], md=3),
            dbc.Col([
                html.Div(id="fn-submit-msg", className="mt-4",
                         style={"fontSize": "0.85rem", "fontWeight": "600"}),
            ], md=6),
        ]),
    ], className="chart-card mb-3"),
    id="fn-form-collapse", is_open=False,
)


# ── Page Layout ───────────────────────────────────────────────────────────────
layout = html.Div([

    html.Div([
        html.Div([
            html.H2("Funding Opportunities", className="page-title"),
            html.P(
                "Consolidated view of all funding opportunities from 3 source lists. "
                "One place for CFR staff to manage, tag, and track — no more listserv fragmentation.",
                className="page-subtitle"
            ),
        ], className="flex-grow-1"),
        html.Div([
            dbc.Button("+ Add Opportunity", id="fn-toggle-form-btn",
                       color="primary", className="cfr-btn"),
        ], className="ms-3 d-flex align-items-center"),
    ], className="page-header d-flex align-items-start"),

    # Add form (collapsible)
    add_form,

    # ── KPI strip ─────────────────────────────────────────────────────────────
    html.Div(id="fn-kpi-strip", className="mb-2"),

    # ── Filters ──────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            dbc.Label("Source List", className="dropdown-label"),
            dcc.Dropdown(id="fn-filter-source",
                         options=[{"label": s.split("(")[-1].rstrip(")") if "(" in s else s,
                                   "value": s} for s in SOURCE_OPTIONS],
                         value="All", clearable=False, className="cfr-dropdown"),
        ], md=3),
        dbc.Col([
            dbc.Label("Status", className="dropdown-label"),
            dcc.Dropdown(id="fn-filter-status",
                         options=[{"label": s, "value": s} for s in STATUS_OPTIONS],
                         value="All", clearable=False, className="cfr-dropdown"),
        ], md=2),
        dbc.Col([
            dbc.Label("Type / LSO", className="dropdown-label"),
            dcc.Dropdown(id="fn-filter-type",
                         options=[{"label": t, "value": t} for t in TYPE_OPTIONS],
                         value="All", clearable=False, className="cfr-dropdown"),
        ], md=2),
        dbc.Col([
            dbc.Label("Research Area", className="dropdown-label"),
            dcc.Dropdown(id="fn-filter-area",
                         options=[{"label": a, "value": a} for a in AREA_OPTIONS],
                         value="All", clearable=False, className="cfr-dropdown"),
        ], md=3),
        dbc.Col([
            dbc.Label("Sort By", className="dropdown-label"),
            dcc.Dropdown(id="fn-sort-by",
                         options=[
                             {"label": "Deadline (soonest first)", "value": "deadline"},
                             {"label": "Award (largest first)",    "value": "amount"},
                             {"label": "Sponsor A–Z",              "value": "sponsor"},
                         ],
                         value="deadline", clearable=False, className="cfr-dropdown"),
        ], md=2),
    ], className="filter-row mb-3"),

    # ── Charts row ────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            html.Div([
                dcc.Graph(id="fn-source-bar", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=4),
        dbc.Col([
            html.Div([
                dcc.Graph(id="fn-timeline", config={"displayModeBar": False}),
            ], className="chart-card"),
        ], md=8),
    ], className="mb-3"),

    # ── Opportunity cards ─────────────────────────────────────────────────────
    html.Div("OPPORTUNITIES", className="section-eyebrow mb-2 px-1"),
    html.Div(id="fn-result-count", className="mb-2",
             style={"fontSize": "0.82rem", "color": TEXT_MID}),
    html.Div(id="fn-cards-container"),

], className="cfr-page")


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output("fn-form-collapse", "is_open"),
    Input("fn-toggle-form-btn", "n_clicks"),
    State("fn-form-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_form(n, is_open):
    return not is_open


@callback(
    Output("fn-kpi-strip",       "children"),
    Output("fn-source-bar",      "figure"),
    Output("fn-timeline",        "figure"),
    Output("fn-cards-container", "children"),
    Output("fn-result-count",    "children"),
    Input("fn-filter-source",    "value"),
    Input("fn-filter-status",    "value"),
    Input("fn-filter-type",      "value"),
    Input("fn-filter-area",      "value"),
    Input("fn-sort-by",          "value"),
    Input("fn-submit-btn",       "n_clicks"),   # refresh after add
)
def update_funding(source, status, opp_type, area, sort_by, _add_click):
    df = load_funding_opportunities(status=status, research_area=area,
                                    opp_type=opp_type, source=source)

    # Sort
    if sort_by == "amount":
        df = df.sort_values("amount_max_k", ascending=False)
    elif sort_by == "sponsor":
        df = df.sort_values("sponsor")
    else:
        df = df.sort_values("deadline", na_position="last")

    # Build cards
    if df.empty:
        cards = html.Div("No opportunities match the current filters.",
                         className="placeholder-text")
    else:
        cards = html.Div([opp_card(row) for _, row in df.iterrows()])

    count_txt = f"Showing {len(df)} opportunit{'y' if len(df)==1 else 'ies'}"

    # Charts always use full unfiltered data for context
    df_all = load_funding_opportunities()
    return (
        kpi_strip(df_all),
        source_bar(df_all),
        deadline_timeline(df_all),
        cards,
        count_txt,
    )


@callback(
    Output("fn-submit-msg",    "children"),
    Output("fn-submit-msg",    "style"),
    Input("fn-submit-btn",     "n_clicks"),
    State("fn-title",          "value"),
    State("fn-sponsor",        "value"),
    State("fn-type",           "value"),
    State("fn-deadline",       "value"),
    State("fn-amt-min",        "value"),
    State("fn-amt-max",        "value"),
    State("fn-source",         "value"),
    State("fn-status",         "value"),
    State("fn-areas",          "value"),
    State("fn-eligibility",    "value"),
    State("fn-url",            "value"),
    State("fn-desc",           "value"),
    State("fn-notes",          "value"),
    State("fn-added-by",       "value"),
    State("fn-is-lso",         "value"),
    State("fn-lso-slots",      "value"),
    State("fn-lso-int-deadline","value"),
    State("fn-lso-int-status", "value"),
    State("fn-lso-nominees",   "value"),
    prevent_initial_call=True,
)
def submit_opportunity(n_clicks, title, sponsor, opp_type, deadline,
                       amt_min, amt_max, source, status, areas,
                       eligibility, url, desc, notes, added_by,
                       is_lso, lso_slots, lso_int_dl, lso_int_status, lso_nominees):
    if not title or not sponsor:
        return "⚠️ Title and Sponsor are required.", {"color": UVA_ORANGE, "fontSize": "0.85rem"}

    lso_flag = (is_lso == "yes")
    data = {
        "title": title, "sponsor": sponsor, "opp_type": opp_type,
        "deadline": deadline, "amount_min_k": float(amt_min or 0),
        "amount_max_k": float(amt_max or 0), "source": source,
        "status": status, "research_areas": areas, "eligibility": eligibility,
        "url": url, "description": desc, "notes": notes, "added_by": added_by,
        "is_lso": lso_flag,
        "lso_slots": int(lso_slots) if lso_slots and lso_flag else None,
        "lso_internal_deadline": lso_int_dl if lso_flag else None,
        "lso_internal_status": lso_int_status if lso_flag else None,
        "lso_nominees": lso_nominees if lso_flag else None,
    }
    ok = add_funding_opportunity(data)
    if ok:
        lso_note = " [LSO]" if lso_flag else ""
        return f"✅ '{title}'{lso_note} added successfully.", {"color": "#2E7D32", "fontSize": "0.85rem"}
    return "❌ Error saving. Check logs.", {"color": "#C62828", "fontSize": "0.85rem"}
