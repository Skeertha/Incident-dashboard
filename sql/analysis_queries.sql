-- ===========================================================================
-- analysis_queries.sql
-- Application Support & Incident Troubleshooting Dashboard
-- SQL used to derive every KPI and chart shown on the dashboard.
-- ===========================================================================

-- 1. Total ticket volume & status breakdown -------------------------------
SELECT status, COUNT(*) AS ticket_count
FROM incidents
GROUP BY status
ORDER BY ticket_count DESC;

-- 2. Monthly incident trend (created vs resolved) --------------------------
SELECT
    DATE_FORMAT(created_date, '%Y-%m') AS month,
    COUNT(*) AS incidents_created,
    SUM(CASE WHEN resolved_date IS NOT NULL THEN 1 ELSE 0 END) AS incidents_resolved
FROM incidents
GROUP BY DATE_FORMAT(created_date, '%Y-%m')
ORDER BY month;

-- 3. Mean Time To Resolve (MTTR) overall and by priority --------------------
SELECT
    priority,
    ROUND(AVG(resolution_time_hours), 2) AS avg_resolution_hours,
    COUNT(*) AS resolved_tickets
FROM incidents
WHERE resolution_time_hours IS NOT NULL
GROUP BY priority
ORDER BY FIELD(priority, 'P1 - Critical','P2 - High','P3 - Medium','P4 - Low');

-- 4. SLA compliance % overall ------------------------------------------------
SELECT
    ROUND(100.0 * SUM(CASE WHEN sla_breached = FALSE THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN sla_breached IS NOT NULL THEN 1 ELSE 0 END), 0), 2) AS sla_compliance_pct
FROM incidents;

-- 5. SLA compliance % by priority -------------------------------------------
SELECT
    priority,
    COUNT(*) AS total_closed,
    SUM(CASE WHEN sla_breached = TRUE THEN 1 ELSE 0 END) AS breached,
    ROUND(100.0 * SUM(CASE WHEN sla_breached = FALSE THEN 1 ELSE 0 END) / COUNT(*), 2) AS sla_compliance_pct
FROM incidents
WHERE sla_breached IS NOT NULL
GROUP BY priority
ORDER BY FIELD(priority, 'P1 - Critical','P2 - High','P3 - Medium','P4 - Low');

-- 6. SLA compliance % by team (identifies teams needing support) -----------
SELECT
    assigned_team,
    COUNT(*) AS total_closed,
    ROUND(100.0 * SUM(CASE WHEN sla_breached = FALSE THEN 1 ELSE 0 END) / COUNT(*), 2) AS sla_compliance_pct,
    ROUND(AVG(resolution_time_hours), 2) AS avg_resolution_hours
FROM incidents
WHERE sla_breached IS NOT NULL
GROUP BY assigned_team
ORDER BY sla_compliance_pct ASC;

-- 7. Top incident categories by volume --------------------------------------
SELECT category, COUNT(*) AS ticket_count,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM incidents), 2) AS pct_of_total
FROM incidents
GROUP BY category
ORDER BY ticket_count DESC;

-- 8. Applications generating the most incidents (candidates for stability work)
SELECT application_name, COUNT(*) AS ticket_count,
       SUM(CASE WHEN priority = 'P1 - Critical' THEN 1 ELSE 0 END) AS critical_count
FROM incidents
GROUP BY application_name
ORDER BY ticket_count DESC
LIMIT 10;

-- 9. Root cause distribution (for resolved tickets) --------------------------
SELECT root_cause, COUNT(*) AS ticket_count
FROM incidents
WHERE root_cause IS NOT NULL AND root_cause <> ''
GROUP BY root_cause
ORDER BY ticket_count DESC;

-- 10. Reopen rate -------------------------------------------------------------
SELECT
    ROUND(100.0 * SUM(reopened_count) / COUNT(*), 2) AS reopen_rate_pct
FROM incidents
WHERE status IN ('Resolved','Closed','Reopened');

-- 11. Change-related incidents (measures change-management quality) ----------
SELECT
    change_related,
    COUNT(*) AS ticket_count,
    ROUND(AVG(resolution_time_hours), 2) AS avg_resolution_hours
FROM incidents
GROUP BY change_related;

-- 12. Average first response time by priority (triage speed) -----------------
SELECT priority, ROUND(AVG(first_response_minutes), 1) AS avg_first_response_minutes
FROM incidents
GROUP BY priority
ORDER BY FIELD(priority, 'P1 - Critical','P2 - High','P3 - Medium','P4 - Low');

-- 13. Customer satisfaction (CSAT) average by team ----------------------------
SELECT assigned_team, ROUND(AVG(csat_score), 2) AS avg_csat, COUNT(*) AS rated_tickets
FROM incidents
WHERE csat_score IS NOT NULL AND csat_score <> ''
GROUP BY assigned_team
ORDER BY avg_csat DESC;

-- 14. Ticket volume by day-of-week & hour (staffing / demand heatmap) --------
SELECT
    DAYNAME(created_date) AS day_of_week,
    HOUR(created_date) AS hour_of_day,
    COUNT(*) AS ticket_count
FROM incidents
GROUP BY DAYNAME(created_date), HOUR(created_date)
ORDER BY FIELD(day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), hour_of_day;

-- 15. Engineer-level workload & performance -----------------------------------
SELECT
    assigned_engineer,
    COUNT(*) AS tickets_handled,
    ROUND(AVG(resolution_time_hours), 2) AS avg_resolution_hours,
    ROUND(100.0 * SUM(CASE WHEN sla_breached = FALSE THEN 1 ELSE 0 END) / COUNT(*), 2) AS sla_compliance_pct
FROM incidents
WHERE resolution_time_hours IS NOT NULL
GROUP BY assigned_engineer
ORDER BY tickets_handled DESC;

-- 16. Currently open / breach-risk tickets (operational "live" view) ---------
SELECT ticket_id, priority, application_name, assigned_team, created_date,
       TIMESTAMPDIFF(HOUR, created_date, NOW()) AS hours_open,
       sla_target_hours
FROM incidents
WHERE status IN ('Open','In Progress')
ORDER BY priority, hours_open DESC;
