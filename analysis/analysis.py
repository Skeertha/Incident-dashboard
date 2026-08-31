"""
analysis.py
-----------
Reads incidents.csv, computes all KPIs shown on the Incident Troubleshooting
Dashboard (mirrors the logic in sql/analysis_queries.sql), and writes a single
dashboard_data.json consumed by dashboard/dashboard.html.

Run:  python3 analysis.py
"""

import json
import pandas as pd
import numpy as np

PRIORITY_ORDER = ["P1 - Critical", "P2 - High", "P3 - Medium", "P4 - Low"]
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_data(path="../data/incidents.csv"):
    df = pd.read_csv(path, parse_dates=["created_date", "resolved_date"])
    df["sla_breached"] = df["sla_breached"].map({True: True, False: False, "True": True, "False": False})
    df["change_related"] = df["change_related"].astype(bool)
    df["csat_score"] = pd.to_numeric(df["csat_score"], errors="coerce")
    df["resolution_time_hours"] = pd.to_numeric(df["resolution_time_hours"], errors="coerce")
    return df


def kpi_summary(df):
    total = len(df)
    resolved_mask = df["resolution_time_hours"].notna()
    open_mask = df["status"].isin(["Open", "In Progress"])
    sla_rated = df["sla_breached"].notna()

    return {
        "total_tickets": int(total),
        "open_tickets": int(open_mask.sum()),
        "resolved_tickets": int(resolved_mask.sum()),
        "reopened_tickets": int((df["reopened_count"] == 1).sum()),
        "avg_mttr_hours": round(df.loc[resolved_mask, "resolution_time_hours"].mean(), 2),
        "sla_compliance_pct": round(100 * (df.loc[sla_rated, "sla_breached"] == False).sum() / sla_rated.sum(), 2),
        "avg_first_response_min": round(df["first_response_minutes"].mean(), 1),
        "avg_csat": round(df["csat_score"].mean(), 2),
        "critical_open": int(((df["priority"] == "P1 - Critical") & open_mask).sum()),
        "change_related_pct": round(100 * df["change_related"].sum() / total, 2),
    }


def monthly_trend(df):
    df = df.copy()
    df["month"] = df["created_date"].dt.strftime("%Y-%m")
    created = df.groupby("month").size()
    resolved = df.dropna(subset=["resolved_date"]).copy()
    resolved["resolved_month"] = resolved["resolved_date"].dt.strftime("%Y-%m")
    resolved_counts = resolved.groupby("resolved_month").size()
    months = sorted(set(created.index) | set(resolved_counts.index))
    return {
        "months": months,
        "created": [int(created.get(m, 0)) for m in months],
        "resolved": [int(resolved_counts.get(m, 0)) for m in months],
    }


def mttr_by_priority(df):
    g = df.dropna(subset=["resolution_time_hours"]).groupby("priority")["resolution_time_hours"].mean()
    return {"priorities": PRIORITY_ORDER, "avg_hours": [round(g.get(p, 0), 2) for p in PRIORITY_ORDER]}


def sla_by_priority(df):
    rated = df.dropna(subset=["sla_breached"])
    out = []
    for p in PRIORITY_ORDER:
        sub = rated[rated["priority"] == p]
        if len(sub) == 0:
            out.append(0)
        else:
            out.append(round(100 * (sub["sla_breached"] == False).sum() / len(sub), 2))
    return {"priorities": PRIORITY_ORDER, "compliance_pct": out}


def sla_by_team(df):
    rated = df.dropna(subset=["sla_breached"])
    g = rated.groupby("assigned_team").agg(
        total=("ticket_id", "count"),
        compliant=("sla_breached", lambda s: (s == False).sum()),
        avg_res=("resolution_time_hours", "mean"),
    )
    g["compliance_pct"] = round(100 * g["compliant"] / g["total"], 2)
    g = g.sort_values("compliance_pct")
    return {
        "teams": g.index.tolist(),
        "compliance_pct": [round(v, 2) for v in g["compliance_pct"]],
        "avg_resolution_hours": [round(v, 2) for v in g["avg_res"]],
        "ticket_count": [int(v) for v in g["total"]],
    }


def category_breakdown(df):
    g = df["category"].value_counts()
    return {"categories": g.index.tolist(), "counts": [int(v) for v in g.values]}


def application_breakdown(df):
    g = df.groupby("application_name").agg(
        total=("ticket_id", "count"),
        critical=("priority", lambda s: (s == "P1 - Critical").sum()),
    ).sort_values("total", ascending=False)
    return {
        "applications": g.index.tolist(),
        "counts": [int(v) for v in g["total"]],
        "critical_counts": [int(v) for v in g["critical"]],
    }


def root_cause_breakdown(df):
    g = df["root_cause"].dropna()
    g = g[g != ""].value_counts()
    return {"causes": g.index.tolist(), "counts": [int(v) for v in g.values]}


def reopen_rate(df):
    closed = df[df["status"].isin(["Resolved", "Closed", "Reopened"])]
    return round(100 * closed["reopened_count"].sum() / len(closed), 2)


def first_response_by_priority(df):
    g = df.groupby("priority")["first_response_minutes"].mean()
    return {"priorities": PRIORITY_ORDER, "avg_minutes": [round(g.get(p, 0), 1) for p in PRIORITY_ORDER]}


def csat_by_team(df):
    rated = df.dropna(subset=["csat_score"])
    g = rated.groupby("assigned_team")["csat_score"].mean().sort_values(ascending=False)
    return {"teams": g.index.tolist(), "avg_csat": [round(v, 2) for v in g.values]}


def demand_heatmap(df):
    d = df.copy()
    d["day_of_week"] = d["created_date"].dt.day_name()
    d["hour_of_day"] = d["created_date"].dt.hour
    pivot = d.pivot_table(index="day_of_week", columns="hour_of_day", values="ticket_id", aggfunc="count", fill_value=0)
    pivot = pivot.reindex(DAY_ORDER)
    hours = list(range(24))
    matrix = [[int(pivot.loc[day, h]) if h in pivot.columns else 0 for h in hours] for day in DAY_ORDER]
    return {"days": DAY_ORDER, "hours": hours, "matrix": matrix}


def engineer_performance(df):
    g = df.dropna(subset=["resolution_time_hours"]).groupby("assigned_engineer").agg(
        handled=("ticket_id", "count"),
        avg_res=("resolution_time_hours", "mean"),
    )
    rated = df.dropna(subset=["sla_breached"])
    sla = rated.groupby("assigned_engineer").apply(lambda s: round(100 * (s["sla_breached"] == False).sum() / len(s), 2))
    g["sla_pct"] = sla
    g = g.sort_values("handled", ascending=False)
    return {
        "engineers": g.index.tolist(),
        "handled": [int(v) for v in g["handled"]],
        "avg_resolution_hours": [round(v, 2) for v in g["avg_res"]],
        "sla_compliance_pct": [round(v, 2) if not pd.isna(v) else 0 for v in g["sla_pct"]],
    }


def priority_distribution(df):
    g = df["priority"].value_counts()
    return {"priorities": PRIORITY_ORDER, "counts": [int(g.get(p, 0)) for p in PRIORITY_ORDER]}


def open_breach_risk(df):
    open_df = df[df["status"].isin(["Open", "In Progress"])].copy()
    now = df["created_date"].max()  # use latest data timestamp as "now" for reproducibility
    open_df["hours_open"] = (now - open_df["created_date"]).dt.total_seconds() / 3600
    open_df["at_risk"] = open_df["hours_open"] > open_df["sla_target_hours"]
    open_df = open_df.sort_values("hours_open", ascending=False).head(15)
    return open_df[["ticket_id", "priority", "application_name", "assigned_team", "hours_open", "at_risk"]].assign(
        hours_open=lambda d: d["hours_open"].round(1)
    ).to_dict(orient="records")


def raw_records(df):
    """Trimmed ticket-level records so the dashboard can filter/aggregate client-side."""
    cols = ["ticket_id", "created_date", "resolved_date", "category", "application_name",
            "priority", "status", "assigned_team", "assigned_engineer", "root_cause",
            "resolution_time_hours", "sla_breached", "csat_score", "reopened_count", "change_related"]
    out = df[cols].copy()
    out["created_date"] = out["created_date"].dt.strftime("%Y-%m-%d %H:%M")
    out["resolved_date"] = out["resolved_date"].dt.strftime("%Y-%m-%d %H:%M")
    out = out.where(pd.notnull(out), None)
    return out.to_dict(orient="records")


def main():
    df = load_data()

    dashboard_data = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "data_range": {
            "start": df["created_date"].min().strftime("%Y-%m-%d"),
            "end": df["created_date"].max().strftime("%Y-%m-%d"),
        },
        "kpi_summary": kpi_summary(df),
        "monthly_trend": monthly_trend(df),
        "mttr_by_priority": mttr_by_priority(df),
        "sla_by_priority": sla_by_priority(df),
        "sla_by_team": sla_by_team(df),
        "category_breakdown": category_breakdown(df),
        "application_breakdown": application_breakdown(df),
        "root_cause_breakdown": root_cause_breakdown(df),
        "reopen_rate_pct": reopen_rate(df),
        "first_response_by_priority": first_response_by_priority(df),
        "csat_by_team": csat_by_team(df),
        "demand_heatmap": demand_heatmap(df),
        "engineer_performance": engineer_performance(df),
        "priority_distribution": priority_distribution(df),
        "open_breach_risk": open_breach_risk(df),
        "raw_records": raw_records(df),
    }

    with open("dashboard_data.json", "w") as f:
        json.dump(dashboard_data, f, indent=2, default=str)

    print("KPI Summary:")
    for k, v in dashboard_data["kpi_summary"].items():
        print(f"  {k}: {v}")
    print("\nWrote dashboard_data.json")


if __name__ == "__main__":
    main()
