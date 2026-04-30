"""
UVA CFR Partner Engagement Dashboard — Database Schema
"""

import os
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Text, Date, Boolean
)
from sqlalchemy.orm import declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "cfr_partners.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
Base   = declarative_base()


class Partner(Base):
    """Corporate / organizational partner record."""
    __tablename__ = "partners"
    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String,  nullable=False, unique=True)
    sector = Column(String, nullable=False)    # Tech, Consulting, Defense, Healthcare, Pharma, Finance, Energy
    hq_city    = Column(String, nullable=True)
    hq_state   = Column(String, nullable=True)
    revenue_b  = Column(Float,  nullable=True)  # annual revenue in $B
    employees_k= Column(Float,  nullable=True)  # employees in thousands
    notes      = Column(Text,   nullable=True)
    partner_type = Column(String, nullable=False, default="Corporate")  # Corporate / Foundation

    # ── Relationship Strength metrics (70 pts) ─────────────────────────────
    sponsored_research_5yr    = Column(Float, nullable=False, default=0)  # $ last 5 FYs
    sponsored_research_alltime= Column(Float, nullable=False, default=0)  # $ all-time (stored, not scored)
    philanthropy_5yr          = Column(Float, nullable=False, default=0)  # $ last 5 FYs
    procurement_score         = Column(Float, nullable=False, default=0)  # 0-10: goods/services $ from org
    faculty_engagement        = Column(Float, nullable=False, default=0)  # 0-10: active awards, projects, advisory, IP, startups
    research_footprint        = Column(Float, nullable=False, default=0)  # legacy: active project count (not scored)
    legal_activity            = Column(Float, nullable=False, default=0)  # 0-10: NDAs, MTAs, DUAs, MRAs, CTAs
    talent_pipeline           = Column(Float, nullable=False, default=0)  # 0-10: hires, internships, fellowships
    engagement_depth          = Column(Float, nullable=False, default=0)  # 0-10: exec visits, co-events, hosted

    # ── Strategic Opportunity metrics (30 pts) ─────────────────────────────
    strategic_fit       = Column(Float, nullable=False, default=0)  # 0-10
    growth_greenfield   = Column(Float, nullable=False, default=0)  # 0-10
    access_influence    = Column(Float, nullable=False, default=0)  # 0-10
    feasibility_timing  = Column(Float, nullable=False, default=0)  # 0-10

    # ── CFR Strategic Plan alignment (SP-01 to SP-06, each 0-10) ──────────
    sp01_org_structure  = Column(Float, nullable=False, default=5)
    sp02_front_door     = Column(Float, nullable=False, default=5)
    sp03_metrics        = Column(Float, nullable=False, default=5)
    sp04_team_capacity  = Column(Float, nullable=False, default=5)
    sp05_data_crm       = Column(Float, nullable=False, default=5)
    sp06_awareness      = Column(Float, nullable=False, default=5)

    # ── Procurement pipeline ────────────────────────────────────────────────
    procurement_stage   = Column(String,  nullable=True)   # Discovery/Design/Implementation/Active
    est_annual_value_k  = Column(Float,   nullable=True)   # estimated annual $k
    procurement_notes   = Column(Text,    nullable=True)


class BenchmarkPeer(Base):
    """Peer institution benchmarking data (from 2025 CFR Benchmarking doc)."""
    __tablename__ = "benchmark_peers"
    id   = Column(Integer, primary_key=True, autoincrement=True)
    institution = Column(String, nullable=False)
    state       = Column(String, nullable=False)
    tier        = Column(String, nullable=False)   # Aspirational / Peer / Emerging

    # Maturity indicators (0-10 scale)
    specialist_model       = Column(Float, nullable=False, default=0)
    holistic_front_door    = Column(Float, nullable=False, default=0)
    modern_metrics         = Column(Float, nullable=False, default=0)
    crm_infrastructure     = Column(Float, nullable=False, default=0)
    executive_engagement   = Column(Float, nullable=False, default=0)
    cross_campus_alignment = Column(Float, nullable=False, default=0)

    active_partners     = Column(Integer, nullable=True)
    annual_research_m   = Column(Float,   nullable=True)  # $M sponsored research
    annual_philanthropy_m = Column(Float, nullable=True)  # $M philanthropy
    cfr_fte             = Column(Float,   nullable=True)  # FTE in corporate relations
    notes               = Column(Text,    nullable=True)


class StrategicPriority(Base):
    """CFR Strategic Plan — 6 priorities tracker."""
    __tablename__ = "strategic_priorities"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    code        = Column(String,  nullable=False, unique=True)   # SP-01 … SP-06
    title       = Column(String,  nullable=False)
    description = Column(Text,    nullable=True)
    status      = Column(String,  nullable=False, default="In Progress")  # Not Started/In Progress/Complete
    progress_pct= Column(Float,   nullable=False, default=0)    # 0-100
    owner       = Column(String,  nullable=True)
    target_date = Column(String,  nullable=True)
    priority_weight = Column(Float, nullable=False, default=1.0)  # relative importance


class Recommendation(Base):
    """CFR Recommendations registry."""
    __tablename__ = "recommendations"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    partner_id  = Column(Integer, nullable=True)    # FK to partners.id (nullable = institution-wide)
    title       = Column(String,  nullable=False)
    category    = Column(String,  nullable=False)   # Research/Philanthropy/Talent/Strategic/Procurement
    priority    = Column(String,  nullable=False)   # High/Medium/Low
    description = Column(Text,    nullable=True)
    est_value_k = Column(Float,   nullable=True)    # estimated $k impact
    timeline    = Column(String,  nullable=True)    # e.g. "Q3 2025"
    status      = Column(String,  nullable=False, default="Open")  # Open/In Progress/Closed


class FundingOpportunity(Base):
    """
    Consolidated funding opportunity record.
    CFR staff paste/upload from 3 listservs into one place.
    """
    __tablename__ = "funding_opportunities"
    id          = Column(Integer, primary_key=True, autoincrement=True)

    # Core fields (always required)
    title       = Column(String, nullable=False)
    sponsor     = Column(String, nullable=False)       # NSF, NIH, DARPA, Private, etc.
    deadline    = Column(String, nullable=True)        # stored as string e.g. "2025-09-15"
    amount_min_k= Column(Float,  nullable=True)        # min award in $k
    amount_max_k= Column(Float,  nullable=True)        # max award in $k

    # Classification
    source      = Column(String, nullable=True)        # which listserv/owner it came from
    research_areas = Column(String, nullable=True)     # comma-separated tags: "Health, AI, Energy"
    eligibility = Column(String, nullable=True)        # "Faculty", "Postdoc", "Team", "All"
    opp_type    = Column(String, nullable=True)        # Grant / Contract / Fellowship / RFP / LSO
    status      = Column(String, nullable=False, default="Active")  # Active / Closing Soon / Expired / Archived

    # LSO — Limited Submission Opportunity fields
    is_lso               = Column(Boolean, nullable=False, default=False)  # True if LSO
    lso_slots            = Column(Integer, nullable=True)   # how many proposals UVA can submit
    lso_internal_deadline= Column(String, nullable=True)    # internal competition deadline
    lso_internal_status  = Column(String, nullable=True)    # Open / In Review / Awarded / Closed
    lso_nominees         = Column(Text,   nullable=True)    # comma-separated nominee names (internal)

    # Detail
    description = Column(Text,   nullable=True)
    url         = Column(String, nullable=True)        # link to full RFP
    notes       = Column(Text,   nullable=True)        # CFR staff notes
    added_by    = Column(String, nullable=True)        # staff name
    date_added  = Column(String, nullable=True)        # ISO date string


class FoundationGrant(Base):
    """
    Grant-level funding history for foundation partners.
    Tracks both UVA-received grants and national giving context.
    """
    __tablename__ = "foundation_grants"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    partner_id       = Column(Integer, nullable=False)   # FK → partners.id
    fiscal_year      = Column(Integer, nullable=True)    # e.g. 2023
    amount_k         = Column(Float,   nullable=True)    # grant amount in $k
    grant_title      = Column(String,  nullable=True)    # descriptive grant name
    program_area     = Column(String,  nullable=True)    # e.g. "Global Health", "AI Research"
    recipient_school = Column(String,  nullable=True)    # e.g. "UVA Health", "Batten School"
    grant_type       = Column(String,  nullable=True)    # "UVA Received" | "National Context"
    notes            = Column(Text,    nullable=True)    # additional context


def create_all():
    Base.metadata.create_all(engine)
    return engine
