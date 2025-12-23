# HubSpot Developer Account Setup Guide

## Overview
This guide walks through setting up a HubSpot developer account and creating a private app for the HubSpot Deals ETL service.

## Step 1: Create HubSpot Developer Account

### 1.1 Sign Up for Developer Account
1. Go to https://developers.hubspot.com/
2. Click "Get started for free"
3. Create account with email and password
4. Verify email address

### 1.2 Create Developer Test Account
1. Log into HubSpot Developer Portal
2. Navigate to "Test Accounts" section
3. Click "Create test account"
4. Choose "Marketing Hub Starter" (free tier)
5. Complete account setup

## Step 2: Create Private App

### 2.1 Navigate to Private Apps
1. In your HubSpot test account, go to Settings (gear icon)
2. Navigate to "Integrations" → "Private Apps"
3. Click "Create a private app"

### 2.2 Configure Private App
1. **Basic Info:**
   - App name: "DLT Deals Extractor"
   - Description: "ETL service for extracting HubSpot deals data"
   
2. **Scopes (Required):**
   - ✅ `crm.objects.deals.read` - Read deals
   - ✅ `crm.schemas.deals.read` - Read deal properties (optional)

3. **Review and Create:**
   - Review permissions
   - Click "Create app"
   - Copy the generated access token immediately

## Step 3: Access Token Management

### 3.1 Secure Token Storage
```bash
# Store in environment variable (recommended)
export HUBSPOT_ACCESS_TOKEN="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Or store in .env file (never commit to git)
echo "HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" >> .env
```

### 3.2 Token Format
- Format: `pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Length: 47 characters
- Prefix: `pat-na1-` (Private App Token, North America 1)

## Step 4: Test API Access

### 4.1 Test Authentication
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 4.2 Expected Response
```json
{
  "results": [],
  "paging": {}
}
```

## Step 5: Account Information

### 5.1 Account Details Template
```json
{
  "account_info": {
    "developer_account_email": "your-email@example.com",
    "test_account_name": "Your Test Account Name",
    "test_account_id": "12345678",
    "private_app_name": "DLT Deals Extractor",
    "private_app_id": "app-12345",
    "access_token_prefix": "pat-na1-",
    "scopes_granted": [
      "crm.objects.deals.read",
      "crm.schemas.deals.read"
    ],
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## Step 6: Security Best Practices

### 6.1 Token Security
- ❌ Never commit access tokens to version control
- ✅ Use environment variables or secure vaults
- ✅ Rotate tokens regularly (every 90 days recommended)
- ✅ Use different tokens for dev/staging/production

### 6.2 Scope Management
- ✅ Only request minimum required scopes
- ✅ Review and audit scopes regularly
- ❌ Don't request write permissions unless needed

## Step 7: Troubleshooting

### 7.1 Common Issues
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check token format and validity |
| 403 Forbidden | Verify scopes are granted |
| 429 Rate Limited | Implement retry with backoff |
| Token expired | Generate new token in private app settings |

### 7.2 Rate Limits
- **Limit:** 150 requests per 10 seconds
- **Burst:** Up to 150 requests in quick succession
- **Best Practice:** 67ms between requests (1000ms / 15 = 67ms)

## Step 8: Documentation Links

- **HubSpot Developers:** https://developers.hubspot.com/
- **Private Apps Guide:** https://developers.hubspot.com/docs/api/private-apps
- **CRM API Documentation:** https://developers.hubspot.com/docs/api/crm/deals
- **Rate Limiting:** https://developers.hubspot.com/docs/api/usage-details
- **Developer Community:** https://community.hubspot.com/t5/HubSpot-Developers/ct-p/developers

---

**Setup Status:** ✅ Ready for implementation
**Next Step:** Create test deals data