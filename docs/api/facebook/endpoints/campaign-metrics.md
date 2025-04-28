# Campaign Metrics Endpoints

## GET /campaign_metrics

Retrieves metrics for specified Facebook Ad campaigns.

### Endpoint

```
GET /facebook/campaign_metrics
```

### Parameters

| Parameter     | Type   | Required | Description                                    | Default                        |
| ------------- | ------ | -------- | ---------------------------------------------- | ------------------------------ |
| ad_account_id | string | Yes      | ID of the Facebook Ad Account                  | -                              |
| campaign_ids  | array  | Yes      | List of campaign IDs to fetch metrics for      | -                              |
| metrics       | string | No       | Comma-separated list of campaign metrics       | spend,impressions,reach,clicks |
| since_date    | string | Yes      | Start date (YYYY-MM-DD)                        | -                              |
| until_date    | string | Yes      | End date (YYYY-MM-DD)                          | -                              |
| access_token  | string | Yes      | Facebook access token with ads_read permission | -                              |

### Example Request

```bash
curl -X GET "http://localhost:8000/facebook/campaign_metrics" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "ad_account_id": "act_123456789",
    "campaign_ids": ["23851234567890", "23851234567891"],
    "metrics": "spend,impressions,reach,clicks",
    "since_date": "2024-03-01",
    "until_date": "2024-03-31",
    "access_token": "EAABw..."
  }'
```

### Response

```json
{
  "data": [
    {
      "campaign_id": "23851234567890",
      "campaign_name": "Campaign 1",
      "metrics": {
        "spend": "1000.50",
        "impressions": "50000",
        "reach": "30000",
        "clicks": "1500"
      }
    },
    {
      "campaign_id": "23851234567891",
      "campaign_name": "Campaign 2",
      "metrics": {
        "spend": "750.25",
        "impressions": "40000",
        "reach": "25000",
        "clicks": "1200"
      }
    }
  ]
}
```

## GET /campaign_metrics_csv

Retrieves campaign metrics in CSV format.

### Endpoint

```
GET /facebook/campaign_metrics_csv
```

### Parameters

Same as `/campaign_metrics` endpoint.

### Example Request

```bash
curl -X GET "http://localhost:8000/facebook/campaign_metrics_csv" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "ad_account_id": "act_123456789",
    "campaign_ids": ["23851234567890", "23851234567891"],
    "metrics": "spend,impressions,reach,clicks",
    "since_date": "2024-03-01",
    "until_date": "2024-03-31",
    "access_token": "EAABw..."
  }'
```

### Response

CSV file with headers:

```csv
campaign_id,campaign_name,spend,impressions,reach,clicks
23851234567890,"Campaign 1",1000.50,50000,30000,1500
23851234567891,"Campaign 2",750.25,40000,25000,1200
```

## Common Campaign Metrics

| Metric      | Description                                 |
| ----------- | ------------------------------------------- |
| spend       | Amount spent in account currency            |
| impressions | Number of times ads were shown              |
| reach       | Number of unique people who saw ads         |
| clicks      | Number of clicks on ads                     |
| cpc         | Average cost per click                      |
| cpm         | Average cost per 1,000 impressions          |
| ctr         | Click-through rate (clicks/impressions)     |
| frequency   | Average number of times each person saw ads |

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid campaign IDs or metrics provided"
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
  "detail": "Insufficient permissions to access ad account"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error processing request"
}
```

## Notes

1. The access token must have `ads_read` permission
2. Campaign IDs must belong to the specified ad account
3. Dates must be in YYYY-MM-DD format
4. The end date must be after or equal to the start date
5. CSV response includes UTF-8 BOM for Excel compatibility
6. Invalid metrics are ignored with a warning
7. At least one valid metric must be provided
