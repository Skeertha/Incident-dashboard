# Incident Console — Application Support & Incident Troubleshooting Dashboard

A portfolio project simulating an end-to-end IT Application Support workflow: incident
data generation, SQL-based analysis, Python/pandas KPI computation, and an interactive
web dashboard — the kind of tooling used for **incident, problem, and change management**
in a Support Engineer / Technical Solution Analyst / Application Support role.

## What it demonstrates

| Skill area | Where |
|---|---|
| SQL (schema design, aggregation, KPI queries) | `sql/schema.sql`, `sql/analysis_queries.sql` |
| Python / pandas data analysis | `analysis/analysis.py` |
| Incident/ticket data modeling | `data/generate_data.py` |
| Front-end data visualization & interactivity (Chart.js, vanilla JS) | `dashboard/dashboard.html` |
| ITSM domain knowledge | SLA targets, priority tiers, root-cause taxonomy, change linkage throughout |

## Project structure

```
incident-dashboard/
├── data/
│   ├── generate_data.py      # generates the synthetic ticket dataset
│   └── incidents.csv         # 2,200 tickets across 12 months (output)
├── sql/
│   ├── schema.sql            # incidents + change_requests tables, indexes
│   └── analysis_queries.sql  # 16 queries: MTTR, SLA %, heatmap, leaderboard, etc.
├── analysis/
│   ├── analysis.py           # pandas KPI computation -> dashboard_data.json
│   └── dashboard_data.json   # computed KPIs consumed by the dashboard (output)
├── dashboard/
│   └── dashboard.html        # standalone interactive dashboard (open in any browser)
└── README.md
```

## The dataset

`incidents.csv` simulates 12 months (Sep 2025–Aug 2026) of tickets from a typical ITSM
tool (ServiceNow / ManageEngine / Jira Service Management style), with:

- **Priority tiers** — P1 Critical → P4 Low, each with a distinct SLA target (4h / 8h / 24h / 72h)
- **10 incident categories** (Database, Network, Batch Job Failure, Security, etc.) each
  with realistic subcategories
- **10 applications** (Core Banking App, Payment Gateway, Auth Service, etc.)
- **6 support teams** (L1/L2/L3, DBA, Network, App Dev) with category-appropriate routing
- Resolution time, first-response time, SLA breach flag, reopen count, CSAT score (1–5),
  root cause, and change-request linkage

Priority mix, SLA breach rates, and CSAT are deliberately correlated (e.g. breached SLAs
and reopened tickets pull CSAT down) so the KPIs tell a coherent, realistic story rather
than being pure noise.

> This is synthetic data generated for demonstration purposes — it does not represent any
> real organization's tickets.

## Running it yourself

```bash
# 1. Generate the dataset
cd data && python3 generate_data.py

# 2. Compute KPIs (requires pandas, numpy)
cd ../analysis && python3 analysis.py

# 3. Open the dashboard
#    dashboard.html already ships with data embedded, so you can open it directly.
#    To refresh it with newly generated data, replace the JSON inside the
#    <script id="dashboard-data" type="application/json"> block with the contents
#    of analysis/dashboard_data.json (raw_records field included).
open ../dashboard/dashboard.html   # or double-click it
```

No server or build step is required — `dashboard.html` is a single self-contained file.

## Dashboard features

- **Live filters** — priority, team, category, and application; every KPI, chart, table,
  and the risk list recompute instantly in the browser (no server round-trip)
- **KPI strip** — ticket volume, SLA compliance %, MTTR, avg. first response time, CSAT, reopen rate
- **Monthly trend** — created vs. resolved tickets over time
- **SLA compliance & MTTR by priority** — where breaches concentrate
- **Category volume & root-cause mix** — what's driving ticket load
- **Team performance table** — sortable by ticket count, SLA %, MTTR, CSAT
- **Demand heatmap** — ticket creation by day-of-week × hour, useful for shift/on-call staffing decisions
- **Engineer workload leaderboard**
- **Open & at-risk tickets** — currently unresolved tickets nearing or past SLA

## Design notes

The visual language (dark console background, monospace figures, hairline borders, status
pills) is intentionally modeled on real NOC/monitoring consoles rather than a generic
SaaS dashboard — the audience for this tool is an on-call support engineer, not an
executive reading a slide.

## Possible extensions

- Swap `incidents.csv` for a real export from your ITSM tool (ServiceNow, Freshservice,
  Jira Service Management) — the schema and queries map directly to typical ticket fields
- Load into a real database (`schema.sql` runs as-is on MySQL/PostgreSQL) and point a BI
  tool (Power BI / Tableau) at it for a second reporting layer
- Add a "problem management" table linking recurring incidents to a parent problem record
- Add authentication + a lightweight backend (Flask/FastAPI) to serve live ticket data
  instead of a static snapshot
