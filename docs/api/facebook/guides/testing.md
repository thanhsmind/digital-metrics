# Testing Guide for Facebook APIs

## Overview

This guide provides instructions for testing the Facebook API endpoints in the Digital Metrics application. It covers setup requirements, test data, and common testing scenarios.

## Prerequisites

1. Facebook Developer Account
2. Facebook Business Manager Account
3. Facebook App with necessary permissions
4. Access Token with required scopes:
   - `ads_read`
   - `pages_read_engagement`
   - `pages_show_list`
   - `business_management`

## Setup

1. Clone the repository and install dependencies
2. Configure environment variables:
   ```env
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   ```
3. Import the Postman collection from `docs/api/facebook/postman/facebook_api_collection.json`
4. Set up Postman environment variables:
   - `base_url`: Your API base URL (default: `http://localhost:8000`)
   - `access_token`: Your Facebook access token

## Test Data

### Business Manager

```json
{
  "business_id": "675341657897354",
  "name": "Test Business"
}
```

### Ad Account

```json
{
  "ad_account_id": "act_123456789",
  "name": "Test Ad Account"
}
```

### Campaigns

```json
{
  "campaigns": [
    {
      "id": "23851234567890",
      "name": "Test Campaign 1"
    },
    {
      "id": "23851234567891",
      "name": "Test Campaign 2"
    }
  ]
}
```

### Pages

```json
{
  "pages": [
    {
      "id": "123456789",
      "name": "Test Page 1"
    },
    {
      "id": "987654321",
      "name": "Test Page 2"
    }
  ]
}
```

## Testing Sequence

1. **Verify Access**

   - Test `/debug_token` to verify token validity
   - Test `/check_business_pages_access` to verify page permissions

2. **Check Available Metrics**

   - Test `/available_metrics` to get valid metrics for each type

3. **Test Business Insights**

   - Test `/business_post_insights_csv` with valid business ID
   - Test `/business_posts_and_reels_insights_csv` with valid business ID

4. **Test Campaign Metrics**
   - Test `/campaign_metrics` with valid ad account and campaign IDs
   - Test `/campaign_metrics_csv` with the same parameters

## Common Test Cases

### 1. Date Range Validation

```bash
# Invalid date range (end before start)
curl -X GET "{{base_url}}/facebook/business_post_insights_csv" \
  -H "Authorization: Bearer {{access_token}}" \
  -d '{
    "business_id": "675341657897354",
    "since_date": "2024-03-31",
    "until_date": "2024-03-01"
  }'

# Expected: 400 Bad Request
```

### 2. Invalid Metrics

```bash
# Invalid metric name
curl -X GET "{{base_url}}/facebook/campaign_metrics" \
  -H "Authorization: Bearer {{access_token}}" \
  -d '{
    "ad_account_id": "act_123456789",
    "campaign_ids": ["23851234567890"],
    "metrics": "invalid_metric,spend"
  }'

# Expected: Warning about invalid metric, continues with valid metrics
```

### 3. Invalid Access Token

```bash
# Expired or invalid token
curl -X GET "{{base_url}}/facebook/debug_token" \
  -H "Authorization: Bearer INVALID_TOKEN"

# Expected: 401 Unauthorized
```

### 4. Missing Required Parameters

```bash
# Missing business_id
curl -X GET "{{base_url}}/facebook/check_business_pages_access"

# Expected: 400 Bad Request
```

## Error Handling Tests

1. **Network Errors**

   - Test with Facebook API downtime simulation
   - Expected: 503 Service Unavailable

2. **Rate Limiting**

   - Make multiple rapid requests
   - Expected: 429 Too Many Requests

3. **Permission Errors**

   - Test with token missing required scopes
   - Expected: 403 Forbidden

4. **Invalid Input**
   - Test with malformed JSON
   - Test with invalid date formats
   - Expected: 400 Bad Request

## CSV Output Validation

1. Check UTF-8 encoding with BOM
2. Verify header row matches requested metrics
3. Validate data types in each column
4. Check for proper handling of special characters

## Performance Testing

1. **Large Date Ranges**

   - Test with 30-day periods
   - Test with 90-day periods
   - Monitor response times

2. **Multiple Campaigns**

   - Test with 5 campaigns
   - Test with 20 campaigns
   - Monitor memory usage

3. **Concurrent Requests**
   - Test with 5 simultaneous requests
   - Test with 10 simultaneous requests
   - Monitor server stability

## Troubleshooting

### Common Issues

1. **Token Expiration**

   - Symptom: 401 Unauthorized
   - Solution: Refresh access token

2. **Missing Permissions**

   - Symptom: 403 Forbidden
   - Solution: Check required scopes in app settings

3. **Rate Limiting**

   - Symptom: 429 Too Many Requests
   - Solution: Implement exponential backoff

4. **Data Inconsistency**
   - Symptom: Missing or null values
   - Solution: Check metric availability for time period

### Debug Tools

1. Use `/debug_token` to check token status
2. Use `/available_metrics` to verify metric names
3. Check application logs for detailed error messages
4. Monitor Facebook Marketing API changelog for updates

## Support

For additional support:

1. Check Facebook Marketing API documentation
2. Review application logs
3. Contact system administrator
