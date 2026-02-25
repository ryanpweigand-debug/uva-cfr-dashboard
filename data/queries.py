"""
UVA CFR Partner Engagement Dashboard — Data Queries & Scoring Engine
Implements Ahsan's 100-pt Partner Scoring Methodology.
"""

import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "cfr_partners.db")
engine   = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# ── Ahsan's Scoring Methodology ───────────────────────────────────────────────
# (column, display_label, max_points)
RELATIONSHIP_METRICS = [
    ("sponsored_research_5yr",    "Sponsored Research (5yr)",    18),
    ("sponsored_research_alltime","Sponsored Research (All-Time)", 7),
    ("philanthropy_5yr",          "Philanthropy (5yr)",           14),
    ("philanthropy_alltime",      "Philanthropy (All-Time)",       6),
    ("research_footprint",        "Research Footprint",           10),
    ("legal_activity",            "Legal / On-Ramp Activity",      5),
    ("talent_pipeline",           "Talent Pipeline",               5),
    ("engagement_depth",          "Engagement Depth",              5),
]
STRATEGIC_METRICS = [
    ("strategic_fit",             "Strategic Fit",                10),
    ("growth_greenfield",         "Growth / Greenfield",           7),
    ("access_influence",          "Access & Influence",            8),
    ("feasibility_timing",        "Feasibility & Timing",          5),
]
ALL_METRICS = RELATIONSHIP_METRICS + STRATEGIC_METRICS

PARTNER_TIERS = [
    (80, 100, "Strategic",  "#E57200", "Full engagement; executive-level relationship management"),
    (60,  79, "Active",     "#1565C0", "Active engagement; growth planning; dedicated account team"),
    (40,  59, "Developing", "#F9A825", "Targeted engagement; identify growth opportunities"),
    (20,  39, "Prospect",   "#7B1FA2", "Monitor and assess; opportunistic engagement"),
    ( 0,  19, "Inactive",   "#78909C", "Low priority; periodic reassessment"),
]

SECTOR_COLORS = {
    "Tech":       "#1976D2",
    "Consulting": "#E57200",
    "Defense":    "#C62828",
    "Healthcare": "#2E7D32",
    "Pharma":     "#6A1B9A",
    "Finance":    "#00838F",
    "Energy":     "#558B2F",
}

TIER_COLORS = {
    "Strategic":  "#E57200",
    "Active":     "#1565C0",
    "Developing": "#F9A825",
    "Prospect":   "#7B1FA2",
    "Inactive":   "#78909C",
}


def get_tier(score: float):
    for lo, hi, label, color, action in PARTNER_TIERS:
        if lo <= score <= hi:
            return label, color, action
    return "Inactive", "#78909C", "Low priority; periodic reassessment"


def compute_percentile_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ahsan's Method 2 — Percentile-Ranked (preferred / data-driven).
    percentile = (# ranked below) / (N - 1) * 100
    points     = (percentile / 100) * max_points
    """
    scored = df.copy()
    n = len(df)
    for col, _, max_pts in ALL_METRICS:
        ranks = df[col].rank(method="average", ascending=True)
        percentile = (ranks - 1) / (n - 1) * 100 if n > 1 else pd.Series([100.0] * n, index=df.index)
        scored[f"pct_{col}"] = (percentile / 100) * max_pts

    scored["relationship_score"] = sum(scored[f"pct_{col}"] for col, _, _ in RELATIONSHIP_METRICS)
    scored["strategic_score"]    = sum(scored[f"pct_{col}"] for col, _, _ in STRATEGIC_METRICS)
    scored["composite_score"]    = scored["relationship_score"] + scored["strategic_score"]
    scored["rank"] = scored["composite_score"].rank(ascending=False, method="min").astype(int)
    scored["tier"] = scored["composite_score"].apply(lambda s: get_tier(s)[0])
    scored["tier_color"] = scored["composite_score"].apply(lambda s: get_tier(s)[1])
    return scored


def compute_judgment_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ahsan's Method 1 — Human Judgment (0-10 scale).
    points = (rating / 10) * max_points
    """
    QUALITATIVE = {"engagement_depth", "strategic_fit", "growth_greenfield",
                   "access_influence", "feasibility_timing"}
    scored = df.copy()
    for col, _, max_pts in ALL_METRICS:
        if col in QUALITATIVE:
            rating = scored[col]
        else:
            col_max = scored[col].max()
            rating = (scored[col] / col_max * 10) if col_max > 0 else 0
        scored[f"jdg_{col}"] = (rating / 10) * max_pts

    scored["relationship_score"] = sum(scored[f"jdg_{col}"] for col, _, _ in RELATIONSHIP_METRICS)
    scored["strategic_score"]    = sum(scored[f"jdg_{col}"] for col, _, _ in STRATEGIC_METRICS)
    scored["composite_score"]    = scored["relationship_score"] + scored["strategic_score"]
    scored["rank"] = scored["composite_score"].rank(ascending=False, method="min").astype(int)
    scored["tier"] = scored["composite_score"].apply(lambda s: get_tier(s)[0])
    scored["tier_color"] = scored["composite_score"].apply(lambda s: get_tier(s)[1])
    return scored


# ── Data Loaders ──────────────────────────────────────────────────────────────

def load_partners() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM partners ORDER BY name", engine)


def load_scored_partners(method: str = "percentile") -> pd.DataFrame:
    df = load_partners()
    if method == "judgment":
        return compute_judgment_scores(df)
    return compute_percentile_scores(df)


def load_benchmarks() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM benchmark_peers ORDER BY annual_research_m DESC", engine)


def load_strategic_priorities() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM strategic_priorities ORDER BY code", engine)


def load_recommendations(partner_id: int = None) -> pd.DataFrame:
    if partner_id:
        q = f"SELECT * FROM recommendations WHERE partner_id = {partner_id} OR partner_id IS NULL ORDER BY priority, title"
    else:
        q = "SELECT * FROM recommendations ORDER BY priority, category, title"
    return pd.read_sql(q, engine)


# ── Portfolio KPIs ─────────────────────────────────────────────────────────────

def portfolio_kpis(method: str = "percentile") -> dict:
    scored = load_scored_partners(method)
    df_raw = load_partners()
    tiers = scored["tier"].value_counts().to_dict()
    return {
        "total_partners": len(scored),
        "strategic_count": tiers.get("Strategic", 0),
        "active_count": tiers.get("Active", 0),
        "developing_count": tiers.get("Developing", 0),
        "avg_score": round(scored["composite_score"].mean(), 1),
        "total_sr_5yr": df_raw["sponsored_research_5yr"].sum(),
        "total_phil_5yr": df_raw["philanthropy_5yr"].sum(),
        "total_talent": df_raw["talent_pipeline"].sum(),
        "total_est_value_k": df_raw["est_annual_value_k"].sum(),
    }


# ── CFR Strategic Plan KPIs ────────────────────────────────────────────────────

SP_COLS = ["sp01_org_structure","sp02_front_door","sp03_metrics",
           "sp04_team_capacity","sp05_data_crm","sp06_awareness"]
SP_LABELS = ["SP-01 Org Structure","SP-02 Front Door","SP-03 Metrics",
             "SP-04 Team","SP-05 Data/CRM","SP-06 Awareness"]


def sp_partner_alignment() -> pd.DataFrame:
    """Mean SP score per priority across all partners."""
    df = load_partners()
    means = df[SP_COLS].mean().values
    return pd.DataFrame({"priority": SP_LABELS, "mean_score": means, "max_score": [10]*6})


# ── Economic Impact (PPE.pdf data) ────────────────────────────────────────────
PPE_STATS = {
    "total_impact_b":   11.9,
    "direct_b":          6.6,
    "indirect_b":        2.6,
    "induced_b":         2.7,
    "total_jobs":       67109,
    "research_impact_b": 1.0,
    "research_jobs":    10700,
    "startups":           55,
    "patents":          2184,
    "uva_health_b":      8.5,
    "health_jobs":      40334,
    "patient_encounters_m": 3.0,
    "state_roi":          35,
    "govt_revenue_m":     455,
    "grad_salary_premium_pct": 53,
    "student_visitor_m":  739,
    "va_jobs_ratio": "1 in 85",
}
