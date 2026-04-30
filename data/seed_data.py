"""
UVA CFR Partner Engagement Dashboard — Seed Data
Populates the database with sample partners, benchmarks, strategic priorities,
and recommendations derived from the CFR source documents.
"""

import os
from sqlalchemy.orm import Session
from schema import create_all, engine, Partner, BenchmarkPeer, StrategicPriority, Recommendation, FundingOpportunity, FoundationGrant
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def seed_partners(session):
    partners_data = [
        # (name, sector, hq_city, hq_state, rev_b, emp_k,
        #  sr5, sr_all, p5, proc_score, fac_eng, legal, talent, depth,
        #  fit, growth, access, feasibility,
        #  sp01, sp02, sp03, sp04, sp05, sp06,
        #  stage, est_k, notes)
        # proc_score  0-10: procurement $ of goods/services UVA buys from org (5yr)
        # fac_eng     0-10: faculty active awards, projects, advisory roles, IP, startups
        # legal       0-10: NDAs, MTAs, DUAs, MRAs, clinical trials agreements
        # talent      0-10: hires, internships, fellowships, capstones, residencies
        # depth       0-10: exec-level visits, co-branded events, hosted engagements
        ("Amazon",           "Tech",        "Seattle",       "WA", 525.0,  1600,
         4200000, 8100000, 1500000, 8.5, 8.5, 7.0, 8.5, 8.5,
         9.0, 8.0, 9.0, 7.5,  7,7,8,7,9,6,  "Active",     280, "AWS cloud research + internship pipeline"),
        ("Google",           "Tech",        "Mountain View", "CA", 282.0,  180,
         6800000, 14200000, 2800000, 8.0, 9.5, 8.0, 9.0, 9.0,
         9.5, 7.5, 9.5, 7.0,  8,8,9,8,9,7,  "Active",     350, "DeepMind research partnerships; Manning alignment"),
        ("Microsoft",        "Tech",        "Redmond",       "WA", 211.0,  220,
         5100000, 11000000, 3200000, 8.5, 9.0, 7.5, 8.5, 8.8,
         9.0, 8.0, 9.0, 8.0,  8,8,8,8,9,7,  "Active",     320, "Azure for Research; hiring pipeline strong"),
        ("IBM",              "Tech",        "Armonk",        "NY",  60.0,  280,
         2900000, 7400000,  800000, 5.5, 7.5, 6.0, 5.5, 7.2,
         7.5, 6.0, 7.5, 7.0,  6,6,7,6,7,5,  "Design",     150, "Quantum computing collaboration opportunity"),
        ("Intel",            "Tech",        "Santa Clara",   "CA",  54.0,  120,
         3600000, 9200000, 1100000, 6.5, 8.0, 6.5, 7.0, 7.8,
         8.0, 7.0, 8.0, 7.5,  7,7,7,7,8,6,  "Active",     180, "Semiconductor research; CHIPS Act alignment"),
        ("McKinsey",         "Consulting",  "New York",      "NY",  13.0,   45,
         1200000, 3100000, 2500000, 7.5, 5.0, 4.0, 7.5, 7.5,
         7.0, 8.5, 8.5, 8.0,  6,8,7,7,6,8,  "Active",     200, "MBA recruiting; advisory board presence"),
        ("Deloitte",         "Consulting",  "New York",      "NY",  59.0,  450,
          980000, 2400000, 3100000, 7.0, 4.5, 3.5, 7.5, 7.0,
         6.5, 8.0, 8.0, 8.5,  6,8,7,7,6,8,  "Active",     175, "Accounting + consulting recruiting pipeline"),
        ("BCG",              "Consulting",  "Boston",        "MA",  12.0,   32,
          750000, 1900000, 1800000, 6.0, 4.5, 3.0, 6.5, 6.5,
         6.0, 7.5, 7.5, 8.0,  5,7,6,6,5,7,  "Design",     120, "Strategy talent source; case competition sponsor"),
        ("Booz Allen",       "Consulting",  "McLean",        "VA",  10.0,   33,
         2100000, 5800000,  600000, 6.0, 6.5, 5.5, 6.0, 6.8,
         7.0, 7.0, 7.0, 7.5,  6,7,7,7,6,6,  "Active",     160, "DoD research overlap; Northern VA proximity"),
        ("Raytheon",         "Defense",     "Waltham",       "MA",  67.0,  185,
         8200000, 19500000, 400000, 6.5, 8.0, 8.0, 6.5, 8.2,
         8.5, 6.0, 8.0, 7.0,  7,6,7,7,7,5,  "Active",     220, "DARPA-adjacent research; strong IP pipeline"),
        ("Lockheed Martin",  "Defense",     "Bethesda",      "MD",  66.0,  116,
         9800000, 23000000, 600000, 7.0, 8.5, 9.0, 7.5, 8.8,
         9.0, 5.5, 8.5, 6.5,  8,6,8,7,7,5,  "Active",     250, "Largest sponsored research partner; engineering focus"),
        ("Northrop Grumman", "Defense",     "Falls Church",  "VA",  39.0,   95,
         7100000, 16800000, 300000, 6.5, 7.5, 7.5, 6.5, 7.9,
         8.0, 5.0, 8.0, 6.5,  7,6,7,6,7,5,  "Active",     190, "VA headquarters — strong regional connection"),
        ("General Dynamics", "Defense",     "Reston",        "VA",  39.0,  100,
         5400000, 12600000, 500000, 6.0, 7.0, 7.0, 6.0, 7.4,
         7.5, 5.5, 7.5, 7.0,  7,6,7,6,7,5,  "Design",     170, "IT + defense; Reston VA presence"),
        ("L3 Technologies",  "Defense",     "New York",      "NY",  19.0,   50,
         3200000, 7900000,  200000, 3.5, 5.5, 5.0, 4.5, 6.5,
         7.0, 5.0, 7.0, 7.0,  6,5,6,5,6,4,  "Discovery",  100, "Emerging defense partner; early stage"),
        ("Johnson & Johnson","Healthcare",  "New Brunswick", "NJ",  93.0,  152,
         2600000, 6200000, 3800000, 8.0, 8.0, 8.0, 7.0, 8.0,
         8.5, 7.5, 8.0, 7.5,  7,8,8,7,7,7,  "Active",     230, "UVA Health clinical trial pipeline; med device"),
        ("Pfizer",           "Pharma",      "New York",      "NY",  58.0,   83,
         4800000, 11200000, 2100000, 7.5, 8.5, 8.0, 7.5, 8.3,
         8.5, 7.0, 8.5, 7.0,  7,7,8,7,8,6,  "Active",     260, "Clinical research + pharmacy school alignment"),
        ("Moderna",          "Pharma",      "Cambridge",     "MA",  18.0,   17,
         5200000,  8900000, 1400000, 7.0, 8.0, 7.5, 7.0, 8.1,
         8.0, 9.0, 8.0, 8.0,  7,7,7,7,8,6,  "Active",     240, "mRNA research partnership; rapid growth partner"),
        ("AstraZeneca",      "Pharma",      "Wilmington",    "DE",  45.0,   83,
         3900000, 9100000, 1700000, 6.5, 7.5, 7.0, 6.5, 7.7,
         8.0, 7.5, 8.0, 7.5,  6,7,7,6,7,6,  "Active",     200, "Oncology + cardiology research alignment"),
        ("Merck",            "Pharma",      "Rahway",        "NJ",  60.0,   68,
         3400000, 8300000, 2200000, 6.0, 7.5, 7.0, 6.5, 7.5,
         8.0, 6.5, 7.5, 7.5,  6,7,7,6,7,6,  "Design",     190, "Vaccine research + UVA Health collaboration"),
        ("UnitedHealth",     "Healthcare",  "Minnetonka",    "MN", 324.0,  440,
         1100000, 2700000, 4500000, 7.0, 6.0, 4.0, 6.5, 7.2,
         7.0, 8.0, 7.5, 8.5,  5,8,7,6,6,7,  "Design",     150, "Health systems + data analytics opportunity"),
        ("Cigna",            "Healthcare",  "Bloomfield",    "CT",  46.0,   70,
          800000, 1900000, 2900000, 5.0, 5.0, 3.5, 5.0, 6.5,
         6.5, 7.5, 7.0, 8.0,  5,7,6,5,5,6,  "Discovery",  100, "Health policy research prospect"),
        ("Siemens",          "Tech",        "Munich",        "DE", 100.0,  300,
         2200000, 5400000,  900000, 5.5, 7.0, 6.5, 5.5, 7.0,
         7.5, 7.0, 7.0, 7.5,  6,6,6,6,7,5,  "Design",     140, "Smart grid + healthcare imaging; exclusive radiology agreement"),
        ("Honeywell",        "Tech",        "Charlotte",     "NC",  36.0,   99,
         1800000, 4600000,  700000, 5.0, 6.0, 5.0, 5.5, 6.8,
         7.0, 6.5, 7.0, 7.5,  5,6,6,5,6,5,  "Discovery",  120, "Aerospace + building tech; Charlotte proximity"),
        ("Accenture",        "Consulting",  "Dublin",        "IE",  65.0,  750,
         1500000, 3800000, 1200000, 6.5, 5.0, 4.0, 7.0, 7.0,
         6.5, 7.5, 7.5, 8.0,  5,7,6,6,6,7,  "Design",     130, "Digital transformation; Darden partnerships"),
        ("SAIC",             "Defense",     "Reston",        "VA",   7.5,   26,
         4100000, 9800000,  250000, 5.5, 7.0, 7.0, 6.0, 7.3,
         7.5, 6.0, 7.5, 7.0,  7,6,7,6,7,5,  "Active",     165, "VA-based; national security research partner"),
        ("Capital One",      "Finance",     "McLean",        "VA",  35.0,   55,
          950000, 2200000, 3500000, 8.5, 6.5, 4.5, 8.0, 7.0,
         7.0, 9.0, 7.0, 9.0,  5,8,7,5,7,8,  "Design",     200, "McLean HQ — massive local hiring + data science"),
        ("Dominion Energy",  "Energy",      "Richmond",      "VA",  14.0,   17,
          600000, 1800000, 2200000, 6.5, 6.0, 4.0, 5.5, 6.5,
         7.0, 8.5, 6.5, 8.5,  5,7,6,5,6,7,  "Discovery",  130, "Clean energy + environmental policy alignment"),
        ("BAE Systems",      "Defense",     "Arlington",     "VA",  28.0,   90,
         3800000, 8600000,  180000, 5.0, 6.5, 6.5, 5.5, 7.1,
         7.5, 5.5, 7.5, 7.0,  6,5,7,6,6,4,  "Active",     160, "Cyber + defense; Arlington VA presence"),
        ("Eli Lilly",        "Pharma",      "Indianapolis",  "IN",  28.0,   37,
         2800000, 6500000, 1600000, 6.5, 7.5, 6.5, 6.5, 7.6,
         8.0, 7.0, 7.5, 7.5,  6,7,7,6,7,6,  "Design",     180, "Alzheimer's + diabetes research; UVA Health"),
        ("Coca-Cola",        "Consulting",  "Atlanta",       "GA",  46.0,   82,
          200000,  550000, 2800000, 9.5, 3.5, 2.5, 7.0, 6.0,
         6.0, 9.5, 6.0, 9.5,  4,9,6,4,5,8,  "Discovery",  250, "Procurement holistic model — $200-300k/yr potential (scholarships+interns+marketing)"),
    ]

    for p in partners_data:
        (name, sector, city, state, rev_b, emp_k,
         sr5, sr_all, p5, proc_score, fac_eng, legal, talent, depth,
         fit, growth, access, feasibility,
         sp01, sp02, sp03, sp04, sp05, sp06,
         stage, est_k, notes) = p

        session.add(Partner(
            name=name, sector=sector, hq_city=city, hq_state=state,
            revenue_b=rev_b, employees_k=float(emp_k),
            sponsored_research_5yr=float(sr5), sponsored_research_alltime=float(sr_all),
            philanthropy_5yr=float(p5), procurement_score=float(proc_score),
            faculty_engagement=float(fac_eng),
            legal_activity=float(legal), talent_pipeline=float(talent),
            engagement_depth=float(depth),
            strategic_fit=float(fit), growth_greenfield=float(growth),
            access_influence=float(access), feasibility_timing=float(feasibility),
            sp01_org_structure=float(sp01), sp02_front_door=float(sp02),
            sp03_metrics=float(sp03), sp04_team_capacity=float(sp04),
            sp05_data_crm=float(sp05), sp06_awareness=float(sp06),
            procurement_stage=stage, est_annual_value_k=float(est_k), notes=notes,
            partner_type="Corporate",
        ))

    # ── Foundation Partners ────────────────────────────────────────────────
    foundation_data = [
        # (name, sector, hq_city, hq_state, rev_b, emp_k,
        #  sr5, sr_all, p5, proc, fac_eng, legal, talent, depth,
        #  fit, growth, access, feasibility,
        #  sp01,sp02,sp03,sp04,sp05,sp06, stage, est_k, notes)
        ("Bill & Melinda Gates Foundation", "Health",     "Seattle",      "WA", 67.0,  1.9,
          8500000, 21000000, 12000000, 1.0, 8.5, 7.0, 4.0, 7.0,
          9.0, 8.0, 9.0, 7.0,  8,7,8,7,8,7,  "Active",     400,
          "Largest private foundation globally; $7B+ annual giving; global health + equitable development; UVA Health + global studies alignment. 990 EIN: 56-2618866."),
        ("Robert Wood Johnson Foundation",  "Health",     "Princeton",    "NJ", 12.0,  0.4,
          5000000, 14000000,  8000000, 1.0, 7.0, 6.0, 5.0, 6.0,
          8.0, 7.0, 8.0, 8.0,  7,7,7,6,7,7,  "Active",     280,
          "Largest U.S. health-only foundation; ~$450M annual giving; health equity and workforce; alignment with public health + nursing schools. 990 EIN: 22-1992342."),
        ("Bloomberg Philanthropies",        "Health",     "New York",     "NY",  8.0,  1.5,
          3500000,  9000000,  5000000, 2.0, 7.0, 6.0, 5.0, 7.0,
          8.0, 8.0, 9.0, 7.0,  7,8,8,7,7,8,  "Active",     250,
          "Public health + urban innovation; Batten + public policy alignment"),
        ("Wellcome Trust",                  "Health",     "London",       "UK", 38.0,  2.0,
          4000000, 11000000,  2000000, 0.0, 7.0, 6.0, 4.0, 5.0,
          7.0, 7.0, 8.0, 5.0,  6,6,7,6,7,6,  "Design",     180,
          "Global health + mental health research; UVA Health + international initiatives"),
        ("Alfred P. Sloan Foundation",      "Science",    "New York",     "NY",  2.2,  0.06,
          3500000,  9500000,  2000000, 0.0, 8.0, 5.0, 8.0, 6.0,
          8.0, 7.0, 7.0, 8.0,  7,6,7,7,8,6,  "Active",     200,
          "~$90M annual giving; STEM research + fellowships; Sloan Research Fellowships active at UVA; Sloan Digital Sky Survey collaboration. 990 EIN: 13-1623877."),
        ("Simons Foundation",               "Science",    "New York",     "NY",  3.5,  0.8,
          4000000, 11000000,  1500000, 0.0, 8.5, 5.0, 6.0, 5.0,
          8.0, 7.0, 7.0, 7.0,  7,6,7,7,8,5,  "Active",     180,
          "Math + physical/life sciences; Simons Investigators open at UVA"),
        ("Gordon & Betty Moore Foundation", "Science",    "Palo Alto",    "CA",  9.0,  0.2,
          3000000,  8000000,  2000000, 0.0, 7.0, 5.0, 5.0, 5.0,
          7.0, 7.0, 7.0, 6.0,  7,6,7,6,7,5,  "Design",     160,
          "~$300M annual giving; environmental conservation + science + patient care; Moore-Sloan data science partnership; UVA environmental science faculty alignment. 990 EIN: 43-1802723."),
        ("Kavli Foundation",                "Science",    "Los Angeles",  "CA",  1.5,  0.2,
          3000000,  8000000,  1500000, 0.0, 8.0, 5.0, 5.0, 5.0,
          8.0, 7.0, 7.0, 6.0,  7,6,7,6,7,5,  "Design",     150,
          "Astrophysics, neuroscience, nanoscience; physics + neuroscience faculty match"),
        ("Lumina Foundation for Education",  "Education",  "Indianapolis", "IN",  1.6,  0.08,
          2000000,  5500000,  3000000, 0.0, 6.0, 5.0, 7.0, 5.0,
          8.0, 7.0, 7.0, 7.0,  7,7,7,6,7,7,  "Design",     150,
          "Higher ed access + completion; Goal 2025: 60% postsecondary credential rate; strong UVA access initiative alignment"),
        ("W.K. Kellogg Foundation",         "Education",  "Battle Creek", "MI",  9.5,  0.3,
          1500000,  4000000,  2000000, 0.0, 5.0, 4.0, 5.0, 4.0,
          6.0, 6.0, 6.0, 6.0,  5,6,6,5,5,6,  "Discovery",  120,
          "Community engagement + education equity; Curry School alignment"),
        ("Carnegie Corporation of New York","Education",  "New York",     "NY",  3.8,  0.15,
          1500000,  4000000,  3000000, 0.0, 5.0, 4.0, 6.0, 5.0,
          7.0, 6.0, 7.0, 6.0,  6,6,7,5,6,6,  "Discovery",  110,
          "Est. 1911 by Andrew Carnegie; ~$165M annual giving; K-12 reform, civic engagement, African higher ed; Democracy Initiative and Curry School alignment. 990 EIN: 13-1628151."),
        ("MacArthur Foundation",            "Social",     "Chicago",      "IL",  7.0,  0.4,
          2500000,  6500000,  3500000, 0.0, 6.0, 5.0, 5.0, 5.0,
          7.0, 6.0, 7.0, 6.0,  6,6,7,6,6,6,  "Design",     140,
          "Social systems + MacArthur Fellows; Batten + Institute for Advanced Studies"),
        ("Rockefeller Foundation",          "Social",     "New York",     "NY",  5.5,  0.4,
          2000000,  5000000,  4000000, 0.0, 6.0, 5.0, 5.0, 6.0,
          7.0, 7.0, 8.0, 6.0,  6,7,7,6,6,7,  "Design",     160,
          "Global food, health, energy + equitable economies; cross-school alignment"),
        ("Pew Charitable Trusts",           "Social",     "Washington",   "DC",  5.5,  1.0,
          2500000,  6000000,  2000000, 1.0, 6.0, 5.0, 5.0, 6.0,
          7.0, 7.0, 8.0, 7.0,  6,7,7,6,6,7,  "Active",     150,
          "Evidence-based policy research; Batten + UVA law; DC presence valuable"),
        ("Andrew W. Mellon Foundation",     "Arts",       "New York",     "NY",  7.0,  0.1,
          2000000,  5500000,  5000000, 0.0, 7.0, 5.0, 7.0, 6.0,
          7.0, 6.0, 7.0, 6.0,  6,6,7,6,7,7,  "Active",     170,
          "Premier funder of arts + humanities; ~$310M annual giving; HIRE initiative for HBCU/diversity in arts; College of Arts & Sciences and McIntire alignment. 990 EIN: 13-1879954."),
        # ── 9 missing priority foundations added from 990/annual report data ──
        ("Anne Mullen Orell Charitable Trust","Health",   "Charlottesville","VA",  0.003, 0.0,
           50000,    150000,   200000, 0.0, 2.0, 1.0, 1.0, 2.0,
           6.0, 5.0, 6.0, 5.0,  5,5,5,5,5,5,  "Discovery",   20,
           "Small Virginia charitable trust; health + education focus; Virginia-based proximity to UVA is an asset. Minimal public 990 data — recommend IRS TEOS lookup for EIN."),
        ("Arnold Ventures",                  "Social",    "Houston",       "TX",  2.8,  0.2,
           500000,  1500000,  1200000, 0.0, 5.0, 3.0, 4.0, 5.0,
           7.0, 7.0, 7.0, 7.0,  5,7,7,5,5,6,  "Discovery",   80,
           "~$350M annual giving; criminal justice reform, health policy, education, public finance; LLC/501(c)(3) hybrid limits 990 transparency; evidence-based policy focus aligns with Batten School."),
        ("Claude Moore Charitable Foundation","Health",  "McLean",        "VA",  0.2,  0.005,
           500000,  1500000,  1000000, 0.0, 5.0, 3.0, 4.0, 4.0,
           7.0, 6.0, 7.0, 6.0,  6,6,7,5,6,6,  "Discovery",   60,
           "Virginia private foundation; health + medical education focus; funds Inova + UVA; McLean VA location; strong regional alignment. Recommend IRS TEOS for exact EIN."),
        ("Ford Foundation",                  "Social",    "New York",      "NY", 16.0,  0.6,
          2000000,  6000000,  6000000, 0.0, 6.0, 5.0, 7.0, 6.0,
          8.0, 7.0, 8.0, 7.0,  6,7,7,6,7,7,  "Design",     200,
          "~$650M annual giving; inequality, democracy, economic justice, racial equity; 2020 issued $1B social bonds; Batten + Equity Center + UVA Law alignment. 990 EIN: 13-1684331."),
        ("William Randolph Hearst Foundation","Education","New York",      "NY",  0.55, 0.025,
          1000000,  3000000,  1500000, 0.0, 4.0, 3.0, 5.0, 4.0,
          6.0, 5.0, 6.0, 5.0,  5,6,6,5,5,6,  "Discovery",   60,
          "Combined Hearst Foundations ~$35M annual giving; education (scholarships, journalism awards), healthcare access, arts/culture; journalism program aligns with UVA Media Studies."),
        ("William and Flora Hewlett Foundation","Education","Menlo Park",  "CA", 13.0,  0.15,
          1500000,  4500000,  3000000, 0.0, 6.0, 4.0, 6.0, 6.0,
          7.0, 7.0, 7.0, 6.0,  6,7,7,6,7,6,  "Design",     150,
          "~$500M annual giving; education reform, climate/clean energy, open education resources (OER), Western conservation; HP co-founder heritage; STEM + environmental alignment at UVA. 990 EIN: 95-3671029."),
        ("W.M. Keck Foundation",             "Science",   "Los Angeles",  "CA",  1.2,  0.03,
          2000000,  6000000,  2000000, 0.0, 7.0, 4.0, 5.0, 5.0,
          8.0, 7.0, 7.0, 7.0,  6,6,7,6,7,5,  "Design",     120,
          "~$100M annual giving; science/engineering/medical research at universities; Keck Observatory; high-risk research investments; does not fund individuals; STEM + medical research faculty match. 990 EIN: 95-2161724."),
        ("Henry Luce Foundation",            "Arts",      "New York",     "NY",  0.7,  0.03,
          1000000,  3000000,  1200000, 0.0, 5.0, 3.0, 5.0, 4.0,
          6.0, 6.0, 6.0, 5.0,  5,6,6,5,6,6,  "Discovery",   70,
          "~$25M annual giving; Asia-U.S. relations, theology, American art, higher education; Luce Scholars Program places Americans in Asia; UVA International Studies + College of Arts alignment. 990 EIN: 13-1982307."),
        ("David and Lucile Packard Foundation","Science", "Los Altos",    "CA",  9.5,  0.12,
          2500000,  7000000,  3500000, 0.0, 6.0, 4.0, 5.0, 5.0,
          7.0, 7.0, 7.0, 6.0,  6,6,7,6,7,5,  "Design",     140,
          "~$400M annual giving; conservation science (oceans, climate), reproductive health, children's development; HP co-founder heritage; large multi-year grants; UVA environmental + public health alignment. 990 EIN: 94-3085918."),
    ]

    for p in foundation_data:
        (name, sector, city, state, rev_b, emp_k,
         sr5, sr_all, p5, proc_score, fac_eng, legal, talent, depth,
         fit, growth, access, feasibility,
         sp01, sp02, sp03, sp04, sp05, sp06,
         stage, est_k, notes) = p

        session.add(Partner(
            name=name, sector=sector, hq_city=city, hq_state=state,
            revenue_b=rev_b, employees_k=float(emp_k),
            sponsored_research_5yr=float(sr5), sponsored_research_alltime=float(sr_all),
            philanthropy_5yr=float(p5), procurement_score=float(proc_score),
            faculty_engagement=float(fac_eng),
            legal_activity=float(legal), talent_pipeline=float(talent),
            engagement_depth=float(depth),
            strategic_fit=float(fit), growth_greenfield=float(growth),
            access_influence=float(access), feasibility_timing=float(feasibility),
            sp01_org_structure=float(sp01), sp02_front_door=float(sp02),
            sp03_metrics=float(sp03), sp04_team_capacity=float(sp04),
            sp05_data_crm=float(sp05), sp06_awareness=float(sp06),
            procurement_stage=stage, est_annual_value_k=float(est_k), notes=notes,
            partner_type="Foundation",
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


def seed_foundation_recommendations(session):
    """
    Foundation-specific ask strategy recommendations (category='Foundation').
    Derived from each foundation's grant history + UVA's institutional strengths.
    Runs after seed_partners so we can resolve real partner IDs by name.
    """
    pid_map = {p.name: p.id for p in session.query(Partner).filter_by(partner_type="Foundation")}

    # (partner_name, title, priority, desc, est_k, timeline)
    fnd_recs = [
        # 1. Bill & Melinda Gates Foundation
        ("Bill & Melinda Gates Foundation",
         "Gates Foundation — Global Health Convergence Initiative", "High",
         "Gates has funded UVA Health across global health equity, mRNA vaccine research, and "
         "COVID-19 surveillance (FY 2021–2023). Next ask: propose a multi-year convergence award "
         "combining UVA Health's infectious disease bench strength with the Frank Batten School's "
         "health policy expertise. Target the Gates Grand Challenges Explorations round with a "
         "co-PI model spanning medicine + public policy. Leverage existing relationship to request "
         "a program officer meeting before submission. Estimated $3–5M multi-year award.",
         4000, "Q2 2025"),

        # 2. Robert Wood Johnson Foundation
        ("Robert Wood Johnson Foundation",
         "RWJF — Virginia Rural Health Workforce Pipeline", "High",
         "RWJF's Culture of Health program maps directly onto UVA's School of Nursing rural "
         "outreach and Batten School's health policy research (funded separately FY 2021–2023). "
         "Next ask: a 3-year bundled grant building a Virginia Rural Health Workforce Pipeline — "
         "nurse training, telehealth deployment, and Batten-led policy evaluation as one package. "
         "RWJF prefers proposals that bridge clinical delivery and policy impact; UVA's multi-school "
         "structure is uniquely positioned for this. Target: $1.5–2M.",
         1750, "Q3 2025"),

        # 3. Alfred P. Sloan Foundation
        ("Alfred P. Sloan Foundation",
         "Sloan Foundation — STEM Fellows + Digital Infrastructure Expansion", "High",
         "Sloan has active fellowship pipelines at UVA (Physics FY 2023, Chemistry FY 2022) and "
         "co-funds the SDSS astronomy collaboration (FY 2021). Expand by nominating 2–3 additional "
         "early-career UVA faculty in CS, Statistics, and Environmental Science for Sloan Research "
         "Fellowships annually. Pair with a Sloan Digital Infrastructure proposal for UVA's data "
         "science computing cluster. UVA's STEM PhD diversity initiative is a natural co-anchor. "
         "Target: $500K–$1M incremental.",
         750, "Q1 2026"),

        # 4. Gordon & Betty Moore Foundation
        ("Gordon & Betty Moore Foundation",
         "Moore Foundation — Environmental Data Science Center at UVA", "High",
         "Moore funded UVA's Environmental Data Science Initiative (FY 2023) and Moore-Sloan Data "
         "Science Environments (FY 2022). Next ask: a Moore Data-Driven Environmental Science Center "
         "— a cross-school hub for AI-assisted ecosystem monitoring, climate modeling, and "
         "conservation policy anchored in UVA's College of Arts & Sciences and SEAS. Pitch as the "
         "mid-Atlantic node in Moore's university data science network. Target: $2–4M over 4 years.",
         3000, "Q2 2026"),

        # 5. Andrew W. Mellon Foundation
        ("Andrew W. Mellon Foundation",
         "Mellon Foundation — Public Humanities at UVA: Ph.D. Pathways + Digitization", "High",
         "Mellon's HIRE initiative and digital humanities grants are active at UVA "
         "(FY 2020–2023 across 4 awards). Next ask: a 'Public Humanities at UVA' campaign "
         "bundling two proposals: (1) a Mellon Humanities Ph.D. Pathways grant expanding "
         "alt-ac career prep for doctoral students via arts nonprofits, government, and public media; "
         "(2) a Mellon digitization award leveraging UVA's Special Collections rare books repository "
         "as a national digital humanities asset. Target: $2–3M.",
         2500, "Q3 2025"),

        # 6. Carnegie Corporation of New York
        ("Carnegie Corporation of New York",
         "Carnegie — Virginia Education Research Center (Curry-Led)", "Medium",
         "Carnegie's K-12 literacy reform and African higher ed priorities map directly onto "
         "Curry School's reading science and math achievement research (FY 2022–2023). Propose a "
         "Carnegie-funded Virginia Education Research Center: a Curry-led statewide hub evaluating "
         "evidence-based literacy and math interventions in high-need VA school districts, with "
         "findings exported to Carnegie's national K-12 network. Target: $1–1.5M over 3 years.",
         1250, "Q4 2025"),

        # 7. Lumina Foundation for Education
        ("Lumina Foundation for Education",
         "Lumina — First-Gen Completion + Credential Quality Research Initiative", "Medium",
         "Lumina's Goal 2025 (60% postsecondary credential attainment) directly supports UVA's "
         "first-generation access programs (FY 2022–2023 grants to Provost office and Curry). "
         "Propose a Lumina-backed Curry School research initiative studying credential quality "
         "and workforce alignment at public flagship universities — UVA as primary research site. "
         "CFR should broker introduction between Lumina program officers, UVA Provost, and Curry "
         "faculty. Target: $750K.",
         750, "Q2 2026"),

        # 8. William and Flora Hewlett Foundation
        ("William and Flora Hewlett Foundation",
         "Hewlett Foundation — Clean Energy Policy Lab + OER Hub", "High",
         "Hewlett's two priorities — open education resources (Curry, FY 2023) and clean energy "
         "policy (Batten, FY 2022) — both have active UVA anchors. Dual-track ask: (1) a Curry "
         "OER research + production center serving K-12 and higher ed across the mid-Atlantic; "
         "(2) a Batten School clean energy policy lab analyzing Virginia's energy transition under "
         "the Clean Economy Act. Bundle as 'UVA Knowledge for the Public Good.' Target: $1.5M.",
         1500, "Q1 2026"),

        # 9. W.M. Keck Foundation
        ("W.M. Keck Foundation",
         "Keck Foundation — High-Risk Neuroscience + Precision Medicine Program", "High",
         "Keck funds high-risk, high-reward university science — UVA School of Medicine's "
         "Alzheimer's biomarker (FY 2023) and genomics (FY 2021) awards confirm fit. "
         "Identify 2 UVA faculty doing genuinely paradigm-challenging research in neurodegeneration "
         "or precision oncology; submit targeted Keck Science Award nominations. Frame as a UVA "
         "multi-PI program with shared instrumentation (Keck does not fund individuals). "
         "Target: $1–2M.",
         1500, "Q3 2025"),

        # 10. David and Lucile Packard Foundation
        ("David and Lucile Packard Foundation",
         "Packard Foundation — Fellows Pipeline + Reproductive Health Research", "Medium",
         "Packard Fellows Program has recognized UVA ecology faculty (FY 2023 Conservation Science "
         "Fellowship, $875K/5yr). Nominate 2 more early-career UVA environmental science faculty "
         "for Packard Fellowships over the next 3 cycles. Simultaneously develop a Packard "
         "reproductive health proposal through UVA Health's OB/GYN + public health departments — "
         "aligning with Packard's family planning priorities (FY 2022 grant, $700K). "
         "CFR: request direct program officer meeting. Target: $1.5M+ total.",
         1750, "Q2 2026"),

        # 11. Ford Foundation
        ("Ford Foundation",
         "Ford Foundation — UVA Equity and Democracy Research Collaborative", "High",
         "Ford's inequality and democratic participation priorities overlap with UVA's Democracy "
         "Initiative, Equity Center, and UVA Law civil rights work (FY 2021–2023 across 3 awards). "
         "Propose a multi-school 'Equity and Democracy Research Collaborative' co-anchored by "
         "Batten, the Equity Center, and UVA Law — positioning UVA as Ford's premier public "
         "flagship partner for Southern U.S. equity work. Ford's $1B social bond signals "
         "multi-year institutional appetite. Target: $2–3M over 4 years.",
         2500, "Q1 2026"),

        # 12. Arnold Ventures
        ("Arnold Ventures",
         "Arnold Ventures — Virginia Evidence Lab (Batten + UVA Law)", "Medium",
         "Arnold Ventures funds only rigorously evidence-based policy research. UVA Law and "
         "Batten School have active Arnold grants on sentencing reform (FY 2023) and drug "
         "pricing (FY 2022). Expand by proposing a joint Batten-UVA Law 'Virginia Evidence Lab' "
         "— a standing Arnold policy evaluation partner producing rapid-turnaround, peer-reviewed "
         "analyses for Virginia and federal policymakers. Position as Arnold's mid-Atlantic "
         "policy hub. Target: $1.5M.",
         1500, "Q3 2026"),

        # 13. William Randolph Hearst Foundation
        ("William Randolph Hearst Foundation",
         "Hearst Foundation — Named Scholars Program (Journalism + Nursing)", "Low",
         "Hearst has two active giving streams at UVA: journalism awards via College of Arts & "
         "Sciences (FY 2023) and nursing scholarships via School of Nursing (FY 2022). Formalize "
         "into a named annual 'Hearst Scholars at UVA' program — 4 journalism awards + 4 nursing "
         "awards per year with Hearst Foundation branding. CFR should broker a personal meeting "
         "between the Hearst Foundation president and UVA deans of both schools. "
         "Modest but renewable. Target: $150K/yr.",
         300, "Q4 2025"),

        # 14. Henry Luce Foundation
        ("Henry Luce Foundation",
         "Luce Foundation — Scholars Pipeline + Theology & American Art Initiative", "Low",
         "Luce Scholars program placements at UVA are active (FY 2023 — Asia/U.S. relations). "
         "Strengthen by nominating 3–4 UVA undergraduates annually for Luce Scholarships "
         "(currently under-nominating). Separately, develop a Luce Theology and Arts grant "
         "proposal through UVA's Religious Studies + Art History departments — a natural fit "
         "for Luce's American art + religion niche. Target: $200–$350K across both programs.",
         275, "Q1 2026"),

        # 15. Claude Moore Charitable Foundation
        ("Claude Moore Charitable Foundation",
         "Claude Moore Foundation — Virginia Health Access Initiative", "Medium",
         "Claude Moore is a McLean, VA-based foundation deeply aligned with UVA Health and "
         "School of Medicine. Prior grants funded simulation lab equipment (FY 2023) and health "
         "access research (FY 2022). Propose a Claude Moore 'Virginia Health Access Initiative': "
         "3-year program embedding UVA medical students in underserved VA communities, paired "
         "with simulation lab expansion at the School of Medicine. Virginia-local roots make "
         "this a high-conversion relationship. Target: $500K–$750K.",
         625, "Q2 2025"),

        # 16. Anne Mullen Orell Charitable Trust
        ("Anne Mullen Orell Charitable Trust",
         "Anne Mullen Orell Trust — Stewardship + Community Health Renewal", "Low",
         "Small Virginia-based charitable trust with prior giving to UVA Health for community "
         "wellness (FY 2023, $50K). Recommend a light-touch stewardship strategy: personal "
         "outreach from UVA Health community benefit office, annual impact report, and a "
         "renewal ask of $50–75K for Charlottesville-region community health programming. "
         "Virginia proximity and mission alignment = high-conversion, low-effort relationship. "
         "Target: $75K renewable annually.",
         75, "Q3 2025"),
    ]

    for partner_name, title, priority, desc, est_k, timeline in fnd_recs:
        pid = pid_map.get(partner_name)
        session.add(Recommendation(
            partner_id=pid,
            title=title,
            category="Foundation",
            priority=priority,
            description=desc,
            est_value_k=float(est_k),
            timeline=timeline,
            status="Open",
        ))


def seed_funding_opportunities(session):
    """
    Sample funding opportunities from real CFR source lists:
      VPR Federal Digest (Lucy Carr Jones)  — federal opportunities from VPR's office
      Limited Submissions (Matt Dooley)     — LSOs managed by Matt Dooley
      CFR + School Research Directors       — opportunities from CFR and school-level directors
    """
    # Regular (non-LSO) opportunities
    # (title, sponsor, deadline, amt_min_k, amt_max_k, source, areas, eligibility, opp_type, status, desc, url, notes)
    regular_opps = [
        ("NSF Convergence Accelerator — Track J: Food & Energy Nexus",
         "NSF", "2025-09-12", 750, 5000,
         "VPR Federal Digest (Lucy Carr Jones)",
         "Energy, Environment, Food Systems",
         "Faculty", "Grant", "Active",
         "Supports convergence research teams tackling real-world challenges at the food-energy nexus. "
         "Phase 1 awards up to $750k; Phase 2 up to $5M. Teams must include non-academic partners.",
         "https://www.nsf.gov/convergence-accelerator", "Strong alignment with Dominion Energy + environmental policy work"),

        ("NIH R01 — Alzheimer's Disease & Related Dementias",
         "NIH/NIA", "2025-10-05", 250, 500,
         "VPR Federal Digest (Lucy Carr Jones)",
         "Health, Neuroscience, Aging",
         "Faculty", "Grant", "Active",
         "Standard R01 mechanism for basic and translational research on ADRD. "
         "Direct costs capped at $500k/yr. Requires UVA Health institutional sign-off.",
         "https://grants.nih.gov", "Aligned with Eli Lilly Alzheimer's research notes; tag to UVA Health"),

        ("DARPA Young Faculty Award (YFA) — Open Broad Agency Announcement",
         "DARPA", "2025-08-30", 500, 1000,
         "VPR Federal Digest (Lucy Carr Jones)",
         "Defense, AI, Engineering, Cybersecurity",
         "Faculty", "Grant", "Closing Soon",
         "Identifies and engages rising stars in junior faculty positions who are likely to make "
         "significant contributions to national security science and engineering. "
         "Awards up to $1M over 2 years.",
         "https://www.darpa.mil/work-with-us/young-faculty-award", "Great match for SEAS faculty; deadline in 6 weeks"),

        ("DOE Office of Science — Basic Energy Sciences Early Career Award",
         "Dept. of Energy", "2025-09-26", 750, 750,
         "VPR Federal Digest (Lucy Carr Jones)",
         "Energy, Materials Science, Chemistry, Physics",
         "Faculty", "Grant", "Closing Soon",
         "Awards up to $750k over 5 years to early-career researchers at universities. "
         "Focus on fundamental research in chemical sciences, geosciences, and energy biosciences.",
         "https://science.osti.gov/early-career", "Priority for SEAS and A&S faculty in first 10 years of appointment"),

        ("Robert Wood Johnson Foundation — Health Equity Research",
         "RWJF", "2025-10-30", 500, 2000,
         "VPR Federal Digest (Lucy Carr Jones)",
         "Health, Health Equity, Social Sciences, Policy",
         "Faculty", "Grant", "Active",
         "Supports research that advances health equity and addresses systemic barriers to health. "
         "Priority given to community-partnered research with measurable policy impact.",
         "https://www.rwjf.org", "Cross-listed: also flagged by CFR + School Directors — deduplicated here"),

        ("NSF CAREER Award — Faculty Early Career Development Program",
         "NSF", "2026-02-20", 400, 600,
         "VPR Federal Digest (Lucy Carr Jones)",
         "All STEM fields",
         "Faculty", "Grant", "Active",
         "NSF's most prestigious award for early-career faculty. Supports research and education "
         "activities in all NSF-supported disciplines. Must be in first 7 years of tenure-track appointment.",
         "https://www.nsf.gov/career", "Perennial — remind RAs to track eligible faculty cohort each cycle"),

        ("Commonwealth of Virginia — Innovation Commercialization Grant",
         "VA CEED / VEDP", "2025-10-10", 50, 500,
         "VPR Federal Digest (Lucy Carr Jones)",
         "Commercialization, Entrepreneurship, Technology Transfer",
         "Faculty", "Grant", "Active",
         "Supports faculty-led technology commercialization with Virginia economic development impact. "
         "Requires industry co-sponsorship letter. Preference for companies in Virginia.",
         "https://www.vedp.org", "Dominion Energy and Capital One could serve as co-sponsors; flag to CFR"),

        ("Wellcome Trust — Mental Health Research Priority Program",
         "Wellcome Trust", "2026-01-15", 500, 5000,
         "VPR Federal Digest (Lucy Carr Jones)",
         "Health, Mental Health, Neuroscience, Global Health",
         "Faculty", "Grant", "Active",
         "Supports ambitious programmes that will transform understanding of mental health conditions "
         "and develop new approaches to prevention and treatment. International collaborations welcome.",
         "https://wellcome.org/grant-funding", "High value — flag to UVA Health, Psychiatry dept"),

        ("Siemens Foundation — STEM Education Research Grant",
         "Siemens Foundation", "2025-11-01", 100, 300,
         "CFR + School Research Directors",
         "Education, STEM, Workforce",
         "Faculty", "Grant", "Active",
         "Supports applied research on STEM education pipeline, workforce development, "
         "and diversity in engineering fields. Priority given to proposals with industry co-investigators.",
         "https://www.siemens-foundation.org", "Direct tie to Siemens corporate partner; flag for CFR relationship manager"),

        ("Google Research Scholar Program",
         "Google", "2025-10-15", 60, 60,
         "CFR + School Research Directors",
         "AI, Machine Learning, Computer Science, Data",
         "Faculty", "Grant", "Active",
         "Unrestricted gifts to support early-career faculty pursuing research in CS and related fields. "
         "$60k award, no deliverables. Nomination via Google Research website.",
         "https://research.google/programs/research-scholar-program/",
         "Flag for faculty working with Google partners; CFR can facilitate intro"),

        ("Microsoft Research Outreach — Azure for Research Credits",
         "Microsoft", "2025-12-31", 20, 150,
         "CFR + School Research Directors",
         "AI, Cloud Computing, Data Science, Health",
         "Faculty", "Grant", "Active",
         "Provides Azure compute credits and technical support for research projects. "
         "Not a cash award — compute credits ranging from $20k to $150k equivalent. "
         "Rolling applications reviewed quarterly.",
         "https://www.microsoft.com/en-us/research/academic-program/microsoft-azure-for-research/",
         "Microsoft is an active partner — CFR can warm intro"),

        ("AFRL University Research Initiative — Autonomy & Human-Machine Teaming",
         "Air Force Research Lab", "2025-11-15", 300, 2000,
         "CFR + School Research Directors",
         "Defense, AI, Autonomy, Engineering",
         "Faculty", "Contract", "Active",
         "Seeking proposals on autonomous systems research and human-machine teaming. "
         "Multi-year contracts ranging from $300k to $2M. Requires DoD security considerations.",
         "https://www.afrl.af.mil", "Aligns with Raytheon, Lockheed, Northrop Grumman partners; tag for defense-adjacent faculty"),

        ("Capital One Spark for Good — Data Science for Social Impact",
         "Capital One", "2025-09-01", 50, 200,
         "CFR + School Research Directors",
         "Data Science, Finance, Social Impact, AI",
         "Faculty", "Grant", "Closing Soon",
         "Supports university-based data science research with measurable social impact. "
         "Capital One McLean HQ is a natural partner. Proposals should include internship component.",
         "https://www.capitalone.com/tech/machine-learning/",
         "Active Capital One corporate relationship — CFR intro available; deadline in <30 days"),

        ("Pfizer Medical Research Grant Program",
         "Pfizer", "2025-12-15", 100, 500,
         "CFR + School Research Directors",
         "Health, Pharma, Clinical Research, Oncology",
         "Faculty", "Grant", "Active",
         "Supports investigator-initiated research in areas aligned with Pfizer therapeutic priorities: "
         "oncology, rare disease, cardiovascular, immunology. No indirect costs taken.",
         "https://www.pfizer.com/science/research/grants",
         "Pfizer is an active CFR partner — relationship manager should flag to UVA Health faculty"),

        ("Raytheon University Research Program — Quantum & Photonics",
         "Raytheon", "2025-11-30", 200, 800,
         "CFR + School Research Directors",
         "Defense, Quantum Computing, Physics, Engineering",
         "Faculty", "Contract", "Active",
         "Raytheon Technologies Research Center funding for university partners in quantum sensing, "
         "quantum communications, and photonic systems. Proprietary research with IP negotiation.",
         "https://www.rtx.com/raytheon/what-we-do/technology/university-research",
         "Raytheon is active CFR partner — CFR relationship manager can facilitate direct intro to RTRC"),
    ]

    for o in regular_opps:
        (title, sponsor, deadline, amt_min, amt_max, source, areas,
         eligibility, opp_type, status, desc, url, notes) = o
        session.add(FundingOpportunity(
            title=title, sponsor=sponsor, deadline=deadline,
            amount_min_k=float(amt_min), amount_max_k=float(amt_max),
            source=source, research_areas=areas, eligibility=eligibility,
            opp_type=opp_type, status=status, description=desc,
            url=url, notes=notes, added_by="CFR Seed Data",
            date_added="2025-07-01",
            is_lso=False,
        ))

    # LSO — Limited Submission Opportunities (managed by Matt Dooley)
    lso_opps = [
        # (title, sponsor, deadline, amt_min_k, amt_max_k, areas, eligibility, status, desc, url, notes,
        #  lso_slots, lso_internal_deadline, lso_internal_status, lso_nominees)
        ("NSF Major Research Instrumentation (MRI) — Track 1",
         "NSF", "2026-01-15", 400, 1600,
         "Infrastructure, Engineering, Physical Sciences, Neuroscience",
         "Faculty", "Active",
         "Supports acquisition or development of multi-user research instrumentation critical to the "
         "advancement of science and engineering. Track 1: up to $1.6M. UVA limited to 3 proposals "
         "institution-wide (max 2 from SEAS).",
         "https://www.nsf.gov/mri",
         "Internal competition open — contact Matt Dooley to submit intent by internal deadline",
         3, "2025-11-01", "Open", ""),

        ("NIH S10 — Shared Instrumentation Grant",
         "NIH/ORIP", "2025-11-05", 500, 2000,
         "Health, Biomedical Research, Instrumentation",
         "Faculty", "Active",
         "Supports purchase of commercially available, state-of-the-art instruments to be shared by "
         "NIH-supported investigators. UVA may submit 1 application. Award range $500k–$2M. "
         "Requires endorsement from Department Chair and Dean.",
         "https://grants.nih.gov/grants/guide/pa-files/PAR-23-177.html",
         "UVA slot: 1 — internal review underway; nominees identified",
         1, "2025-09-15", "In Review", "Dr. Sarah Chen (Neuroscience), Dr. Mark Torres (Biomedical Eng)"),

        ("Simons Foundation — Investigators in Mathematical Modeling of Living Systems",
         "Simons Foundation", "2026-03-01", 500, 500,
         "Mathematics, Biology, Computational Biology, Physics",
         "Faculty", "Active",
         "Five-year, $100k/yr awards to mid-career faculty doing exceptional research at the interface "
         "of mathematics and living systems. UVA limited to 2 nominations. Highly competitive nationally.",
         "https://www.simonsfoundation.org/grant/simons-investigators/",
         "UVA nominations must go through VPR office — coordinate with Matt Dooley and Lucy Carr Jones",
         2, "2025-12-01", "Open", ""),
    ]

    for o in lso_opps:
        (title, sponsor, deadline, amt_min, amt_max, areas, eligibility, status,
         desc, url, notes, slots, int_deadline, int_status, nominees) = o
        session.add(FundingOpportunity(
            title=title, sponsor=sponsor, deadline=deadline,
            amount_min_k=float(amt_min), amount_max_k=float(amt_max),
            source="Limited Submissions (Matt Dooley)",
            research_areas=areas, eligibility=eligibility,
            opp_type="LSO", status=status, description=desc,
            url=url, notes=notes, added_by="CFR Seed Data",
            date_added="2025-07-01",
            is_lso=True, lso_slots=slots,
            lso_internal_deadline=int_deadline,
            lso_internal_status=int_status,
            lso_nominees=nominees,
        ))


def seed_foundation_grants(session):
    """
    Grant-level funding history for foundation partners.
    partner_name is resolved to partner_id at seed time.
    grant_type: "UVA Received" = actual UVA grant; "National Context" = national giving reference.
    amount_k in $k (e.g. 500 = $500,000).
    """
    # Build name→id map
    partners = {p.name: p.id for p in session.query(Partner).filter_by(partner_type="Foundation")}

    grants = [
        # (partner_name, fiscal_year, amount_k, grant_title, program_area, recipient_school, grant_type, notes)

        # ── Bill & Melinda Gates Foundation ───────────────────────────────────
        ("Bill & Melinda Gates Foundation", 2023, 7000000,
         "Gates Grand Challenges Explorations — Global Health", "Global Health", None,
         "National Context", "$7B+ annual giving; flagship programs: GAVI, malaria eradication, reproductive health"),

        # ── Robert Wood Johnson Foundation ────────────────────────────────────
        ("Robert Wood Johnson Foundation", 2023, 450000,
         "Culture of Health / National Programs", "Health Equity", None,
         "National Context", "~$450M annual giving focused on U.S. health equity and nursing workforce"),

        # ── Alfred P. Sloan Foundation ────────────────────────────────────────
        ("Alfred P. Sloan Foundation", 2023, 90000,
         "Sloan Annual Programs — STEM + Technology", "STEM Research", None,
         "National Context", "~$90M annual giving; Sloan Research Fellowships, energy/environment, digital information"),

        # ── Gordon & Betty Moore Foundation ───────────────────────────────────
        ("Gordon & Betty Moore Foundation", 2023, 300000,
         "Conservation + Science + Patient Care — National", "Environmental Science", None,
         "National Context", "~$300M annual giving; ocean conservation, science, patient-centered care"),

        # ── Andrew W. Mellon Foundation ────────────────────────────────────────
        ("Andrew W. Mellon Foundation", 2023, 310000,
         "Mellon Annual Giving — Arts & Humanities", "Arts & Humanities", None,
         "National Context", "~$310M annual giving; HIRE initiative, HBCU support, performing arts, higher ed diversity"),

        # ── Ford Foundation ────────────────────────────────────────────────────
        ("Ford Foundation", 2023, 650000,
         "Ford Annual Giving — Inequality & Democracy", "Social Justice", None,
         "National Context", "~$650M annual giving; inequality, democratic participation, economic opportunity"),

        # ── Carnegie Corporation of New York ───────────────────────────────────
        ("Carnegie Corporation of New York", 2023, 165000,
         "Carnegie Annual Giving — Education + Civic", "Education", None,
         "National Context", "~$165M annual giving; K-12 reform, civic integration of immigrants, science education"),
    ]

    for g in grants:
        (partner_name, fiscal_year, amount_k, grant_title,
         program_area, recipient_school, grant_type, notes) = g
        pid = partners.get(partner_name)
        if pid is None:
            continue
        session.add(FoundationGrant(
            partner_id=pid,
            fiscal_year=fiscal_year,
            amount_k=float(amount_k),
            grant_title=grant_title,
            program_area=program_area,
            recipient_school=recipient_school,
            grant_type=grant_type,
            notes=notes,
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
        seed_funding_opportunities(session)
        session.flush()  # assign partner IDs before FK-dependent seeding
        seed_foundation_grants(session)
        seed_foundation_recommendations(session)
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
