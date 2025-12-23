# 🗄️ HubSpot Deals ETL - Database Schema Design

This document provides the database schema design for the HubSpot Deals ETL service with two core tables: ScanJob and HubSpotDeals.

---

## 📋 Overview

The HubSpot Deals ETL database schema consists of two main tables:

1. **ScanJob** - Core scan job management and tracking
2. **HubSpotDeals** - Storage for extracted HubSpot deals data

---

## 🏗️ Table Schemas

### 1. ScanJob Table

**Purpose**: Core scan job management and status tracking

| **Column Name**         | **Type**    | **Constraints**           | **Description**                          |
|-------------------------|-------------|---------------------------|------------------------------------------|
| `id`                    | String      | PRIMARY KEY               | Unique internal identifier               |
| `scan_id`               | String      | UNIQUE, NOT NULL, INDEX   | External scan identifier                 |
| `status`                | String      | NOT NULL, INDEX           | pending, running, completed, failed, cancelled |
| `scan_type`             | String      | NOT NULL                  | Type of scan (user, project, calendar, etc.) |
| `config`                | JSON        | NOT NULL                  | Scan configuration and parameters        |
| `organization_id`       | String      | NULLABLE                  | Organization/tenant identifier           |
| `error_message`         | Text        | NULLABLE                  | Error details if scan failed            |
| `started_at`            | DateTime    | NULLABLE                  | When scan execution started             |
| `completed_at`          | DateTime    | NULLABLE                  | When scan finished                      |
| `total_items`           | Integer     | DEFAULT 0                 | Total items to process                  |
| `processed_items`       | Integer     | DEFAULT 0                 | Items successfully processed            |
| `failed_items`          | Integer     | DEFAULT 0                 | Items that failed processing            |
| `success_rate`          | String      | NULLABLE                  | Calculated success percentage           |
| `batch_size`            | Integer     | DEFAULT 50                | Processing batch size                   |
| `created_at`            | DateTime    | NOT NULL                  | Record creation timestamp               |
| `updated_at`            | DateTime    | NOT NULL                  | Record last update timestamp            |

**Indexes:**
```sql
-- Performance indexes
CREATE INDEX idx_scan_status_created ON scan_jobs(status, created_at);
CREATE INDEX idx_scan_id_status ON scan_jobs(scan_id, status);
CREATE INDEX idx_scan_type_status ON scan_jobs(scan_type, status);
CREATE INDEX idx_scan_org_status ON scan_jobs(organization_id, status);
```

---

### 2. HubSpotDeals Table

**Purpose**: Store extracted HubSpot deals data with ETL metadata

| **Column Name**         | **Type**    | **Constraints**           | **Description**                          |
|-------------------------|-------------|---------------------------|------------------------------------------|
| `id`                    | String      | PRIMARY KEY               | Unique result identifier                 |
| `scan_job_id`           | String      | FOREIGN KEY, NOT NULL     | Reference to scan_jobs.id               |
| `deal_id`               | String      | NOT NULL, INDEX           | HubSpot deal ID                         |
| `deal_name`             | String      | NULLABLE                  | Deal name/title                         |
| `amount`                | Decimal     | NULLABLE                  | Deal amount in company currency         |
| `deal_stage`            | String      | NULLABLE, INDEX           | Current deal stage                      |
| `close_date`            | DateTime    | NULLABLE, INDEX           | Expected or actual close date           |
| `pipeline`              | String      | NULLABLE                  | Sales pipeline identifier               |
| `deal_type`             | String      | NULLABLE                  | Type of deal (newbusiness, existing)    |
| `hubspot_owner_id`      | String      | NULLABLE                  | HubSpot owner ID                        |
| `deal_stage_probability`| Decimal     | NULLABLE                  | Probability of closing (0-1)            |
| `description`           | Text        | NULLABLE                  | Deal description                        |
| `analytics_source`      | String      | NULLABLE                  | Original source of the deal             |
| `num_associated_contacts`| Integer    | DEFAULT 0                 | Number of associated contacts           |
| `priority`              | String      | NULLABLE                  | Deal priority (high, medium, low)       |
| `next_step`             | String      | NULLABLE                  | Next step in the deal process           |
| `forecast_amount`       | Decimal     | NULLABLE                  | Forecasted amount                       |
| `forecast_probability`  | Decimal     | NULLABLE                  | Forecast probability                    |
| `hubspot_created_at`    | DateTime    | NULLABLE                  | Deal creation date in HubSpot           |
| `hubspot_updated_at`    | DateTime    | NULLABLE                  | Last modification date in HubSpot       |
| `archived`              | Boolean     | DEFAULT FALSE             | Whether deal is archived                |
| `raw_properties`        | JSON        | NULLABLE                  | Complete HubSpot properties JSON        |
| `_extracted_at`         | DateTime    | NOT NULL                  | ETL extraction timestamp                |
| `_scan_id`              | String      | NOT NULL, INDEX           | External scan identifier                |
| `_tenant_id`            | String      | NULLABLE, INDEX           | Multi-tenant organization ID            |
| `created_at`            | DateTime    | NOT NULL                  | Record creation timestamp               |
| `updated_at`            | DateTime    | NOT NULL                  | Record last update timestamp            |

**CREATE TABLE Statement:**

```sql
CREATE TABLE hubspot_deals (
    id VARCHAR(255) PRIMARY KEY,
    scan_job_id VARCHAR(255) NOT NULL REFERENCES scan_jobs(id) ON DELETE CASCADE,
    deal_id VARCHAR(255) NOT NULL,
    deal_name VARCHAR(500),
    amount DECIMAL(15,2),
    deal_stage VARCHAR(100),
    close_date TIMESTAMP,
    pipeline VARCHAR(100),
    deal_type VARCHAR(100),
    hubspot_owner_id VARCHAR(255),
    deal_stage_probability DECIMAL(3,2),
    description TEXT,
    analytics_source VARCHAR(255),
    num_associated_contacts INTEGER DEFAULT 0,
    priority VARCHAR(50),
    next_step VARCHAR(500),
    forecast_amount DECIMAL(15,2),
    forecast_probability DECIMAL(3,2),
    hubspot_created_at TIMESTAMP,
    hubspot_updated_at TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE,
    raw_properties JSON,
    _extracted_at TIMESTAMP NOT NULL,
    _scan_id VARCHAR(255) NOT NULL,
    _tenant_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes for Performance:**
```sql
-- Basic performance indexes
CREATE INDEX idx_hubspot_deals_scan_job ON hubspot_deals(scan_job_id);
CREATE INDEX idx_hubspot_deals_deal_id ON hubspot_deals(deal_id);
CREATE INDEX idx_hubspot_deals_scan_id ON hubspot_deals(_scan_id);

-- Multi-tenant support
CREATE INDEX idx_hubspot_deals_tenant ON hubspot_deals(_tenant_id);
CREATE INDEX idx_hubspot_deals_tenant_scan ON hubspot_deals(_tenant_id, _scan_id);

-- Business logic indexes
CREATE INDEX idx_hubspot_deals_stage ON hubspot_deals(deal_stage);
CREATE INDEX idx_hubspot_deals_close_date ON hubspot_deals(close_date);
CREATE INDEX idx_hubspot_deals_pipeline ON hubspot_deals(pipeline);
CREATE INDEX idx_hubspot_deals_owner ON hubspot_deals(hubspot_owner_id);

-- ETL metadata indexes
CREATE INDEX idx_hubspot_deals_extracted_at ON hubspot_deals(_extracted_at);
CREATE INDEX idx_hubspot_deals_archived ON hubspot_deals(archived);

-- Composite indexes for common queries
CREATE INDEX idx_hubspot_deals_tenant_stage_date ON hubspot_deals(_tenant_id, deal_stage, close_date);
CREATE INDEX idx_hubspot_deals_pipeline_stage ON hubspot_deals(pipeline, deal_stage);
```

---

---

## 🔗 Relationships

### Primary Relationships
```sql
-- ScanJob to HubSpot Deals (One-to-Many)
scan_jobs.id ← hubspot_deals.scan_job_id
```

### Cascade Behavior
- **DELETE ScanJob**: Cascades to delete all related HubSpot deals
- **Multi-tenant Isolation**: Use _tenant_id for data separation

---

## 📊 Common Queries

### Basic Scan Management

```sql
-- Get scan job with status
SELECT id, scan_id, status, scan_type, total_items, processed_items 
FROM scan_jobs 
WHERE scan_id = 'your-scan-id';

-- Get active scans
SELECT scan_id, status, started_at, scan_type 
FROM scan_jobs 
WHERE status IN ('running', 'pending') 
ORDER BY created_at DESC;

-- Get scan progress
SELECT 
    scan_id,
    total_items,
    processed_items,
    CASE 
        WHEN total_items > 0 THEN ROUND((processed_items * 100.0 / total_items), 2)
        ELSE 0 
    END as progress_percentage
FROM scan_jobs 
WHERE scan_id = 'your-scan-id';
```

### HubSpot Deals Management

```sql
-- Get paginated deals results
SELECT id, deal_id, deal_name, amount, deal_stage, close_date, pipeline
FROM hubspot_deals 
WHERE scan_job_id = 'job-id'
ORDER BY close_date DESC 
LIMIT 100 OFFSET 0;

-- Count deals by stage
SELECT deal_stage, COUNT(*) as count, SUM(amount) as total_amount
FROM hubspot_deals 
WHERE scan_job_id = 'job-id' AND archived = FALSE
GROUP BY deal_stage;

-- Count deals by pipeline
SELECT pipeline, COUNT(*) as count, AVG(amount) as avg_amount
FROM hubspot_deals 
WHERE scan_job_id = 'job-id' AND archived = FALSE
GROUP BY pipeline;

-- Search deals by name or description
SELECT deal_id, deal_name, amount, deal_stage 
FROM hubspot_deals 
WHERE scan_job_id = 'job-id' 
AND (deal_name ILIKE '%search_term%' OR description ILIKE '%search_term%');

-- Get deals by date range
SELECT deal_id, deal_name, amount, close_date
FROM hubspot_deals 
WHERE scan_job_id = 'job-id' 
AND close_date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY close_date;

-- Get deals by owner
SELECT hubspot_owner_id, COUNT(*) as deal_count, SUM(amount) as total_value
FROM hubspot_deals 
WHERE scan_job_id = 'job-id' AND archived = FALSE
GROUP BY hubspot_owner_id;

-- Multi-tenant query
SELECT deal_id, deal_name, amount, deal_stage
FROM hubspot_deals 
WHERE _tenant_id = 'tenant-123' 
AND _scan_id = 'scan-001'
ORDER BY _extracted_at DESC;
```

### Control Operations

```sql
-- Get scan job status and basic info
SELECT scan_id, status, started_at, completed_at, error_message
FROM scan_jobs 
WHERE scan_id = 'your-scan-id';

-- Cancel a scan (update status)
UPDATE scan_jobs 
SET status = 'cancelled', 
    completed_at = CURRENT_TIMESTAMP,
    error_message = 'Cancelled by user'
WHERE scan_id = 'your-scan-id' 
AND status IN ('pending', 'running');
```

---

## 🛠️ Implementation Examples

### Creating a New Scan Job

```sql
-- Create scan job
INSERT INTO scan_jobs (
    id, scan_id, status, scan_type, config, organization_id, batch_size
) VALUES (
    'uuid-1', 'my-scan-001', 'pending', 'user_extraction', 
    '{"auth": {"token": "..."}, "filters": {...}}', 
    'org-123', 100
);
```

### Adding HubSpot Deals Results

```sql
-- Insert HubSpot deals results
INSERT INTO hubspot_deals (
    id, scan_job_id, deal_id, deal_name, amount, deal_stage, close_date, 
    pipeline, deal_type, hubspot_owner_id, hubspot_created_at, hubspot_updated_at,
    _extracted_at, _scan_id, _tenant_id
) VALUES 
(
    'uuid-3', 'uuid-1', '51', 'New Website Project', 1500.00, 'presentationscheduled', 
    '2024-02-15 00:00:00', 'default', 'newbusiness', 'owner-123', 
    '2024-01-15 10:30:00', '2024-01-20 14:22:00', CURRENT_TIMESTAMP, 
    'hubspot-scan-001', 'tenant-123'
),
(
    'uuid-4', 'uuid-1', '52', 'Enterprise Software License', 5000.00, 'qualifiedtobuy', 
    '2024-03-01 00:00:00', 'default', 'existingbusiness', 'owner-456', 
    '2024-01-10 09:15:00', '2024-01-18 16:45:00', CURRENT_TIMESTAMP, 
    'hubspot-scan-001', 'tenant-123'
);

-- Batch insert with raw properties
INSERT INTO hubspot_deals (
    id, scan_job_id, deal_id, deal_name, amount, deal_stage, 
    raw_properties, _extracted_at, _scan_id, _tenant_id
) VALUES (
    'uuid-5', 'uuid-1', '53', 'Mobile App Development', 25000.00, 'contractsent',
    '{"dealname": "Mobile App Development", "amount": "25000", "dealstage": "contractsent", "custom_field_1": "value1"}',
    CURRENT_TIMESTAMP, 'hubspot-scan-001', 'tenant-123'
);

-- Update scan job progress
UPDATE scan_jobs 
SET processed_items = processed_items + 3,
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'uuid-1';
```

### Status Updates

```sql
-- Start scan
UPDATE scan_jobs 
SET status = 'running', 
    started_at = CURRENT_TIMESTAMP 
WHERE scan_id = 'my-scan-001';

-- Complete scan
UPDATE scan_jobs 
SET status = 'completed', 
    completed_at = CURRENT_TIMESTAMP,
    success_rate = CASE 
        WHEN total_items > 0 THEN ROUND(((total_items - failed_items) * 100.0 / total_items), 2)::TEXT || '%'
        ELSE '100%' 
    END
WHERE scan_id = 'my-scan-001';
```

---

## 🔧 Customization Options

### Result Table Naming
Replace `[result_table]` with your preferred name:
- `scan_results` (generic)
- `user_results` (specific to user scans)
- `extraction_results` (for data extraction)
- `calendar_events` (for calendar data)
- `project_data` (for project information)

### Result Table Customization Examples

**Replace `[result_table]` and customize fields for your specific data:**

**1. User/People Data:**
```sql
CREATE TABLE user_results (
    id VARCHAR PRIMARY KEY,
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    user_id VARCHAR UNIQUE,
    username VARCHAR,
    email VARCHAR,
    display_name VARCHAR,
    department VARCHAR,
    job_title VARCHAR,
    manager_email VARCHAR,
    status VARCHAR, -- active, inactive, suspended
    last_login TIMESTAMP,
    permissions JSON,
    profile_data JSON,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**2. Project/Repository Data:**
```sql  
CREATE TABLE project_results (
    id VARCHAR PRIMARY KEY,
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    project_id VARCHAR UNIQUE,
    project_key VARCHAR,
    project_name VARCHAR,
    description TEXT,
    project_type VARCHAR, -- software, business, etc.
    lead_email VARCHAR,
    team_members JSON,
    project_status VARCHAR,
    created_date TIMESTAMP,
    last_updated TIMESTAMP,
    settings JSON,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**3. Issue/Ticket Data:**
```sql
CREATE TABLE issue_results (
    id VARCHAR PRIMARY KEY,  
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    issue_id VARCHAR UNIQUE,
    issue_key VARCHAR,
    title VARCHAR,
    description TEXT,
    issue_type VARCHAR,
    priority VARCHAR,
    status VARCHAR,
    assignee_email VARCHAR,
    reporter_email VARCHAR,
    created_date TIMESTAMP,
    updated_date TIMESTAMP,
    resolved_date TIMESTAMP,
    labels JSON,
    custom_fields JSON,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**4. Calendar/Event Data:**
```sql
CREATE TABLE calendar_events (
    id VARCHAR PRIMARY KEY,
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    event_id VARCHAR UNIQUE,
    calendar_id VARCHAR,
    title VARCHAR,
    description TEXT,
    organizer_name VARCHAR,
    organizer_email VARCHAR,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    location VARCHAR,
    is_virtual BOOLEAN,
    meeting_url VARCHAR,
    attendees JSON,
    event_type VARCHAR, -- meeting, appointment, etc.
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**5. Generic/Flexible Data (when structure varies):**
```sql
CREATE TABLE scan_results (
    id VARCHAR PRIMARY KEY,
    scan_job_id VARCHAR REFERENCES scan_jobs(id),
    object_id VARCHAR, -- ID from source system
    object_type VARCHAR, -- user, project, issue, etc.
    object_name VARCHAR, -- Display name
    raw_data JSON NOT NULL, -- Complete API response
    processed_data JSON, -- Cleaned/normalized data
    extraction_metadata JSON, -- Processing info, batch, etc.
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Additional Columns (Optional Customizations)

**For ScanJob Table:**
```sql
-- Add service-specific columns
ALTER TABLE scan_jobs ADD COLUMN service_name VARCHAR(50);
ALTER TABLE scan_jobs ADD COLUMN api_version VARCHAR(20);
ALTER TABLE scan_jobs ADD COLUMN rate_limit_remaining INTEGER;
ALTER TABLE scan_jobs ADD COLUMN priority_level VARCHAR(20) DEFAULT 'normal';
ALTER TABLE scan_jobs ADD COLUMN max_retries INTEGER DEFAULT 3;
```

---

## 📈 Performance Considerations

### Indexing Strategy
- **Primary Operations**: Index on `scan_id`, `status`, and `created_at`
- **Filtering**: Index on `organization_id`, `scan_type`, `result_type`
- **Pagination**: Composite indexes on frequently queried column combinations
- **Foreign Keys**: Always index foreign key columns

### Data Retention
```sql
-- Archive completed scans older than 90 days
CREATE TABLE scan_jobs_archive AS SELECT * FROM scan_jobs WHERE FALSE;

-- Move old data
INSERT INTO scan_jobs_archive 
SELECT * FROM scan_jobs 
WHERE status = 'completed' 
AND completed_at < CURRENT_DATE - INTERVAL '90 days';

-- Clean up
DELETE FROM scan_jobs 
WHERE status = 'completed' 
AND completed_at < CURRENT_DATE - INTERVAL '90 days';
```

### Large Result Sets
```sql
-- Partition result table by scan_job_id for very large datasets
CREATE TABLE [result_table] (
    -- columns as defined above
) PARTITION BY HASH (scan_job_id);

-- Create partitions
CREATE TABLE [result_table]_p0 PARTITION OF [result_table] FOR VALUES WITH (modulus 4, remainder 0);
CREATE TABLE [result_table]_p1 PARTITION OF [result_table] FOR VALUES WITH (modulus 4, remainder 1);
-- etc.
```

---

## 🛡️ Data Integrity

### Constraints
```sql
-- Ensure valid status values
ALTER TABLE scan_jobs ADD CONSTRAINT check_valid_status 
CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'));

-- Ensure valid priority levels
ALTER TABLE scan_controls ADD CONSTRAINT check_valid_priority 
CHECK (priority_level IN ('low', 'normal', 'high', 'urgent'));

-- Ensure positive values
ALTER TABLE scan_jobs ADD CONSTRAINT check_positive_counts 
CHECK (total_items >= 0 AND processed_items >= 0 AND failed_items >= 0);
```

### Triggers
```sql
-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_scan_jobs_updated_at 
    BEFORE UPDATE ON scan_jobs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

### Usage Guidelines

### Best Practices
1. **Use appropriate batch sizes** for your data volume to manage memory and performance
2. **Implement proper error handling** and store error details in `error_message`
3. **Regular cleanup** of old scan jobs and results based on retention policies
4. **Monitor scan progress** using the progress tracking fields (`total_items`, `processed_items`)
5. **Use JSON config** to store flexible scan parameters and authentication details

### Common Patterns
- **Progress Tracking**: Update `processed_items` and `failed_items` as scan progresses
- **Error Recovery**: Store detailed error information in `error_message` field
- **Flexible Configuration**: Use JSON `config` field for scan parameters, auth details, filters
- **Status Management**: Use clear status transitions (pending → running → completed/failed/cancelled)
- **Data Organization**: Use meaningful `scan_id` values for easy identification

---

**Database Schema Version**: 1.0  
**Last Updated**: [Current Date]  
**Compatible With**: PostgreSQL, MySQL, SQLite, SQL Server