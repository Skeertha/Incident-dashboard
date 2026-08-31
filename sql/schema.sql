-- ===========================================================================
-- schema.sql
-- Application Support & Incident Troubleshooting Dashboard
-- Target DB: MySQL / PostgreSQL compatible (minor tweaks noted inline)
-- ===========================================================================

DROP TABLE IF EXISTS incidents;

CREATE TABLE incidents (
    ticket_id               VARCHAR(20)     PRIMARY KEY,
    created_date            DATETIME        NOT NULL,
    resolved_date           DATETIME        NULL,
    category                VARCHAR(50)     NOT NULL,
    subcategory             VARCHAR(60)     NOT NULL,
    application_name        VARCHAR(60)     NOT NULL,
    priority                VARCHAR(20)     NOT NULL,          -- P1 - Critical / P2 - High / P3 - Medium / P4 - Low
    status                  VARCHAR(20)     NOT NULL,          -- Open / In Progress / Resolved / Closed / Reopened
    assigned_team           VARCHAR(40)     NOT NULL,
    assigned_engineer       VARCHAR(60)     NOT NULL,
    reported_by             VARCHAR(40)     NOT NULL,
    root_cause              VARCHAR(40)     NULL,
    sla_target_hours        INT             NOT NULL,
    first_response_minutes  INT             NOT NULL,
    resolution_time_hours   DECIMAL(8,2)    NULL,
    sla_breached            BOOLEAN         NULL,
    reopened_count          INT             DEFAULT 0,
    change_related          BOOLEAN         DEFAULT FALSE,
    csat_score              TINYINT         NULL,              -- 1-5
    resolution_notes        VARCHAR(500)    NULL,

    CONSTRAINT chk_priority CHECK (priority IN ('P1 - Critical','P2 - High','P3 - Medium','P4 - Low')),
    CONSTRAINT chk_csat CHECK (csat_score BETWEEN 1 AND 5 OR csat_score IS NULL)
);

-- Helpful indexes for the dashboard's most common filters/aggregations
CREATE INDEX idx_incidents_created_date   ON incidents (created_date);
CREATE INDEX idx_incidents_priority       ON incidents (priority);
CREATE INDEX idx_incidents_team           ON incidents (assigned_team);
CREATE INDEX idx_incidents_category       ON incidents (category);
CREATE INDEX idx_incidents_status         ON incidents (status);

-- ---------------------------------------------------------------------------
-- Optional companion table: change_requests
-- Demonstrates incident <-> change linkage for "problem/change management"
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS change_requests;

CREATE TABLE change_requests (
    change_id       VARCHAR(20)   PRIMARY KEY,
    ticket_id       VARCHAR(20)   NULL REFERENCES incidents(ticket_id),
    change_type     VARCHAR(30),         -- Standard / Normal / Emergency
    implemented_on  DATETIME,
    outcome         VARCHAR(20)          -- Successful / Failed / Rolled Back
);

-- Load data (MySQL):
-- LOAD DATA LOCAL INFILE 'incidents.csv'
-- INTO TABLE incidents
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS;

-- Load data (PostgreSQL):
-- \copy incidents FROM 'incidents.csv' WITH (FORMAT csv, HEADER true);
