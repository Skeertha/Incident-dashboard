"""
generate_data.py
-----------------
Generates a realistic, synthetic IT Application Support incident dataset
for the "Application Support & Incident Troubleshooting Dashboard" project.

This simulates 12 months of ticket data from an ITSM tool (e.g. ServiceNow /
ManageEngine / Jira Service Management) covering incident creation, triage,
routing, resolution, SLA tracking, root cause, and change linkage.

Output: ../data/incidents.csv  (~2,200 rows)

Run:  python3 generate_data.py
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

# ---------------------------------------------------------------------------
# Reference / lookup data
# ---------------------------------------------------------------------------

APPLICATIONS = [
    "Core Banking App", "Payment Gateway", "CRM Portal", "Order Management System",
    "HR Portal", "Reporting Dashboard", "Auth Service", "Inventory System",
    "Customer Support Portal", "Billing Engine",
]

CATEGORY_SUBCATEGORY = {
    "Application Issue": ["UI Error", "Application Crash", "Feature Not Working", "Data Mismatch"],
    "Database": ["Query Timeout", "Deadlock", "Connection Pool Exhausted", "Data Corruption"],
    "Network": ["VPN Failure", "Latency", "DNS Issue", "Firewall Block"],
    "Server/Infra": ["Disk Space Full", "CPU Spike", "Server Down", "Memory Leak"],
    "Access/Authentication": ["Login Failure", "Password Reset", "SSO Error", "Permission Denied"],
    "Batch Job Failure": ["Job Timeout", "Job Failed - Data Error", "Job Not Triggered", "Duplicate Run"],
    "Performance": ["Slow Response Time", "Report Load Timeout", "API Latency", "Page Load Delay"],
    "Integration/API": ["API Failure", "Webhook Not Firing", "Third-Party Timeout", "Payload Mismatch"],
    "Hardware": ["Printer Issue", "Workstation Failure", "Peripheral Not Detected", "Device Offline"],
    "Security": ["Suspicious Login", "Certificate Expiry", "Vulnerability Alert", "Unauthorized Access Attempt"],
}
CATEGORIES = list(CATEGORY_SUBCATEGORY.keys())

PRIORITY_WEIGHTS = {
    "P1 - Critical": 0.06,
    "P2 - High": 0.22,
    "P3 - Medium": 0.47,
    "P4 - Low": 0.25,
}

# SLA resolution target (business hours converted to wall-clock hours for simplicity)
SLA_TARGET_HOURS = {
    "P1 - Critical": 4,
    "P2 - High": 8,
    "P3 - Medium": 24,
    "P4 - Low": 72,
}

TEAMS = ["L1 Support", "L2 Support", "L3 Engineering", "DBA Team", "Network Team", "App Dev Team"]

TEAM_BY_CATEGORY = {
    "Application Issue": ["L2 Support", "App Dev Team"],
    "Database": ["DBA Team", "L3 Engineering"],
    "Network": ["Network Team", "L2 Support"],
    "Server/Infra": ["L3 Engineering", "Network Team"],
    "Access/Authentication": ["L1 Support", "L2 Support"],
    "Batch Job Failure": ["App Dev Team", "L3 Engineering"],
    "Performance": ["L3 Engineering", "DBA Team"],
    "Integration/API": ["App Dev Team", "L3 Engineering"],
    "Hardware": ["L1 Support"],
    "Security": ["Network Team", "L3 Engineering"],
}

ENGINEERS = [
    "A. Rangan", "S. Priya", "M. Kumar", "K. Suresh", "R. Iyer", "T. Divya",
    "V. Prasad", "N. Fathima", "J. Antony", "B. Meena", "P. Arjun", "L. Chitra",
]

ROOT_CAUSES = [
    "Code Defect", "Configuration Error", "Infra Failure", "Data Issue",
    "User Error", "Third-Party Outage", "Capacity/Performance", "Unknown",
]

REPORTED_BY = ["End User", "Monitoring Alert", "Batch Job Monitor", "Customer", "Support Team (Proactive)"]

STATUS_POOL_CLOSED = ["Resolved", "Closed"]

RESOLUTION_NOTE_TEMPLATES = {
    "Application Issue": "Identified faulty code path; deployed hotfix / config change and validated with user.",
    "Database": "Optimized query / cleared lock and restarted affected session; verified data integrity.",
    "Network": "Restarted network service / re-routed traffic; confirmed connectivity restored.",
    "Server/Infra": "Freed disk space / restarted service; added monitoring alert to prevent recurrence.",
    "Access/Authentication": "Reset credentials / corrected access role; user confirmed successful login.",
    "Batch Job Failure": "Re-triggered job after correcting input file; added validation check.",
    "Performance": "Tuned query/index or scaled resources; response time back within threshold.",
    "Integration/API": "Coordinated with third-party vendor / corrected payload mapping; retested integration.",
    "Hardware": "Replaced/reset device; confirmed functioning with end user.",
    "Security": "Investigated alert, confirmed false positive / revoked access; updated certificate.",
}

START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2026, 8, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

N_TICKETS = 2200


def weighted_choice(weights_dict):
    keys = list(weights_dict.keys())
    weights = list(weights_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]


def random_datetime_in_range():
    day_offset = random.randint(0, TOTAL_DAYS)
    base_day = START_DATE + timedelta(days=day_offset)
    # Bias incident creation towards business hours (9am-9pm) with some off-hour noise
    if random.random() < 0.8:
        hour = random.randint(9, 21)
    else:
        hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    return base_day.replace(hour=hour, minute=minute, second=0)


def generate_ticket(ticket_num):
    ticket_id = f"INC{100000 + ticket_num}"
    created_dt = random_datetime_in_range()
    category = random.choice(CATEGORIES)
    subcategory = random.choice(CATEGORY_SUBCATEGORY[category])
    priority = weighted_choice(PRIORITY_WEIGHTS)
    sla_target = SLA_TARGET_HOURS[priority]
    application = random.choice(APPLICATIONS)
    team = random.choice(TEAM_BY_CATEGORY[category])
    engineer = random.choice(ENGINEERS)
    reported_by = random.choice(REPORTED_BY)
    root_cause = random.choice(ROOT_CAUSES)

    # First response time (minutes) - generally faster for higher priority
    base_response = {"P1 - Critical": 12, "P2 - High": 25, "P3 - Medium": 60, "P4 - Low": 180}[priority]
    first_response_minutes = max(2, int(random.gauss(base_response, base_response * 0.4)))

    # Determine whether ticket is still open (mostly recent tickets) or resolved
    days_since_created = (END_DATE - created_dt).days
    is_open = days_since_created < 2 and random.random() < 0.5

    # Resolution time: sample around SLA target with some breaches
    breach_chance = {"P1 - Critical": 0.18, "P2 - High": 0.15, "P3 - Medium": 0.12, "P4 - Low": 0.08}[priority]
    if random.random() < breach_chance:
        resolution_hours = sla_target * random.uniform(1.2, 3.5)
        sla_breached = True
    else:
        resolution_hours = sla_target * random.uniform(0.15, 0.95)
        sla_breached = False

    resolution_hours = round(resolution_hours, 2)

    if is_open:
        status = random.choice(["Open", "In Progress"])
        resolved_dt = None
        resolution_hours_val = ""
        sla_breached_val = ""
        csat = ""
        reopened_count = 0
    else:
        resolved_dt = created_dt + timedelta(hours=resolution_hours)
        status = random.choices(STATUS_POOL_CLOSED + ["Reopened"], weights=[0.72, 0.20, 0.08])[0]
        reopened_count = 1 if status == "Reopened" else 0
        resolution_hours_val = resolution_hours
        sla_breached_val = sla_breached
        # CSAT tends lower when SLA breached or reopened
        if sla_breached or reopened_count:
            csat = random.choices([1, 2, 3, 4, 5], weights=[15, 25, 30, 20, 10])[0]
        else:
            csat = random.choices([1, 2, 3, 4, 5], weights=[2, 5, 18, 40, 35])[0]

    change_related = random.random() < 0.14  # ~14% of incidents tie back to a recent change
    resolution_notes = RESOLUTION_NOTE_TEMPLATES[category] if not is_open else ""

    return {
        "ticket_id": ticket_id,
        "created_date": created_dt.strftime("%Y-%m-%d %H:%M"),
        "resolved_date": resolved_dt.strftime("%Y-%m-%d %H:%M") if resolved_dt else "",
        "category": category,
        "subcategory": subcategory,
        "application_name": application,
        "priority": priority,
        "status": status,
        "assigned_team": team,
        "assigned_engineer": engineer,
        "reported_by": reported_by,
        "root_cause": root_cause if not is_open else "",
        "sla_target_hours": sla_target,
        "first_response_minutes": first_response_minutes,
        "resolution_time_hours": resolution_hours_val,
        "sla_breached": sla_breached_val,
        "reopened_count": reopened_count,
        "change_related": change_related,
        "csat_score": csat,
        "resolution_notes": resolution_notes,
    }


def main():
    fieldnames = [
        "ticket_id", "created_date", "resolved_date", "category", "subcategory",
        "application_name", "priority", "status", "assigned_team", "assigned_engineer",
        "reported_by", "root_cause", "sla_target_hours", "first_response_minutes",
        "resolution_time_hours", "sla_breached", "reopened_count", "change_related",
        "csat_score", "resolution_notes",
    ]

    rows = [generate_ticket(i) for i in range(1, N_TICKETS + 1)]
    rows.sort(key=lambda r: r["created_date"])

    out_path = "incidents.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} tickets -> {out_path}")


if __name__ == "__main__":
    main()
