# HubSpot Deals ETL - Data Extraction Service

## Overview

This service extracts deals data from HubSpot CRM using DLT (Data Load Tool) and provides REST API endpoints for managing extraction jobs.

## Features

- **HubSpot CRM Integration**: Extract deals data from HubSpot CRM API v3
- **Job Management**: Start, monitor, and control extraction jobs
- **Data Export**: Download results in JSON, CSV, and Excel formats
- **Checkpointing**: Resume interrupted extractions
- **Rate Limiting**: Respect HubSpot API rate limits (150 req/10s)
- **Multi-tenant**: Support for multiple organizations
- **Data Transformation**: Convert HubSpot data to structured database format

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Docker and Docker Compose
- HubSpot account with Private App access token

### Environment Setup

1. Copy environment template:
```bash
cp .env.example .env
```

2. Update `.env` with your configuration:
```bash
# HubSpot API Configuration
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
HUBSPOT_API_BASE_URL=https://api.hubapi.com
HUBSPOT_API_TIMEOUT=30

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hubspot_deals_etl
DB_USER=postgres
DB_PASSWORD=your-password
DB_SCHEMA=hubspot_deals
```

### Running with Docker

1. Start services:
```bash
docker-compose up -d --build
```

2. Check health:
```bash
curl http://localhost:5200/health
```

3. View API documentation:
```bash
open http://localhost:5200/docs
```

### Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up database:
```bash
# Create database and tables
python -c "from models.database import init_db; init_db()"
```

3. Start the service:
```bash
python app.py
```

## API Usage

### Start HubSpot Deals Extraction

```bash
curl -X POST "http://localhost:5200/scan/start" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "scanId": "hubspot-deals-001",
      "type": ["hubspot_deals"],
      "auth": {
        "access_token": "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
      },
      "filters": {
        "archived": false,
        "dealStages": ["qualifiedtobuy", "presentationscheduled", "contractsent"],
        "properties": ["dealname", "amount", "dealstage", "closedate", "pipeline"]
      }
    }
  }'
```

### Monitor Progress

```bash
curl "http://localhost:5200/scan/status/hubspot-deals-001"
```

### Get Results

```bash
curl "http://localhost:5200/scan/result/hubspot-deals-001?page=1&page_size=100"
```

### Download Results

```bash
# CSV format
curl "http://localhost:5200/scan/download/hubspot-deals-001/csv" -o hubspot_deals.csv

# Excel format
curl "http://localhost:5200/scan/download/hubspot-deals-001/excel" -o hubspot_deals.xlsx

# JSON format
curl "http://localhost:5200/scan/download/hubspot-deals-001/json" -o hubspot_deals.json
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `PORT` | Service port | `5200` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `hubspot_deals_etl` |
| `HUBSPOT_ACCESS_TOKEN` | HubSpot Private App token | Required |
| `HUBSPOT_API_TIMEOUT` | API timeout (seconds) | `30` |
| `HUBSPOT_BATCH_SIZE` | Records per API request | `100` |
| `LOG_LEVEL` | Logging level | `INFO` |

### HubSpot Scan Configuration

```json
{
  "config": {
    "scanId": "unique-identifier",
    "type": ["hubspot_deals"],
    "auth": {
      "access_token": "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    },
    "filters": {
      "archived": false,
      "dealStages": ["qualifiedtobuy", "presentationscheduled"],
      "pipelines": ["default"],
      "properties": ["dealname", "amount", "dealstage", "closedate"],
      "dateRange": {
        "property": "closedate",
        "startDate": "2024-01-01",
        "endDate": "2024-12-31"
      }
    }
  }
}
```

## Development

### Project Structure

```
hubspot-deals-etl/
├── api/                           # REST API endpoints
├── models/                        # Database models
├── services/                      # Business logic
│   ├── hubspot_api_service.py    # HubSpot CRM API client
│   ├── data_source.py            # DLT data source for deals
│   ├── extraction_service.py     # Extraction orchestration
│   └── database_service.py       # Database operations
├── docs/                          # Documentation
│   ├── INTEGRATION-DOCS.md       # HubSpot API integration guide
│   ├── DATABASE-DESIGN-DOCS.md   # Database schema documentation
│   ├── APi-DOCS.md               # Service API documentation
│   └── HUBSPOT-SETUP-GUIDE.md    # HubSpot account setup guide
├── test-results/                  # Test data and results
├── app.py                         # Flask application
├── config.py                      # Configuration
├── test_hubspot_integration.py    # Integration test script
└── requirements.txt               # Dependencies
```

### Testing

Run the integration test:
```bash
# Set your HubSpot access token
export HUBSPOT_ACCESS_TOKEN="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Run comprehensive test suite
python test_hubspot_integration.py --verbose --output test_results.json
```

Run individual tests:
```bash
# Test API connection only
python test_hubspot_integration.py --token YOUR_TOKEN

# Test with verbose output
python test_hubspot_integration.py --token YOUR_TOKEN --verbose
```

### HubSpot Setup

1. **Create HubSpot Developer Account**
   - Go to https://developers.hubspot.com/
   - Sign up for free developer account
   - Create test account

2. **Create Private App**
   - Navigate to Settings → Integrations → Private Apps
   - Create new private app: "DLT Deals Extractor"
   - Add required scopes: `crm.objects.deals.read`
   - Generate access token

3. **Create Test Data**
   - Add 5 test deals with different stages and amounts
   - Ensure variety in deal properties for testing

See `docs/HUBSPOT-SETUP-GUIDE.md` for detailed instructions.

## Data Schema

### HubSpot Deals Table

The service creates a `hubspot_deals` table with the following structure:

```sql
CREATE TABLE hubspot_deals (
    id VARCHAR(255) PRIMARY KEY,
    scan_job_id VARCHAR(255) NOT NULL,
    deal_id VARCHAR(255) NOT NULL,           -- HubSpot deal ID
    deal_name VARCHAR(500),                  -- Deal name/title
    amount DECIMAL(15,2),                    -- Deal amount
    deal_stage VARCHAR(100),                 -- Current deal stage
    close_date TIMESTAMP,                    -- Expected/actual close date
    pipeline VARCHAR(100),                   -- Sales pipeline
    deal_type VARCHAR(100),                  -- Deal type (new/existing business)
    hubspot_owner_id VARCHAR(255),          -- Deal owner ID
    hubspot_created_at TIMESTAMP,           -- Creation date in HubSpot
    hubspot_updated_at TIMESTAMP,           -- Last update in HubSpot
    raw_properties JSON,                     -- Complete HubSpot properties
    _extracted_at TIMESTAMP NOT NULL,       -- ETL extraction timestamp
    _scan_id VARCHAR(255) NOT NULL,         -- Scan identifier
    _tenant_id VARCHAR(255),                -- Multi-tenant organization ID
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

## Monitoring

### Health Checks

- **Health endpoint**: `GET /health`
- **Stats endpoint**: `GET /stats`

### Logging

Logs are structured JSON format with the following levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General information and progress
- `WARNING`: Warning messages and rate limits
- `ERROR`: Error messages and failures

### Metrics

The service tracks:
- HubSpot API request counts and response times
- Deals extraction statistics (total, processed, failed)
- Rate limiting and retry attempts
- Database performance and connection health

## Troubleshooting

### Common Issues

1. **Authentication Errors (401)**
   - Verify HubSpot access token format: `pat-na1-...`
   - Check token is not expired
   - Ensure private app has correct scopes

2. **Permission Errors (403)**
   - Verify `crm.objects.deals.read` scope is enabled
   - Check private app is installed in correct HubSpot account

3. **Rate Limiting (429)**
   - Service automatically handles HubSpot rate limits
   - Check logs for retry attempts and delays

4. **No Deals Retrieved**
   - Verify deals exist in HubSpot account
   - Check `archived` filter setting
   - Ensure deal stages filter matches existing data

5. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database and schema exist

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python app.py
```

### HubSpot API Testing

Test HubSpot API access directly:
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=5" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Performance

### Rate Limiting
- HubSpot allows 150 requests per 10 seconds
- Service automatically throttles to ~67ms between requests
- Implements exponential backoff for 429 responses

### Batch Processing
- Processes 100 deals per API request (HubSpot maximum)
- Saves checkpoints every 5 pages (500 deals)
- Supports pause/resume functionality

### Database Optimization
- Indexes on deal_id, scan_id, tenant_id, and deal_stage
- Composite indexes for common query patterns
- JSON storage for flexible property handling

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Service Version**: 1.0.0  
**HubSpot CRM API**: v3  
**Last Updated**: 2024-12-16