# Business Insights Endpoints

## GET /business_post_insights_csv

Retrieves post insights for all pages associated with a Facebook Business and returns the data as a CSV file.

### Endpoint

```
GET /facebook/business_post_insights_csv
```

### Parameters

| Parameter   | Type   | Required | Description                          | Default                                        |
| ----------- | ------ | -------- | ------------------------------------ | ---------------------------------------------- |
| business_id | string | Yes      | ID of the Facebook Business Manager  | -                                              |
| metrics     | string | No       | Comma-separated list of post metrics | post_impressions,post_reach,post_engaged_users |
| since_date  | string | Yes      | Start date (YYYY-MM-DD)              | -                                              |
| until_date  | string | Yes      | End date (YYYY-MM-DD)                | -                                              |

### Example Request

```bash
curl -X GET "http://localhost:8000/facebook/business_post_insights_csv" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "business_id": "675341657897354",
    "metrics": "post_impressions,post_reach,post_engaged_users",
    "since_date": "2024-03-01",
    "until_date": "2024-03-31"
  }'
```

### Response

CSV file with headers:

```csv
post_id,created_time,message,type,post_impressions,post_reach,post_engaged_users
123_456,2024-03-15T10:00:00Z,"Sample post content",photo,1000,800,150
```

## GET /business_posts_and_reels_insights_csv

Retrieves both post and reel insights for all pages associated with a Facebook Business.

### Endpoint

```
GET /facebook/business_posts_and_reels_insights_csv
```

### Parameters

| Parameter    | Type   | Required | Description                          | Default                                                  |
| ------------ | ------ | -------- | ------------------------------------ | -------------------------------------------------------- |
| business_id  | string | Yes      | ID of the Facebook Business Manager  | -                                                        |
| post_metrics | string | No       | Comma-separated list of post metrics | post_impressions,post_reach,post_engaged_users           |
| reel_metrics | string | No       | Comma-separated list of reel metrics | video_total_views,video_avg_time_watched,video_view_time |
| since_date   | string | Yes      | Start date (YYYY-MM-DD)              | -                                                        |
| until_date   | string | Yes      | End date (YYYY-MM-DD)                | -                                                        |

### Example Request

```bash
curl -X GET "http://localhost:8000/facebook/business_posts_and_reels_insights_csv" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "business_id": "675341657897354",
    "post_metrics": "post_impressions,post_reach,post_engaged_users",
    "reel_metrics": "video_total_views,video_avg_time_watched,video_view_time",
    "since_date": "2024-03-01",
    "until_date": "2024-03-31"
  }'
```

### Response

CSV file with headers:

```csv
content_id,created_time,message,type,content_type,impressions,reach,engaged_users,total_views,avg_time_watched
123_456,2024-03-15T10:00:00Z,"Sample post",photo,Post,1000,800,150,null,null
789_012,2024-03-16T11:00:00Z,"Sample reel",video,Reel,null,null,null,5000,15.5
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid metrics: [invalid_metric]. Available: [list of valid metrics]"
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

1. The response is a CSV file with UTF-8 encoding and BOM for Excel compatibility
2. Dates must be in YYYY-MM-DD format
3. The end date must be after or equal to the start date
4. Invalid metrics are ignored with a warning
5. At least one valid metric must be provided
