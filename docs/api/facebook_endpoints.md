# Facebook API Endpoints Documentation

## Table of Contents

- [Business Post Insights](#business-post-insights)
- [Business Posts and Reels Insights](#business-posts-and-reels-insights)
- [Campaign Metrics](#campaign-metrics)
- [Post Metrics](#post-metrics)
- [Reel Metrics](#reel-metrics)
- [Utility Endpoints](#utility-endpoints)

## Business Post Insights

### GET /business_post_insights_csv

Retrieves post insights for all pages associated with a Facebook Business and returns the data as a CSV file.

**Endpoint:** `/facebook/business_post_insights_csv`

**Parameters:**

- `business_id` (required): ID of the Facebook Business Manager
- `metrics` (optional): Comma-separated list of post metrics
  - Default: `post_impressions,post_reach,post_engaged_users`
  - Available metrics: See [Available Metrics](#available-metrics)
- `since_date` (required): Start date (YYYY-MM-DD)
- `until_date` (required): End date (YYYY-MM-DD)

**Test Data:**

```json
{
  "business_id": "675341657897354",
  "metrics": "post_impressions,post_reach,post_engaged_users,post_reactions_by_type_total",
  "since_date": "2024-03-01",
  "until_date": "2024-03-31"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/facebook/business_post_insights_csv?business_id=675341657897354&metrics=post_impressions,post_reach,post_engaged_users&since_date=2024-03-01&until_date=2024-03-31" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:** CSV file with headers:

```csv
post_id,created_time,message,type,post_impressions,post_reach,post_engaged_users
123_456,2024-03-15T10:00:00Z,"Sample post content",photo,1000,800,150
```

## Business Posts and Reels Insights

### GET /business_posts_and_reels_insights_csv

Retrieves both post and reel insights for all pages associated with a Facebook Business.

**Endpoint:** `/facebook/business_posts_and_reels_insights_csv`

**Parameters:**

- `business_id` (required): ID of the Facebook Business Manager
- `post_metrics` (optional): Comma-separated list of post metrics
  - Default: `post_impressions,post_reach,post_engaged_users`
- `reel_metrics` (optional): Comma-separated list of reel metrics
  - Default: `video_total_views,video_avg_time_watched,video_view_time`
- `since_date` (required): Start date (YYYY-MM-DD)
- `until_date` (required): End date (YYYY-MM-DD)

**Test Data:**

```json
{
  "business_id": "675341657897354",
  "post_metrics": "post_impressions,post_reach,post_engaged_users",
  "reel_metrics": "video_total_views,video_avg_time_watched,video_view_time",
  "since_date": "2024-03-01",
  "until_date": "2024-03-31"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/facebook/business_posts_and_reels_insights_csv?business_id=675341657897354&post_metrics=post_impressions,post_reach&reel_metrics=video_total_views,video_avg_time_watched&since_date=2024-03-01&until_date=2024-03-31" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:** CSV file with headers:

```csv
content_id,created_time,message,type,content_type,impressions,reach,engaged_users,total_views,avg_time_watched
123_456,2024-03-15T10:00:00Z,"Sample post",photo,Post,1000,800,150,null,null
789_012,2024-03-16T11:00:00Z,"Sample reel",video,Reel,null,null,null,5000,15.5
```

## Campaign Metrics

### GET /campaign_metrics

Retrieves metrics for Facebook ad campaigns.

**Endpoint:** `/facebook/campaign_metrics`

**Parameters:**

- `ad_account_id` (required): ID of the Facebook Ad Account
- `campaign_ids` (optional): Comma-separated list of campaign IDs
- `metrics` (optional): Comma-separated list of metrics
  - Default: `spend,impressions,reach,clicks,ctr`
- `since_date` (required): Start date (YYYY-MM-DD)
- `until_date` (required): End date (YYYY-MM-DD)
- `access_token` (required): Facebook access token

**Test Data:**

```json
{
  "ad_account_id": "act_123456789",
  "campaign_ids": "23456789,34567890",
  "metrics": "spend,impressions,reach,clicks,ctr",
  "since_date": "2024-03-01",
  "until_date": "2024-03-31",
  "access_token": "YOUR_ACCESS_TOKEN"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/facebook/campaign_metrics?ad_account_id=act_123456789&campaign_ids=23456789,34567890&metrics=spend,impressions,reach&since_date=2024-03-01&until_date=2024-03-31" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**

```json
{
  "success": true,
  "message": "Campaign metrics retrieved successfully",
  "data": [
    {
      "campaign_id": "23456789",
      "campaign_name": "Test Campaign 1",
      "spend": 100.5,
      "impressions": 10000,
      "reach": 8000,
      "clicks": 150,
      "ctr": 0.015
    }
  ],
  "summary": {
    "total_spend": 100.5,
    "total_impressions": 10000,
    "total_reach": 8000
  }
}
```

### GET /campaign_metrics_csv

Retrieves campaign metrics in CSV format.

**Endpoint:** `/facebook/campaign_metrics_csv`

**Parameters:**

- `ad_account_id` (required): ID of the Facebook Ad Account
- `metrics` (required): Comma-separated list of metrics
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `dimensions` (optional): Comma-separated list of dimensions (e.g., age, gender)

**Test Data:**

```json
{
  "ad_account_id": "act_123456789",
  "metrics": "spend,impressions,reach,clicks,ctr",
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "dimensions": "age,gender"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/facebook/campaign_metrics_csv?ad_account_id=act_123456789&metrics=spend,impressions,reach&start_date=2024-03-01&end_date=2024-03-31" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Post Metrics

### GET /post_metrics

Retrieves metrics for Facebook posts.

**Endpoint:** `/facebook/post_metrics`

**Parameters:**

- `page_id` (required): ID of the Facebook Page
- `post_ids` (optional): Comma-separated list of post IDs
- `metrics` (optional): Comma-separated list of metrics
  - Default: `impressions,reach,engaged_users,reactions`
- `since_date` (required): Start date (YYYY-MM-DD)
- `until_date` (required): End date (YYYY-MM-DD)
- `access_token` (required): Facebook access token

**Test Data:**

```json
{
  "page_id": "123456789",
  "post_ids": "123_456,123_457",
  "metrics": "impressions,reach,engaged_users,reactions",
  "since_date": "2024-03-01",
  "until_date": "2024-03-31",
  "access_token": "YOUR_ACCESS_TOKEN"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/facebook/post_metrics?page_id=123456789&metrics=impressions,reach&since_date=2024-03-01&until_date=2024-03-31" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### GET /post_metrics_csv

Retrieves post metrics in CSV format.

**Endpoint:** `/facebook/post_metrics_csv`

**Parameters:**

- `page_id` (required): ID of the Facebook Page
- `metrics` (required): Comma-separated list of metrics
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

**Test Data:**

```json
{
  "page_id": "123456789",
  "metrics": "post_impressions,post_reach,post_engaged_users",
  "start_date": "2024-03-01",
  "end_date": "2024-03-31"
}
```

## Reel Metrics

### GET /reel_metrics

Retrieves metrics for Facebook reels.

**Endpoint:** `/facebook/reel_metrics`

**Parameters:**

- `page_id` (required): ID of the Facebook Page
- `reel_ids` (optional): Comma-separated list of reel IDs
- `metrics` (optional): Comma-separated list of metrics
  - Default: See [Available Metrics](#available-metrics)
- `since_date` (required): Start date (YYYY-MM-DD)
- `until_date` (required): End date (YYYY-MM-DD)
- `access_token` (required): Facebook access token

**Test Data:**

```json
{
  "page_id": "123456789",
  "metrics": "video_total_views,video_avg_time_watched,video_view_time",
  "since_date": "2024-03-01",
  "until_date": "2024-03-31",
  "access_token": "YOUR_ACCESS_TOKEN"
}
```

### GET /reel_metrics_csv

Retrieves reel metrics in CSV format.

**Endpoint:** `/facebook/reel_metrics_csv`

**Parameters:**

- `page_id` (required): ID of the Facebook Page
- `metrics` (required): Comma-separated list of metrics
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

**Test Data:**

```json
{
  "page_id": "123456789",
  "metrics": "video_total_views,video_avg_time_watched,video_view_time",
  "start_date": "2024-03-01",
  "end_date": "2024-03-31"
}
```

## Utility Endpoints

### GET /available_metrics

Returns lists of available metrics for different Facebook content types.

**Endpoint:** `/facebook/available_metrics`

**Example Request:**

```bash
curl -X GET "https://api.example.com/facebook/available_metrics" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**

```json
{
  "post_metrics": [
    "post_impressions",
    "post_reach",
    "post_engaged_users",
    "post_reactions_by_type_total"
  ],
  "reel_metrics": [
    "video_total_views",
    "video_avg_time_watched",
    "video_view_time"
  ],
  "campaign_metrics": ["spend", "impressions", "reach", "clicks", "ctr"]
}
```

### GET /debug_token

Debugs a Facebook access token.

**Endpoint:** `/facebook/debug_token`

**Parameters:**

- `token` (required): Facebook access token to debug

**Example Request:**

```bash
curl -X GET "https://api.example.com/facebook/debug_token?token=YOUR_ACCESS_TOKEN" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### GET /check_business_pages_access

Checks access to all pages in a business.

**Endpoint:** `/facebook/check_business_pages_access`

**Parameters:**

- `business_id` (required): ID of the Facebook Business

**Test Data:**

```json
{
  "business_id": "675341657897354"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/facebook/check_business_pages_access?business_id=675341657897354" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Available Metrics

### Post Metrics

- post_impressions
- post_reach
- post_engaged_users
- post_reactions_by_type_total
- post_clicks
- post_negative_feedback

### Reel Metrics

- video_total_views
- video_avg_time_watched
- video_view_time
- video_views_paid
- video_views_organic
- video_view_time_organic
- video_view_time_paid

### Campaign Metrics

- spend
- impressions
- reach
- clicks
- ctr
- cost_per_inline_link_click
- cost_per_inline_post_engagement

## Error Responses

All endpoints may return the following error responses:

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

1. All dates should be in YYYY-MM-DD format
2. The end date must be after or equal to the start date
3. Access tokens must have appropriate permissions for the requested data
4. CSV responses include a BOM character for Excel compatibility
5. All CSV files use UTF-8 encoding
