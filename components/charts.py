"""
UVA CFR Partner Engagement Dashboard — Shared Chart Helpers
"""

import plotly.graph_objects as go
import plotly.express as px

# ── Brand Constants — Official UVA Brand Palette (brand.virginia.edu) ─────────
# Primary
UVA_NAVY   = "#232D4B"   # Official UVA Blue
UVA_ORANGE = "#E57200"   # Official UVA Orange

# Official secondary palette
UVA_CYAN    = "#009FDF"
UVA_YELLOW  = "#FDDA24"
UVA_TEAL    = "#25CAD3"
UVA_GREEN   = "#62BB46"
UVA_MAGENTA = "#EF3F6B"
UVA_LINK    = "#495E9D"  # Official link blue / web-only

# Neutral / web-only — official values from brand.virginia.edu
LIGHT_BG   = "#F1F1EF"   # Official light gray
CARD_BG    = "#FFFFFF"
BORDER     = "#DADADA"   # Official medium gray
TEXT_DARK  = "#232D4B"   # Using navy for headings
TEXT_MID   = "#666666"   # Official text gray
TEXT_LIGHT = "#8492A6"
GRID_COLOR = "#EBEBEA"   # Slightly off-white for grid lines

# Legacy alias used in some pages
UVA_BLUE   = UVA_LINK

CHART_FONT = "Libre Franklin, Franklin Gothic Medium, Segoe UI, Arial, sans-serif"

TIER_COLORS = {
    "Strategic":  "#E57200",
    "Active":     "#1565C0",
    "Developing": "#F9A825",
    "Prospect":   "#7B1FA2",
    "Inactive":   "#78909C",
}

SECTOR_COLORS = {
    "Tech":       "#1976D2",
    "Consulting": "#E57200",
    "Defense":    "#C62828",
    "Healthcare": "#2E7D32",
    "Pharma":     "#6A1B9A",
    "Finance":    "#00838F",
    "Energy":     "#558B2F",
}


def chart_layout(title="", height=380, show_legend=True):
    """Base layout dict for all Plotly charts — UVA Brand 2024."""
    return dict(
        template="plotly_white",
        title=dict(
            text=f'<span style="font-size:13px;font-weight:700;color:{UVA_NAVY};'
                 f'font-family:{CHART_FONT};letter-spacing:0.01em">{title}</span>',
            x=0.01, xref="paper",
        ),
        paper_bgcolor=CARD_BG,
        plot_bgcolor="#FAFAFA",
        height=height,
        margin=dict(l=50, r=20, t=50, b=40),
        font=dict(color=TEXT_MID, size=11, family=CHART_FONT),
        xaxis=dict(gridcolor=GRID_COLOR, linecolor=BORDER,
                   tickfont=dict(size=10, color=TEXT_MID),
                   zerolinecolor=BORDER),
        yaxis=dict(gridcolor=GRID_COLOR, linecolor=BORDER,
                   tickfont=dict(size=10, color=TEXT_MID),
                   zerolinecolor=BORDER),
        legend=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(size=10, family=CHART_FONT),
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right",  x=1,
        ) if show_legend else dict(visible=False),
    )


def make_gauge(value, title, max_val=100, color=UVA_ORANGE, height=220):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(font=dict(size=32, color=TEXT_DARK, family=CHART_FONT), suffix=""),
        title=dict(text=f'<span style="font-size:11px;color:{TEXT_MID}">{title}</span>',
                   font=dict(size=11)),
        gauge=dict(
            axis=dict(range=[0, max_val], tickwidth=1, tickcolor=BORDER,
                      tickfont=dict(size=9)),
            bar=dict(color=color, thickness=0.7),
            bgcolor=LIGHT_BG,
            bordercolor=BORDER,
            borderwidth=1,
            steps=[
                dict(range=[0, max_val * 0.2],  color="#F5F5F5"),
                dict(range=[max_val * 0.2, max_val * 0.4], color="#EEEEEE"),
                dict(range=[max_val * 0.4, max_val * 0.6], color="#E8E8E8"),
                dict(range=[max_val * 0.6, max_val * 0.8], color="#E0E0E0"),
            ],
            threshold=dict(
                line=dict(color=UVA_ORANGE, width=3),
                thickness=0.8,
                value=value
            ),
        ),
    ))
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        height=height,
        margin=dict(l=20, r=20, t=40, b=10),
        font=dict(family=CHART_FONT),
    )
    return fig


def make_radar(categories, values, max_values, partner_name="", height=380):
    """Radar chart normalizing values to % of max_pts."""
    norm = [v / m * 100 if m > 0 else 0 for v, m in zip(values, max_values)]
    cats_closed = categories + [categories[0]]
    vals_closed  = norm + [norm[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_closed, theta=cats_closed,
        fill="toself",
        fillcolor=f"rgba(35,45,75,0.12)",
        line=dict(color=UVA_NAVY, width=2),
        name=partner_name,
        hovertemplate="%{theta}: %{r:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=LIGHT_BG,
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(size=9, color=TEXT_LIGHT),
                gridcolor=GRID_COLOR,
            ),
            angularaxis=dict(
                tickfont=dict(size=10, color=TEXT_DARK),
                gridcolor=GRID_COLOR,
            ),
        ),
        paper_bgcolor=CARD_BG,
        height=height,
        margin=dict(l=50, r=50, t=40, b=40),
        showlegend=False,
        font=dict(family=CHART_FONT),
    )
    return fig
