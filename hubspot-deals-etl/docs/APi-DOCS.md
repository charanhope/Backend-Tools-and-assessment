# HubSpot Deals ETL - API Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URLs](#base-urls)
4. [Common Response Formats](#common-response-formats)
5. [API Endpoints](#api-endpoints)
6. [Health & Stats Endpoints](#health--stats-endpoints)
7. [Error Handling](#error-handling)
8. [Examples](#examples)
9. [Rate Limiting](#rate-limiting)
10. [Changelog](#changelog)

## 🔍 Overview

The HubSpot Deals ETL service provides REST API endpoints for extracting, processing, and managing HubSpot deals data through automated scan jobs.

### API Version
- **Version**: 1.0.0
- **Base Path**: `/api/v1`
- **Content Type**: `application/json`
- **Documentation**: Available at `/docs` (Swagger UI)

### Key Features
- **Deal Extraction**: Extract deals data from HubSpot CRM API v3
- **Scan Management**: Start, monitor, and control extraction jobs
- **Data Export**: Download results in JSON, CSV, and Excel formats
- **Multi-tenant Support**: Isolated data processing per organization
- **Real-time Monitoring**: Track extraction progress and status

## 🔐 Authentication

The HubSpot Deals ETL service requires HubSpot Private App access tokens for authentication.

### Required Credentials
- **HubSpot Access Token**: Private app access token from HubSpot
- **Tenant ID**: Organization identifier (optional for multi-tenant setups)

### Required HubSpot Permissions
- `crm.objects.deals.read` - Read access to deals objects
- `crm.schemas.deals.read` - Read access to deal schemas (optional)

### Authentication Headers
```
Authorization: Bearer <hubspot_access_token>
Content-Type: application/json
X-Tenant-ID: <tenant_id> (optional)
```

## 🌐 Base URLs

### Development
```
http://localhost:5200
```

### Staging
```
http://localhost:5201
```

### Production
```
http://localhost:5202
```

### Swagger Documentation
```
http://localhost:5200/docs
```

## 📊 Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response (Validation)
```json
{
  "status": "error",
  "message": "Input validation failed",
  "errors": {
    "[field_name]": "Field is required"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response (Application Logic)
```json
{
  "status": "error",
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "The requested resource was not found",
  "details": {},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Pagination Response
```json
{
  "pagination": {
    "current_page": 1,
    "page_size": 50,
    "total_items": 150,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  }
}
```

## 🔍 Scan Endpoints

### 1. Start HubSpot Deals Extraction

**POST** `/scan/start`

Initiates a new HubSpot deals extraction process.

#### Request Body
```json
{
  "config": {
    "scanId": "hubspot-deals-001",
    "type": ["hubspot_deals"],
    "auth": {
      "access_token": "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    },
    "filters": {
      "archived": false,
      "dealStages": ["qualifiedtobuy", "presentationscheduled", "contractsent"],
      "pipelines": ["default"],
      "dateRange": {
        "property": "closedate",
        "startDate": "2024-01-01",
        "endDate": "2024-12-31"
      }
    },
    "properties": [
      "dealname", "amount", "dealstage", "closedate", "pipeline", 
      "dealtype", "hubspot_owner_id", "description"
    ]
  }
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config.scanId` | string | Yes | Unique identifier for the scan (alphanumeric, hyphens, underscores only, max 255 chars) |
| `config.type` | array | Yes | Service types to scan (must include "hubspot_deals") |
| `config.auth.access_token` | string | Yes | HubSpot Private App access token |
| `config.filters.archived` | boolean | No | Include archived deals (default: false) |
| `config.filters.dealStages` | array | No | Filter by specific deal stages |
| `config.filters.pipelines` | array | No | Filter by specific pipelines |
| `config.filters.dateRange` | object | No | Filter by date range on specified property |
| `config.properties` | array | No | List of HubSpot properties to extract (default: all standard properties) |

#### Response
```json
{
  "message": "HubSpot deals extraction started",
  "scanId": "hubspot-deals-001",
  "status": "started"
}
```

#### Status Codes
- **202**: Extraction started successfully
- **400**: Invalid request data or HubSpot authentication failed
- **409**: Extraction already in progress
- **500**: Internal server error

---

### 2. Get Extraction Status

**GET** `/scan/status/{scan_id}`

Retrieves the current status of an extraction process.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response (Existing Extraction)
```json
{
  "id": "internal-job-id",
  "scanId": "hubspot-deals-001",
  "status": "running",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "progress": {
    "total_deals": 1500,
    "processed_deals": 850,
    "failed_deals": 5,
    "current_batch": 9,
    "total_batches": 15,
    "deals_per_batch": 100,
    "success_rate": "99.4%"
  }
}
```

#### Response (Non-existent Extraction)
```json
{
  "id": null,
  "scanId": null,
  "status": "not_found",
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "created_at": null,
  "updated_at": null
}
```

#### Status Values
- **pending**: Extraction queued but not started
- **running**: Extraction in progress
- **completed**: Extraction finished successfully
- **failed**: Extraction failed with error
- **cancelled**: Extraction cancelled by user
- **not_found**: Extraction does not exist

#### Status Codes
- **200**: Always returns 200 (check `status` field for actual state)
- **400**: Invalid scan ID format

---

### 3. Cancel Extraction

**POST** `/scan/cancel/{scan_id}`

Cancels an ongoing extraction process.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response
```json
{
  "message": "HubSpot deals extraction cancelled successfully",
  "scanId": "hubspot-deals-001",
  "status": "cancelled"
}
```

#### Status Codes
- **200**: Extraction cancelled successfully
- **400**: Invalid scan ID format or extraction cannot be cancelled
- **404**: Extraction not found
- **500**: Internal server error

---

### 4. Remove Extraction

**DELETE** `/scan/remove/{scan_id}`

Removes an extraction and all associated data from the system.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response
```json
{
  "message": "Extraction and 1,234 deals removed successfully",
  "scanId": "hubspot-deals-001",
  "status": "removed"
}
```

#### Status Codes
- **200**: Extraction removed successfully
- **400**: Invalid scan ID format or extraction cannot be removed
- **404**: Extraction not found
- **500**: Internal server error

---

### 5. Get Extraction Results

**GET** `/scan/result/{scan_id}`

Retrieves paginated extraction results with full event details.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (minimum: 1) |
| `page_size` | integer | No | 100 | Events per page (1-1000) |

#### Response
```json
{
  "scanId": "hubspot-deals-001",
  "status": "completed",
  "data": [
    {
      "id": "result-uuid-1",
      "deal_id": "51",
      "deal_name": "New Website Project",
      "amount": 1500.00,
      "deal_stage": "presentationscheduled",
      "close_date": "2024-02-15T00:00:00.000Z",
      "pipeline": "default",
      "deal_type": "newbusiness",
      "hubspot_owner_id": "owner-123",
      "hubspot_created_at": "2024-01-15T10:30:00.000Z",
      "hubspot_updated_at": "2024-01-20T14:22:00.000Z",
      "_extracted_at": "2024-01-25T09:15:00.000Z",
      "_scan_id": "hubspot-deals-001"
    }
  ],
  "pagination": {
    "current_page": 1,
    "page_size": 100,
    "total_deals": 1500,
    "total_pages": 15,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  },
  "count": 100,
  "total_count": 1500,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:45:00Z",
  "error_message": null
}
```

#### Status Codes
- **200**: Results retrieved successfully
- **400**: Invalid scan ID format or pagination parameters
- **404**: Extraction not found
- **500**: Internal server error

---

### 6. Download Extraction Results

**GET** `/scan/download/{scan_id}/{format}`

Downloads extraction results in the specified format.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |
| `format` | string | Yes | Download format (json, csv, excel) |

#### Supported Formats
- **json**: JSON format with pretty printing
- **csv**: Comma-separated values with headers
- **excel**: Microsoft Excel (.xlsx) format

#### Response
File download with appropriate content-type and Content-Disposition headers:
- **JSON**: `Content-Type: application/json`
- **CSV**: `Content-Type: text/csv`
- **Excel**: `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

#### Status Codes
- **200**: File download initiated
- **400**: Invalid scan ID format or unsupported format
- **404**: Extraction not found
- **500**: Internal server error

#### Example URLs
```
GET /scan/download/my-scan-001/json
GET /scan/download/my-scan-001/csv
GET /scan/download/my-scan-001/excel
```

---

## 🏥 Health & Stats Endpoints

### 1. Health Check

**GET** `/health`

Returns the overall health status of the service.

#### Response (Healthy)
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "[Service Name]",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "cache": "healthy",
    "external_api": "healthy"
  }
}
```

#### Response (Unhealthy)
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "[Service Name]",
  "version": "1.0.0",
  "checks": {
    "database": "unhealthy: connection timeout",
    "cache": "healthy",
    "external_api": "degraded: high latency"
  }
}
```

#### Status Codes
- **200**: Service is healthy
- **503**: Service is unhealthy

---

### 2. Service Statistics

**GET** `/stats`

Returns comprehensive service statistics and performance metrics.

#### Response
```json
{
  "total_requests": 15000,
  "active_connections": 23,
  "success_rate": 99.5,
  "average_response_time": 125.5,
  "errors_last_hour": 5,
  "uptime": "7 days, 3:24:15",
  "memory_usage": "512MB",
  "cpu_usage": "15%",
  "last_restart": "2024-01-08T10:30:00Z"
}
```

#### Status Codes
- **200**: Statistics retrieved successfully
- **500**: Internal server error

---

## ⚠️ Error Handling

### Error Response Formats

#### Validation Errors (400)
Returned for input validation failures:
```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Input validation failed",
  "errors": {
    "[field_name]": "[error_message]"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Authentication Errors (401)
```json
{
  "status": "error",
  "error_code": "UNAUTHORIZED",
  "message": "Authentication required",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Authorization Errors (403)
```json
{
  "status": "error",
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Not Found Errors (404)
```json
{
  "status": "error",
  "error_code": "NOT_FOUND",
  "message": "Resource not found",
  "resource_id": "[id]",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Conflict Errors (409)
```json
{
  "status": "error",
  "error_code": "CONFLICT",
  "message": "Resource already exists",
  "conflicting_field": "[field_name]",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Rate Limit Errors (429)
```json
{
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests",
  "retry_after": 60,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Server Errors (500)
```json
{
  "status": "error",
  "error_code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "incident_id": "inc_123456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `CONFLICT` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_ERROR` | Server error |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

---

## 📚 Examples

### Complete Extraction Workflow

#### 1. Start HubSpot Deals Extraction
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
        "dateRange": {
          "property": "closedate",
          "startDate": "2024-01-01",
          "endDate": "2024-12-31"
        }
      },
      "properties": [
        "dealname", "amount", "dealstage", "closedate", "pipeline", 
        "dealtype", "hubspot_owner_id", "description"
      ]
    }
  }'
```

#### 2. Monitor Progress
```bash
curl "http://localhost:5200/scan/status/hubspot-deals-001"
```

#### 3. Get Results
```bash
curl "http://localhost:5200/scan/result/hubspot-deals-001?page=1&page_size=50"
```

#### 4. Download Results
```bash
# Download as CSV
curl "http://localhost:5200/scan/download/hubspot-deals-001/csv" \
  -o "hubspot_deals_results.csv"

# Download as Excel
curl "http://localhost:5200/scan/download/hubspot-deals-001/excel" \
  -o "hubspot_deals_results.xlsx"

# Download as JSON
curl "http://localhost:5200/scan/download/hubspot-deals-001/json" \
  -o "hubspot_deals_results.json"
```

#### 5. Cancel Extraction (if needed)
```bash
curl -X POST "http://localhost:5200/scan/cancel/hubspot-deals-001"
```

#### 6. Remove Extraction (cleanup)
```bash
curl -X DELETE "http://localhost:5200/scan/remove/hubspot-deals-001"
```

### PowerShell Examples

#### Start Extraction
```powershell
$body = @{
  config = @{
    scanId = "powershell-test-001"
    type = @("calendar")
    auth = @{
      "[auth_key_1]" = "[auth_value_1]"
      "[auth_key_2]" = "[auth_value_2]"
    }
    dateRange = @{
      startDate = "2024-01-01"
      endDate = "2024-01-31"
    }
    user_upns = @("user@company.com")
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "https://api.your-domain.com/scan/start" -Method Post -Body $body -ContentType "application/json"
```

#### Get Status
```powershell
Invoke-RestMethod -Uri "https://api.your-domain.com/scan/status/powershell-test-001"
```

#### Download Results
```powershell
# Download Excel file
Invoke-WebRequest -Uri "https://api.your-domain.com/scan/download/powershell-test-001/excel" -OutFile "results.xlsx"

# Download CSV file
Invoke-WebRequest -Uri "https://api.your-domain.com/scan/download/powershell-test-001/csv" -OutFile "results.csv"
```

### Python Examples

#### Start Extraction
```python
import requests

url = "https://api.your-domain.com/scan/start"
payload = {
    "config": {
        "scanId": "python-test-001",
        "type": ["calendar"],
        "auth": {
            "[auth_key_1]": "[auth_value_1]",
            "[auth_key_2]": "[auth_value_2]"
        },
        "dateRange": {
            "startDate": "2024-01-01",
            "endDate": "2024-01-31"
        },
        "user_upns": ["user@company.com"]
    }
}

response = requests.post(url, json=payload)
print(response.json())
```

#### Monitor Progress
```python
import requests
import time

scan_id = "python-test-001"
url = f"https://api.your-domain.com/scan/status/{scan_id}"

while True:
    response = requests.get(url)
    status = response.json()
    
    print(f"Status: {status['status']}")
    
    if status['status'] in ['completed', 'failed', 'cancelled', 'not_found']:
        break
    
    time.sleep(10)  # Check every 10 seconds
```

#### Get Paginated Results
```python
import requests

scan_id = "python-test-001"
page = 1
all_events = []

while True:
    url = f"https://api.your-domain.com/scan/result/{scan_id}?page={page}&page_size=100"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        all_events.extend(data['data'])
        
        if not data['pagination']['has_next']:
            break
        
        page += 1
    else:
        print(f"Error: {response.status_code}")
        break

print(f"Total events retrieved: {len(all_events)}")
```

#### Download Results
```python
import requests

scan_id = "python-test-001"

# Download different formats
formats = ['json', 'csv', 'excel']
for fmt in formats:
    url = f"https://api.your-domain.com/scan/download/{scan_id}/{fmt}"
    response = requests.get(url)
    
    if response.status_code == 200:
        filename = f"calendar_results.{fmt if fmt != 'excel' else 'xlsx'}"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {fmt}: {response.status_code}")
```

#### Error Handling
```python
import requests