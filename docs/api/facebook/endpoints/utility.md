# Utility Endpoints

## GET /available_metrics

Retrieves lists of available metrics for posts, reels, and campaigns.

### Endpoint

```
GET /facebook/available_metrics
```

### Parameters

None

### Example Request

```bash
curl -X GET "http://localhost:8000/facebook/available_metrics" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Response

```json
{
  "post_metrics": [
    "post_impressions",
    "post_reach",
    "post_engaged_users",
    "post_reactions_by_type_total",
    "post_clicks",
    "post_negative_feedback"
  ],
  "reel_metrics": [
    "video_total_views",
    "video_avg_time_watched",
    "video_view_time",
    "video_views_unique",
    "video_view_time_organic",
    "video_sound_on"
  ],
  "campaign_metrics": [
    "spend",
    "impressions",
    "reach",
    "clicks",
    "cpc",
    "cpm",
    "ctr",
    "frequency"
  ]
}
```

## GET /debug_token

Debugs a Facebook access token and returns its metadata.

### Endpoint

```
GET /facebook/debug_token
```

### Parameters

| Parameter   | Type   | Required | Description               |
| ----------- | ------ | -------- | ------------------------- |
| input_token | string | Yes      | The access token to debug |

### Example Request

```bash
curl -X GET "http://localhost:8000/facebook/debug_token?input_token=EAABw..." \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Response

```json
{
  "data": {
    "app_id": "123456789",
    "type": "USER",
    "application": "Your App Name",
    "data_access_expires_at": 1234567890,
    "expires_at": 1234567890,
    "is_valid": true,
    "issued_at": 1234567890,
    "scopes": [
      "ads_read",
      "pages_read_engagement",
      "pages_show_list",
      "business_management"
    ],
    "user_id": "123456789"
  }
}
```

## GET /check_business_pages_access

Checks access to all pages associated with a Facebook Business.

### Endpoint

```
GET /facebook/check_business_pages_access
```

### Parameters

| Parameter   | Type   | Required | Description                         |
| ----------- | ------ | -------- | ----------------------------------- |
| business_id | string | Yes      | ID of the Facebook Business Manager |

### Example Request

```bash
curl -X GET "http://localhost:8000/facebook/check_business_pages_access?business_id=675341657897354" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Response

```json
{
  "pages": [
    {
      "id": "123456789",
      "name": "Page 1",
      "access_status": "full",
      "required_permissions": ["pages_read_engagement"],
      "missing_permissions": []
    },
    {
      "id": "987654321",
      "name": "Page 2",
      "access_status": "partial",
      "required_permissions": ["pages_read_engagement", "pages_show_list"],
      "missing_permissions": ["pages_show_list"]
    }
  ],
  "summary": {
    "total_pages": 2,
    "full_access": 1,
    "partial_access": 1,
    "no_access": 0
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid input token format"
}
```

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "Insufficient permissions to access resource"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error processing request"
}
```

## Notes

1. All endpoints require a valid access token in the Authorization header
2. The `/debug_token` endpoint requires an app access token or client token
3. The `/check_business_pages_access` endpoint requires business_management permission
4. Access status can be "full", "partial", or "none"
5. Required permissions vary based on the metrics being accessed
