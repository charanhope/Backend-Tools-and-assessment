# 📋 HubSpot Deals ETL - Integration with HubSpot CRM API

This document explains the HubSpot CRM API v3 endpoints required by the HubSpot Deals ETL service to extract deals data from HubSpot instances.

---

## 📋 Overview

The HubSpot Deals ETL service integrates with HubSpot CRM API v3 endpoints to extract deals information. Below are the required and optional endpoints:

### ✅ **Required Endpoint (Essential)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals`            | Search and list deals               | v3          | crm.objects.deals.read   | **Required** |

### 🔧 **Optional Endpoints (Advanced Features)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals/{dealId}`   | Get detailed deal information       | v3          | crm.objects.deals.read   | Optional     |
| `/crm/v3/objects/deals/batch/read` | Batch read multiple deals           | v3          | crm.objects.deals.read   | Optional     |
| `/crm/v3/properties/deals`         | Get deal property definitions       | v3          | crm.schemas.deals.read   | Optional     |
| `/crm/v3/pipelines/deals`          | Get deal pipeline configurations    | v3          | crm.schemas.deals.read   | Optional     |

## 🔐 Authentication Requirements

### **Private App Access Token Authentication**
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

### **Required Permissions**
- **crm.objects.deals.read**: Read access to deals objects
- **crm.schemas.deals.read**: Read access to deal schemas and properties (optional for advanced features)

---

## 🌐 HubSpot CRM API Endpoints

### 🎯 **PRIMARY ENDPOINT (Required for Basic Deal Extraction)**

### 1. **Search Deals** - `/crm/v3/objects/deals` ✅ **REQUIRED**

**Purpose**: Get paginated list of all deals - **THIS IS ALL YOU NEED FOR BASIC DEAL EXTRACTION**

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals`

**Query Parameters**:
```
?limit=100&after=cursor_value&properties=dealname,amount,dealstage,closedate&archived=false
```

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=dealname,amount,dealstage,closedate,pipeline,dealtype,createdate,hs_lastmodifieddate
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure** (Contains ALL essential deal data):
```json
{
  "results": [
    {
      "id": "51",
      "properties": {
        "amount": "1500.00",
        "closedate": "2024-02-15T00:00:00.000Z",
        "createdate": "2024-01-15T10:30:00.000Z",
        "dealname": "New Website Project",
        "dealstage": "presentationscheduled",
        "dealtype": "newbusiness",
        "hs_lastmodifieddate": "2024-01-20T14:22:00.000Z",
        "pipeline": "default"
      },
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-20T14:22:00.000Z",
      "archived": false
    },
    {
      "id": "52",
      "properties": {
        "amount": "5000.00",
        "closedate": "2024-03-01T00:00:00.000Z",
        "createdate": "2024-01-10T09:15:00.000Z",
        "dealname": "Enterprise Software License",
        "dealstage": "qualifiedtobuy",
        "dealtype": "existingbusiness",
        "hs_lastmodifieddate": "2024-01-18T16:45:00.000Z",
        "pipeline": "default"
      },
      "createdAt": "2024-01-10T09:15:00.000Z",
      "updatedAt": "2024-01-18T16:45:00.000Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "NTI%3D",
      "link": "https://api.hubapi.com/crm/v3/objects/deals?after=NTI%3D&limit=100"
    }
  }
}
```

**✅ This endpoint provides ALL the default deal fields:**
- Deal ID, Deal Name, Amount, Close Date
- Deal Stage, Deal Type, Pipeline
- Creation and Modification timestamps
- Custom properties (when specified)
- Archived status

**Rate Limit**: 150 requests per 10 seconds

**Query Parameters Details:**
- **limit**: Number of results per page (1-100, default: 10)
- **after**: Cursor for pagination (use value from paging.next.after)
- **properties**: Comma-separated list of properties to include
- **archived**: Include archived deals (true/false, default: false)

**Available Deal Properties:**
- **dealname**: Deal name/title
- **amount**: Deal amount in company currency
- **dealstage**: Current stage in sales pipeline
- **closedate**: Expected or actual close date
- **pipeline**: Sales pipeline ID
- **dealtype**: Type of deal (newbusiness, existingbusiness, etc.)
- **createdate**: Deal creation date
- **hs_lastmodifieddate**: Last modification date
- **hubspot_owner_id**: Deal owner ID
- **dealstage**: Deal stage (appointmentscheduled, qualifiedtobuy, presentationscheduled, decisionmakerboughtin, contractsent, closedwon, closedlost)
- **hs_deal_stage_probability**: Probability of closing (0-1)
- **description**: Deal description
- **hs_analytics_source**: Original source of the deal
- **hs_analytics_source_data_1**: Additional source data
- **hs_analytics_source_data_2**: Additional source data
- **num_associated_contacts**: Number of associated contacts
- **num_contacted_notes**: Number of notes
- **num_notes**: Total number of notes
- **hs_createdate**: HubSpot creation date
- **hs_object_id**: HubSpot object ID
- **hs_deal_amount_calculation_preference**: Amount calculation preference
- **hs_forecast_amount**: Forecasted amount
- **hs_forecast_probability**: Forecast probability
- **hs_manual_forecast_category**: Manual forecast category
- **hs_next_step**: Next step in the deal process
- **hs_priority**: Deal priority (high, medium, low)

---

## 🔧 **OPTIONAL ENDPOINTS (Advanced Features Only)**

> **⚠️ Note**: These endpoints are NOT required for basic [object] extraction. Only implement if you need advanced [object] analytics like [feature 1], [feature 2], or [feature 3].

### 2. **Get [Object] Details** - `/[api_path]/[endpoint_1]/{objectId}` 🔧 **OPTIONAL**

**Purpose**: Get detailed information for a specific [object]

**When to use**: Only if you need additional [object] metadata not available in search

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_1]/{objectId}`

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_1]/[sample_id]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[field_id]": "[sample_id]",
  "[field_url]": "https://[your_instance].[platform_domain]/[api_path]/[endpoint_1]/[sample_id]",
  "[field_name]": "[Sample Object Name]",
  "[field_type]": "[object_type]",
  "[additional_field_1]": {
    "[sub_field_1]": [
      {
        "[property_1]": "[value_1]",
        "[property_2]": "[value_2]",
        "[property_3]": true
      }
    ],
    "[sub_field_2]": [
      {
        "[property_4]": "[value_4]",
        "[property_5]": "[value_5]"
      }
    ]
  },
  "[nested_object]": {
    "[nested_field_1]": "[value_1]",
    "[nested_field_2]": "[value_2]",
    "[nested_field_3]": "[value_3]",
    "[nested_field_4]": "[value_4]",
    "[nested_field_5]": "[value_5]"
  },
  "[boolean_field_1]": true,
  "[boolean_field_2]": false,
  "[boolean_field_3]": false
}
```

---

### 3. **Get [Object] [Related Data]** - `/[api_path]/[endpoint_2]/{objectId}/[related_endpoint]` 🔧 **OPTIONAL**

**Purpose**: Get [related data] associated with a [object]

**When to use**: Only if you need [related data] analysis and [specific metrics]

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_2]/{objectId}/[related_endpoint]`

**Query Parameters**:
```
?[param1]=[value]&[param2]=[value]&[filter_param]=[filter_value]
```

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_2]/[sample_id]/[related_endpoint]?[param2]=[value]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[pagination_start]": 0,
  "[pagination_size]": 50,
  "[pagination_total]": 25,
  "[pagination_last]": false,
  "[data_array]": [
    {
      "[related_id]": 1,
      "[related_url]": "https://[your_instance].[platform_domain]/[api_path]/[related_endpoint]/1",
      "[related_status]": "[status_1]",
      "[related_name]": "[Related Item 1]",
      "[date_start]": "[date_format]",
      "[date_end]": "[date_format]",
      "[date_complete]": "[date_format]",
      "[date_created]": "[date_format]",
      "[origin_field]": "[sample_id]",
      "[description_field]": "[Description text]"
    },
    {
      "[related_id]": 2,
      "[related_url]": "https://[your_instance].[platform_domain]/[api_path]/[related_endpoint]/2",
      "[related_status]": "[status_2]", 
      "[related_name]": "[Related Item 2]",
      "[date_start]": "[date_format]",
      "[date_end]": "[date_format]",
      "[date_created]": "[date_format]",
      "[origin_field]": "[sample_id]",
      "[description_field]": "[Description text]"
    }
  ]
}
```

---

### 4. **Get [Object] Configuration** - `/[api_path]/[endpoint_3]/{objectId}/[config_endpoint]` 🔧 **OPTIONAL**

**Purpose**: Get [object] configuration details ([config_type_1], [config_type_2], [config_type_3])

**When to use**: Only if you need [workflow type] and [object] setup analysis

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_3]/{objectId}/[config_endpoint]`

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_3]/[sample_id]/[config_endpoint]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[field_id]": "[sample_id]",
  "[field_name]": "[Sample Object Name]",
  "[field_type]": "[object_type]",
  "[field_url]": "https://[your_instance].[platform_domain]/[api_path]/[endpoint_3]/[sample_id]/[config_endpoint]",
  "[location_field]": {
    "[location_type]": "[location_value]",
    "[location_identifier]": "[identifier]"
  },
  "[filter_field]": {
    "[filter_id]": "[filter_value]",
    "[filter_url]": "https://[your_instance].[platform_domain]/[api_path]/[filter_endpoint]/[filter_value]"
  },
  "[config_object]": {
    "[config_array]": [
      {
        "[config_name]": "[Config Item 1]",
        "[config_values]": [
          {
            "[config_id]": "[id_1]",
            "[config_url]": "https://[your_instance].[platform_domain]/[api_path]/[status_endpoint]/[id_1]"
          }
        ]
      },
      {
        "[config_name]": "[Config Item 2]",
        "[config_values]": [
          {
            "[config_id]": "[id_2]",
            "[config_url]": "https://[your_instance].[platform_domain]/[api_path]/[status_endpoint]/[id_2]"
          }
        ]
      },
      {
        "[config_name]": "[Config Item 3]",
        "[config_values]": [
          {
            "[config_id]": "[id_3]",
            "[config_url]": "https://[your_instance].[platform_domain]/[api_path]/[status_endpoint]/[id_3]"
          }
        ]
      }
    ],
    "[constraint_type]": "[constraint_value]"
  },
  "[estimation_field]": {
    "[estimation_type]": "[estimation_value]",
    "[estimation_details]": {
      "[detail_id]": "[detail_value]",
      "[detail_name]": "[Detail Display Name]"
    }
  }
}
```

---

### 5. **Get [Object] [Additional Data]** - `/[api_path]/[endpoint_4]/{objectId}/[additional_endpoint]` 🔧 **OPTIONAL**

**Purpose**: Get [additional data] for a [object]

**When to use**: Only if you need [additional data] analysis and [specific functionality]

**Method**: `GET`

**URL**: `https://{baseUrl}/[api_path]/[endpoint_4]/{objectId}/[additional_endpoint]`

**Query Parameters**:
```
?[param1]=[value]&[param2]=[value]&[query_param]=[query_value]&[validation_param]=[validation_value]&[fields_param]=[field1],[field2],[field3],[field4]
```

**Request Example**:
```http
GET https://[your_instance].[platform_domain]/[api_path]/[endpoint_4]/[sample_id]/[additional_endpoint]?[param2]=[value]
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
```

**Response Structure**:
```json
{
  "[pagination_start]": 0,
  "[pagination_size]": 50,
  "[pagination_total]": 120,
  "[data_key]": [
    {
      "[item_id]": "[item_id_value]",
      "[item_key]": "[ITEM-123]",
      "[item_url]": "https://[your_instance].[platform_domain]/[api_path]/[item_endpoint]/[item_id_value]",
      "[item_fields]": {
        "[summary_field]": "[Item summary text]",
        "[status_field]": {
          "[status_id]": "[status_id_value]",
          "[status_name]": "[Status Name]",
          "[status_category]": {
            "[category_id]": 2,
            "[category_key]": "[category_key]",
            "[category_color]": "[color-name]"
          }
        },
        "[assignee_field]": {
          "[assignee_id]": "[assignee_account_id]",
          "[assignee_name]": "[Assignee Name]"
        },
        "[priority_field]": {
          "[priority_id]": "[priority_id_value]",
          "[priority_name]": "[Priority Level]"
        }
      }
    }
  ]
}
```

---

## 📊 Data Extraction Flow

### 🎯 **SIMPLE FLOW (Recommended - Using Only Required Endpoint)**

### **Single Endpoint Approach - `/crm/v3/objects/deals` Only**
```python
def extract_all_deals_simple():
    """Extract all deals using only the /crm/v3/objects/deals endpoint"""
    base_url = "https://api.hubapi.com"
    all_deals = []
    after_cursor = None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    while True:
        params = {
            "limit": 100,
            "properties": "dealname,amount,dealstage,closedate,pipeline,dealtype,createdate,hs_lastmodifieddate,hubspot_owner_id",
            "archived": "false"
        }
        
        if after_cursor:
            params["after"] = after_cursor
        
        response = requests.get(
            f"{base_url}/crm/v3/objects/deals",
            params=params,
            headers=headers
        )
        
        if response.status_code == 429:  # Rate limited
            time.sleep(1)
            continue
            
        data = response.json()
        deals = data.get("results", [])
        
        if not deals:  # No more deals
            break
            
        all_deals.extend(deals)
        
        # Check if there's a next page
        paging = data.get("paging", {})
        if "next" not in paging:
            break
            
        after_cursor = paging["next"]["after"]
    
    return all_deals

# This gives you ALL essential deal data:
# - Deal ID, Deal Name, Amount, Close Date
# - Deal Stage, Pipeline, Deal Type
# - Creation and modification timestamps
# - Deal owner information
```

---

### 🔧 **ADVANCED FLOW (Optional - Multiple Endpoints)**

> **⚠️ Only use this if you need [related_data], [configuration], or [additional_data] data**

### **Step 1: Batch [Object] Retrieval**
```python
# Get [objects] in batches of 50
for start_at in range(0, total_objects, 50):
    response = requests.get(
        f"{base_url}/[api_path]/[primary_endpoint]",
        params={
            "[pagination_param]": start_at,
            "[size_param]": 50
        },
        headers=auth_headers
    )
    objects_data = response.json()
    objects = objects_data.get("[data_array]", [])
```

### **Step 2: Enhanced [Object] Details (Optional)**
```python
# Get detailed information for each [object]
for obj in objects:
    response = requests.get(
        f"{base_url}/[api_path]/[endpoint_1]/{obj['[field_id]']}",
        headers=auth_headers
    )
    detailed_object = response.json()
```

### **Step 3: [Object] [Related Data] (Optional)**
```python
# Get [related data] for each [specific type] [object]
for obj in objects:
    if obj['[field_type]'] == '[specific_type]':
        response = requests.get(
            f"{base_url}/[api_path]/[endpoint_2]/{obj['[field_id]']}/[related_endpoint]",
            params={"[param2]": 50},
            headers=auth_headers
        )
        object_related_data = response.json()
```

### **Step 4: [Object] Configuration (Optional)**
```python
# Get configuration for each [object]
for obj in objects:
    response = requests.get(
        f"{base_url}/[api_path]/[endpoint_3]/{obj['[field_id]']}/[config_endpoint]",
        headers=auth_headers
    )
    object_config = response.json()
```

---

## ⚡ Performance Considerations

### **Rate Limiting**
- **Default Limit**: 150 requests per 10 seconds per API token
- **Burst Limit**: Up to 150 requests can be made in quick succession
- **Best Practice**: Implement exponential backoff on 429 responses

### **Batch Processing**
- **Recommended Batch Size**: 100 deals per request (maximum allowed)
- **Concurrent Requests**: Max 10 parallel requests (deals are complex objects)
- **Request Interval**: 67ms between requests to stay under rate limits (150 req/10s = 1 req per 67ms)

### **Error Handling**
```http
# Rate limit exceeded
HTTP/429 Too Many Requests
Retry-After: 1

# Authentication failed  
HTTP/401 Unauthorized

# Insufficient permissions
HTTP/403 Forbidden

# Deal not found
HTTP/404 Not Found

# Invalid request
HTTP/400 Bad Request
```

---

## 📈 Monitoring & Debugging

### **Request Headers for Debugging**
```http
[AUTH_HEADER]: [AUTH_VALUE]
Content-Type: application/json
User-Agent: [ServiceName]/1.0
X-Request-ID: [object]-scan-001-batch-1
```

### **Response Validation**
```python
def validate_object_response(object_data):
    required_fields = ["[field_id]", "[field_name]", "[field_type]", "[nested_object]"]
    for field in required_fields:
        if field not in object_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate [object] type
    if object_data["[field_type]"] not in ["[type_1]", "[type_2]"]:
        raise ValueError(f"Invalid [object] type: {object_data['[field_type]']}")
```

### **API Usage Metrics**
- Track requests per [time period]
- Monitor response times
- Log rate limit headers
- Track authentication failures

---

## 🧪 Testing API Integration

### **Test Authentication**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Deal Search**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=5&properties=dealname,amount,dealstage" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Deal Details**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals/{dealId}?properties=dealname,amount,dealstage,closedate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Deal Properties**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/properties/deals" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 🚨 Common Issues & Solutions

### **Issue**: 401 Unauthorized
**Solution**: Verify access token is valid and not expired
```bash
curl -X GET "https://api.hubapi.com/crm/v3/objects/deals?limit=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### **Issue**: 403 Forbidden
**Solution**: Check private app has "crm.objects.deals.read" scope enabled

### **Issue**: 429 Rate Limited
**Solution**: Implement retry with exponential backoff
```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 1))
                wait_time = retry_after + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")
```

### **Issue**: Empty Deal List
**Solution**: Check if deals exist in the HubSpot portal and verify archived parameter

### **Issue**: Missing Deal Properties
**Solution**: Ensure properties are specified in the request or use default properties

### **Issue**: Need Pipeline/Stage Information But Want to Keep It Simple**
**Solution**: Start with `/crm/v3/objects/deals` only. Add `/crm/v3/pipelines/deals` later if needed for advanced pipeline analytics

---

## 📞 Support Resources

- **HubSpot CRM API Documentation**: https://developers.hubspot.com/docs/api/crm/deals
- **Rate Limiting Guide**: https://developers.hubspot.com/docs/api/usage-details
- **Authentication Guide**: https://developers.hubspot.com/docs/api/private-apps
- **Deals Properties Reference**: https://developers.hubspot.com/docs/api/crm/properties
- **HubSpot Developer Community**: https://community.hubspot.com/t5/HubSpot-Developers/ct-p/developers