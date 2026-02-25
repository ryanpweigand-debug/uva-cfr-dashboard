"""
UVA CFR Partner Engagement Dashboard — Seed Data
Populates the database with sample partners, benchmarks, strategic priorities,
and recommendations derived from the CFR source documents.
"""

import os
from sqlalchemy.orm import Session
from schema import create_all, engine, Partner, BenchmarkPeer, StrategicPriority, Recommendation
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def seed_partners(session):
    partners_data = [
        # (name, sector, hq_city, hq_state, rev_b, emp_k,
        #  sr5, sr_all, p5, p_all, footprint, legal, talent, depth,
        #  fit, growth, access, feasibility,
        #  sp01, sp02, sp03, sp04, sp05, sp06,
        #  stage, est_k, notes)
        ("Amazon",           "Tech",        "Seattle",       "WA", 525.0,  1600,
         4200000, 8100000, 1500000, 3200000, 12, 8, 22, 8.5,
         9.0, 8.0, 9.0, 7.5,  7,7,8,7,9,6,  "Active",     280, "AWS cloud research + internship pipeline"),
        ("Google",           "Tech",        "Mountain View", "CA", 282.0,  180,
         6800000, 14200000, 2800000, 6500000, 18, 12, 35, 9.0,
         9.5, 7.5, 9.5, 7.0,  8,8,9,8,9,7,  "Active",     350, "DeepMind research partnerships; Manning alignment"),
        ("Microsoft",        "Tech",        "Redmond",       "WA", 211.0,  220,
         5100000, 11000000, 3200000, 7800000, 15, 10, 28, 8.8,
         9.0, 8.0, 9.0, 8.0,  8,8,8,8,9,7,  "Active",     320, "Azure for Research; hiring pipeline strong"),
        ("IBM",              "Tech",        "Armonk",        "NY",  60.0,  280,
         2900000, 7400000,  800000, 2100000,  9,  7, 14, 7.2,
         7.5, 6.0, 7.5, 7.0,  6,6,7,6,7,5,  "Design",     150, "Quantum computing collaboration opportunity"),
        ("Intel",            "Tech",        "Santa Clara",   "CA",  54.0,  120,
         3600000, 9200000, 1100000, 2900000, 11,  9, 18, 7.8,
         8.0, 7.0, 8.0, 7.5,  7,7,7,7,8,6,  "Active",     180, "Semiconductor research; CHIPS Act alignment"),
        ("McKinsey",         "Consulting",  "New York",      "NY",  13.0,   45,
         1200000, 3100000, 2500000, 6200000,  5,  4, 10, 7.5,
         7.0, 8.5, 8.5, 8.0,  6,8,7,7,6,8,  "Active",     200, "MBA recruiting; advisory board presence"),
        ("Deloitte",         "Consulting",  "New York",      "NY",  59.0,  450,
          980000, 2400000, 3100000, 7800000,  4,  3,  8, 7.0,
         6.5, 8.0, 8.0, 8.5,  6,8,7,7,6,8,  "Active",     175, "Accounting + consulting recruiting pipeline"),
        ("BCG",              "Consulting",  "Boston",        "MA",  12.0,   32,
          750000, 1900000, 1800000, 4400000,  3,  2,  7, 6.5,
         6.0, 7.5, 7.5, 8.0,  5,7,6,6,5,7,  "Design",     120, "Strategy talent source; case competition sponsor"),
        ("Booz Allen",       "Consulting",  "McLean",        "VA",  10.0,   33,
         2100000, 5800000,  600000, 1500000,  7,  6, 12, 6.8,
         7.0, 7.0, 7.0, 7.5,  6,7,7,7,6,6,  "Active",     160, "DoD research overlap; Northern VA proximity"),
        ("Raytheon",         "Defense",     "Waltham",       "MA",  67.0,  185,
         8200000, 19500000, 400000, 1100000, 14, 15, 16, 8.2,
         8.5, 6.0, 8.0, 7.0,  7,6,7,7,7,5,  "Active",     220, "DARPA-adjacent research; strong IP pipeline"),
        ("Lockheed Martin",  "Defense",     "Bethesda",      "MD",  66.0,  116,
         9800000, 23000000, 600000, 1700000, 16, 18, 20, 8.8,
         9.0, 5.5, 8.5, 6.5,  8,6,8,7,7,5,  "Active",     250, "Largest sponsored research partner; engineering focus"),
        ("Northrop Grumman", "Defense",     "Falls Church",  "VA",  39.0,   95,
         7100000, 16800000, 300000,  800000, 11, 13, 14, 7.9,
         8.0, 5.0, 8.0, 6.5,  7,6,7,6,7,5,  "Active",     190, "VA headquarters — strong regional connection"),
        ("General Dynamics", "Defense",     "Reston",        "VA",  39.0,  100,
         5400000, 12600000, 500000, 1300000,  9, 11, 11, 7.4,
         7.5, 5.5, 7.5, 7.0,  7,6,7,6,7,5,  "Design",     170, "IT + defense; Reston VA presence"),
        ("L3 Technologies",  "Defense",     "New York",      "NY",  19.0,   50,
         3200000, 7900000,  200000,  550000,  6,  8,  8, 6.5,
         7.0, 5.0, 7.0, 7.0,  6,5,6,5,6,4,  "Discovery",  100, "Emerging defense partner; early stage"),
        ("Johnson & Johnson","Healthcare",  "New Brunswick", "NJ",  93.0,  152,
         2600000, 6200000, 3800000, 9400000,  8,  9, 12, 8.0,
         8.5, 7.5, 8.0, 7.5,  7,8,8,7,7,7,  "Active",     230, "UVA Health clinical trial pipeline; med device"),
        ("Pfizer",           "Pharma",      "New York",      "NY",  58.0,   83,
         4800000, 11200000, 2100000, 5300000, 13, 11, 20, 8.3,
         8.5, 7.0, 8.5, 7.0,  7,7,8,7,8,6,  "Active",     260, "Clinical research + pharmacy school alignment"),
        ("Moderna",          "Pharma",      "Cambridge",     "MA",  18.0,   17,
         5200000,  8900000, 1400000, 2800000, 11, 10, 18, 8.1,
         8.0, 9.0, 8.0, 8.0,  7,7,7,7,8,6,  "Active",     240, "mRNA research partnership; rapid growth partner"),
        ("AstraZeneca",      "Pharma",      "Wilmington",    "DE",  45.0,   83,
         3900000, 9100000, 1700000, 4200000, 10,  9, 15, 7.7,
         8.0, 7.5, 8.0, 7.5,  6,7,7,6,7,6,  "Active",     200, "Oncology + cardiology research alignment"),
        ("Merck",            "Pharma",      "Rahway",        "NJ",  60.0,   68,
         3400000, 8300000, 2200000, 5500000,  9,  8, 14, 7.5,
         8.0, 6.5, 7.5, 7.5,  6,7,7,6,7,6,  "Design",     190, "Vaccine research + UVA Health collaboration"),
        ("UnitedHealth",     "Healthcare",  "Minnetonka",    "MN", 324.0,  440,
         1100000, 2700000, 4500000, 11000000, 4,  3,  7, 7.2,
         7.0, 8.0, 7.5, 8.5,  5,8,7,6,6,7,  "Design",     150, "Health systems + data analytics opportunity"),
        ("Cigna",            "Healthcare",  "Bloomfield",    "CT",  46.0,   70,
          800000, 1900000, 2900000, 7200000,  3,  2,  5, 6.5,
         6.5, 7.5, 7.0, 8.0,  5,7,6,5,5,6,  "Discovery",  100, "Health policy research prospect"),
        ("Siemens",          "Tech",        "Munich",        "DE", 100.0,  300,
         2200000, 5400000,  900000, 2300000,  7,  6, 10, 7.0,
         7.5, 7.0, 7.0, 7.5,  6,6,6,6,7,5,  "Design",     140, "Smart grid + healthcare imaging research"),
        ("Honeywell",        "Tech",        "Charlotte",     "NC",  36.0,   99,
         1800000, 4600000,  700000, 1800000,  6,  5,  9, 6.8,
         7.0, 6.5, 7.0, 7.5,  5,6,6,5,6,5,  "Discovery",  120, "Aerospace + building tech; Charlotte proximity"),
        ("Accenture",        "Consulting",  "Dublin",        "IE",  65.0,  750,
         1500000, 3800000, 1200000, 3000000,  5,  4, 11, 7.0,
         6.5, 7.5, 7.5, 8.0,  5,7,6,6,6,7,  "Design",     130, "Digital transformation; Darden partnerships"),
        ("SAIC",             "Defense",     "Reston",        "VA",   7.5,   26,
         4100000, 9800000,  250000,  640000,  8, 10, 13, 7.3,
         7.5, 6.0, 7.5, 7.0,  7,6,7,6,7,5,  "Active",     165, "VA-based; national security research partner"),
        # Additional partners
        ("Capital One",      "Finance",     "McLean",        "VA",  35.0,   55,
          950000, 2200000, 3500000, 8500000,  4,  3,  9, 7.0,
         7.0, 9.0, 7.0, 9.0,  5,8,7,5,7,8,  "Design",     200, "McLean HQ — massive local hiring + data science"),
        ("Dominion Energy",  "Energy",      "Richmond",      "VA",  14.0,   17,
          600000, 1800000, 2200000, 5400000,  3,  2,  6, 6.5,
         7.0, 8.5, 6.5, 8.5,  5,7,6,5,6,7,  "Discovery",  130, "Clean energy + environmental policy alignment"),
        ("BAE Systems",      "Defense",     "Arlington",     "VA",  28.0,   90,
         3800000, 8600000,  180000,  480000,  7,  9, 10, 7.1,
         7.5, 5.5, 7.5, 7.0,  6,5,7,6,6,4,  "Active",     160, "Cyber + defense; Arlington VA presence"),
        ("Eli Lilly",        "Pharma",      "Indianapolis",  "IN",  28.0,   37,
         2800000, 6500000, 1600000, 3900000,  8,  7, 13, 7.6,
         8.0, 7.0, 7.5, 7.5,  6,7,7,6,7,6,  "Design",     180, "Alzheimer's + diabetes research; UVA Health"),
        ("Coca-Cola",        "Consulting",  "Atlanta",       "GA",  46.0,   82,
          200000,  550000, 2800000, 6800000,  2,  2,  8, 6.0,
         6.0, 9.5, 6.0, 9.5,  4,9,6,4,5,8,  "Discovery",  250, "Procurement holistic model — $200-300k/yr potential (scholarships+interns+marketing)"),
    ]

    for p in partners_data:
        (name, sector, city, state, rev_b, emp_k,
         sr5, sr_all, p5, p_all, footprint, legal, talent, depth,
         fit, growth, access, feasibility,
         sp01, sp02, sp03, sp04, sp05, sp06,
         stage, est_k, notes) = p

        session.add(Partner(
            name=name, sector=sector, hq_city=city, hq_state=state,
            revenue_b=rev_b, employees_k=float(emp_k),
            sponsored_research_5yr=float(sr5), sponsored_research_alltime=float(sr_all),
            philanthropy_5yr=float(p5), philanthropy_alltime=float(p_all),
            research_footprint=float(footprint), legal_activity=float(legal),
            talent_pipeline=float(talent), engagement_depth=float(depth),
            strategic_fit=float(fit), growth_greenfield=float(growth),
            access_influence=float(access), feasibility_timing=float(feasibility),
            sp01_org_structure=float(sp01), sp02_front_door=float(sp02),
            sp03_metrics=float(sp03), sp04_team_capacity=float(sp04),
            sp05_data_crm=float(sp05), sp06_awareness=float(sp06),
            procurement_stage=stage, est_annual_value_k=float(est_k), notes=notes,
        ))


def seed_benchmarks(session):
    peers = [
        # (institution, state, tier, spec, front_door, metrics, crm, exec, cross, partners, research_m, phil_m, fte, notes)
        ("Georgia Tech",       "GA", "Aspirational",
         9, 9, 9, 9, 9, 8,  320, 285.0, 48.0, 12, "Best-in-class specialist model; dedicated industry verticals"),
        ("UT-Austin",          "TX", "Aspirational",
         8, 8, 8, 8, 8, 8,  280, 312.0, 52.0, 11, "Energy sector strength; integrated front door"),
        ("U Minnesota",        "MN", "Aspirational",
         8, 7, 8, 7, 8, 7,  250, 268.0, 44.0, 10, "Med device + ag tech; strong CRM adoption"),
        ("UNC-Chapel Hill",    "NC", "Peer",
         7, 7, 7, 7, 7, 7,  180, 198.0, 38.0,  8, "Closest benchmark; similar public R1 profile"),
        ("U Memphis",          "TN", "Peer",
         6, 6, 6, 6, 6, 6,   80,  62.0, 15.0,  5, "Regional focus; emerging corporate relations function"),
        ("Kansas State",       "KS", "Peer",
         5, 5, 6, 5, 6, 5,   60,  48.0, 12.0,  4, "Ag + defense; growing industry engagement"),
        ("UVA (Current)",      "VA", "Self",
         5, 4, 4, 4, 5, 5,  150, 180.0, 35.0,  6, "Baseline: CFR team building; opportunity for specialist model"),
        ("UVA (Target)",       "VA", "Self",
         8, 8, 8, 8, 8, 8,  220, 260.0, 55.0, 10, "3-year target aligned with CFR Strategic Plan"),
    ]
    for p in peers:
        (inst, state, tier, spec, fd, met, crm, exc, cross,
         partners, res, phil, fte, notes) = p
        session.add(BenchmarkPeer(
            institution=inst, state=state, tier=tier,
            specialist_model=float(spec), holistic_front_door=float(fd),
            modern_metrics=float(met), crm_infrastructure=float(crm),
            executive_engagement=float(exc), cross_campus_alignment=float(cross),
            active_partners=partners, annual_research_m=float(res),
            annual_philanthropy_m=float(phil), cfr_fte=float(fte), notes=notes,
        ))


def seed_strategic_priorities(session):
    sp_data = [
        ("SP-01", "Strengthen Organizational Structure",
         "Define clear roles, reporting lines, and accountability within CFR. "
         "Create a specialist-driven model with vertical leads for key sectors "
         "(Tech, Defense, Healthcare, Pharma) modeled on Georgia Tech and UT-Austin.",
         "In Progress", 45, "CFR Director", "Q4 2025", 1.2),
        ("SP-02", "Establish Holistic 'Front Door' for Partners",
         "Create a single, unified entry point for corporate partners across all "
         "UVA schools and units. Develop the Procurement Partnership model "
         "(scholarships + internships + sponsored research + marketing) "
         "as exemplified by the Coca-Cola holistic engagement framework.",
         "In Progress", 30, "VP External Relations", "Q1 2026", 1.5),
        ("SP-03", "Revamp CFR Metrics & Performance",
         "Replace activity-based metrics with outcome-based KPIs. Implement "
         "Ahsan's 100-pt Partner Scoring Methodology. Track: partner tier "
         "progression, total economic value, research commercialization rate, "
         "talent pipeline conversion, and cross-campus engagement breadth.",
         "In Progress", 60, "CFR Analytics Lead", "Q3 2025", 1.3),
        ("SP-04", "Expand and Specialize Team",
         "Hire 4 industry-sector specialists over 24 months. Develop career paths "
         "for CFR staff. Benchmark staffing against peer institutions "
         "(Georgia Tech: 12 FTE; UT-Austin: 11 FTE vs. UVA current: 6 FTE).",
         "Not Started", 10, "CFR Director / CHRO", "Q2 2026", 1.1),
        ("SP-05", "Improve Data and CRM Infrastructure",
         "Implement a unified CRM (Salesforce or equivalent) that integrates "
         "OVPR, Advancement, Career Center, and OGC data. Enable real-time "
         "partner scoring and relationship tracking. Target: full data parity "
         "with peer institutions by Q4 2025.",
         "In Progress", 40, "IT / CFR Analytics", "Q4 2025", 1.4),
        ("SP-06", "Increase Internal Awareness & Alignment",
         "Launch internal communications campaign to ensure all UVA schools and "
         "units understand CFR's role as the corporate front door. Develop "
         "engagement playbooks for deans, department chairs, and PI teams. "
         "Host quarterly internal showcases of partner success stories.",
         "Not Started", 15, "Marketing / External Relations", "Q1 2026", 1.0),
    ]
    for code, title, desc, status, pct, owner, date, weight in sp_data:
        session.add(StrategicPriority(
            code=code, title=title, description=desc,
            status=status, progress_pct=float(pct),
            owner=owner, target_date=date, priority_weight=weight,
        ))


def seed_recommendations(session):
    recs = [
        # (partner_id, title, category, priority, desc, est_k, timeline, status)
        (None, "Launch Sector Specialist Hiring",
         "Strategic", "High",
         "Hire 4 industry-sector specialists (Tech, Defense, Healthcare, Pharma) "
         "to deepen relationships with top-tier partners. Model after Georgia Tech's "
         "specialist-driven team structure.",
         500, "Q1 2026", "Open"),
        (None, "Implement Unified CRM (Salesforce)",
         "Strategic", "High",
         "Deploy Salesforce for Corporate Relations to integrate OVPR, Advancement, "
         "and Career Center data. Enable real-time partner scoring dashboard.",
         350, "Q4 2025", "In Progress"),
        (None, "Develop Holistic Partner Packages",
         "Procurement", "High",
         "Create bundled engagement packages (Research + Talent + Philanthropy + "
         "Brand) modeled on the Coca-Cola procurement framework. Target 5 pilot "
         "partners in FY2025. Estimated value: $200-300k/yr per partner.",
         1200, "Q3 2025", "In Progress"),
        (1, "Expand Amazon AWS Research Partnership",
         "Research", "High",
         "Leverage AWS for Research credits program. Target 2 new PI grants via "
         "Amazon Research Awards. Estimated incremental sponsored research: $800k.",
         800, "Q2 2025", "Open"),
        (2, "Google DeepMind Research Initiative",
         "Research", "High",
         "Formalize collaboration with Google DeepMind for AI/ML research. "
         "Align with Manning Institute priorities. Estimated value: $1.2M/yr.",
         1200, "Q1 2026", "Open"),
        (10, "Raytheon Engineering Fellowship",
         "Talent", "High",
         "Launch dedicated Raytheon Engineering Fellowship for UVA graduate students "
         "in Electrical and Systems Engineering. Target 5 fellows/yr at $25k each.",
         125, "Q4 2025", "Open"),
        (14, "Johnson & Johnson Clinical Trial Network",
         "Research", "High",
         "Expand J&J clinical trial partnership through UVA Health. "
         "Target 3 new Phase II/III trials. Estimated research value: $2M+.",
         2000, "Q2 2026", "Open"),
        (15, "Pfizer UVA Health Drug Development Collaboration",
         "Research", "Medium",
         "Establish Pfizer-UVA joint lab for early-stage drug discovery. "
         "Leverage UVA's Pharmacology department strengths.",
         900, "Q3 2025", "Open"),
        (26, "Capital One Data Science Partnership",
         "Research", "High",
         "Capital One McLean HQ creates natural proximity. Establish data science "
         "research partnership + co-op pipeline. Estimated 15 co-ops/yr.",
         300, "Q2 2025", "In Progress"),
        (29, "Coca-Cola Holistic Engagement Model",
         "Procurement", "Medium",
         "Execute 3-phase Discovery/Design/Implementation plan. Target $200-300k/yr "
         "package: scholarships ($75k) + internships ($100k) + marketing ($75k+). "
         "Contract template ready.",
         250, "Q4 2025", "Open"),
        (None, "UVA CFR Benchmarking Dashboard Launch",
         "Strategic", "Medium",
         "Present peer benchmarking analysis to CFR leadership and UVA Provost. "
         "Use dashboard data to justify SP-04 team expansion ask.",
         0, "Q3 2025", "In Progress"),
        (None, "Partner Tier Review (Annual)",
         "Strategic", "Medium",
         "Conduct annual review of all partner scores and tier assignments. "
         "Promote Active partners to Strategic with dedicated action plans.",
         0, "Q4 2025", "Open"),
    ]
    for r in recs:
        (pid, title, cat, pri, desc, est_k, timeline, status) = r
        session.add(Recommendation(
            partner_id=pid, title=title, category=cat, priority=pri,
            description=desc, est_value_k=float(est_k) if est_k else 0,
            timeline=timeline, status=status,
        ))


def ensure_db():
    """Create DB and seed data if it doesn't already exist."""
    db_path = os.path.join(BASE_DIR, "cfr_partners.db")
    if os.path.exists(db_path):
        return  # Already seeded
    print("Creating database and seeding data...")
    create_all()
    with Session(engine) as session:
        seed_partners(session)
        seed_benchmarks(session)
        seed_strategic_priorities(session)
        seed_recommendations(session)
        session.commit()
    print(f"Database created: {db_path}")


if __name__ == "__main__":
    # Allow re-seeding from command line
    db_path = os.path.join(BASE_DIR, "cfr_partners.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed existing database.")
    ensure_db()
    print("Done.")
