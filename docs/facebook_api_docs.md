# Facebook API Documentation

## Overview

The Facebook API module provides a comprehensive set of endpoints for retrieving metrics and insights from Facebook Pages, Posts, Reels, and Ad Campaigns. The API is built using FastAPI and integrates with the official Facebook Business SDK to fetch data from the Facebook Graph API.

This documentation provides details on each available endpoint, including request parameters, response formats, example requests, and implementation details.

## Core Features

- Fetch post insights for Facebook Business Pages
- Export metrics data in CSV format for easy analysis
- Support for Facebook Reels metrics
- Campaign metrics for Facebook Ads
- Authentication and access token management
- Debug Facebook access tokens

## API Endpoints

### Business Post Insights

#### `GET /business_post_insights_csv`

Retrieves post insights for a Facebook Business Page and returns the data in CSV format.

**Request Parameters:**

- `business_id` (required): ID of the Facebook Business
- `metrics` (optional, default: "impressions,reach,engaged_users,reactions"): Comma-separated list of metrics to retrieve
- `since_date` (required): Start date in YYYY-MM-DD format
- `until_date` (required): End date in YYYY-MM-DD format

**Response:**

- Content-Type: text/csv
- Streaming response with CSV data containing post ID, creation time, message, type, and requested metrics

**Implementation Details:**

- Connects to Facebook Business API using app credentials
- Retrieves all pages owned by the business
- For each page, fetches all posts within the date range
- For each post, retrieves the requested metrics
- Combines all data into a CSV file with appropriate headers

**Example Usage:**

```
GET /business_post_insights_csv?business_id=123456789&metrics=impressions,reach,clicks&since_date=2023-01-01&until_date=2023-01-31
```

### Business Posts and Reels Insights

#### `GET /business_posts_and_reels_insights_csv`

Retrieves combined insights for both regular posts and reels from a Facebook Business Page and returns the data in CSV format.

**Request Parameters:**

- `business_id` (required): ID of the Facebook Business
- `post_metrics` (optional, default: "impressions,reach,engaged_users"): Comma-separated list of metrics for regular posts
- `reel_metrics` (optional, default: DEFAULT_REEL_METRICS): Comma-separated list of metrics for reels
- `since_date` (required): Start date in YYYY-MM-DD format
- `until_date` (required): End date in YYYY-MM-DD format

**Response:**

- Content-Type: text/csv
- Streaming response with CSV data containing post ID, creation time, message, type, and all requested metrics

**Implementation Details:**

- Validates provided metrics against available metrics for posts and reels
- Retrieves all posts and reels for all pages owned by the business
- Distinguishes between regular posts and reels
- Applies appropriate metrics to each content type
- Combines all data into a single CSV export

**Example Usage:**

```
GET /business_posts_and_reels_insights_csv?business_id=123456789&post_metrics=impressions,reach&reel_metrics=plays,comments&since_date=2023-01-01&until_date=2023-01-31
```

### Campaign Metrics

#### `GET /campaign_metrics`

Retrieves metrics for Facebook Ad Campaigns and returns structured JSON data.

**Request Parameters:**

- `ad_account_id` (required): ID of the Facebook Ad Account
- `campaign_ids` (optional): Comma-separated list of campaign IDs
- `metrics` (optional, default: "spend,impressions,reach,clicks,ctr"): Comma-separated list of metrics
- `since_date` (required): Start date in YYYY-MM-DD format
- `until_date` (required): End date in YYYY-MM-DD format
- `access_token` (required): Facebook access token with ads_read permission

**Response:**

- Content-Type: application/json
- JSON object with the following structure:
  ```json
  {
    "success": true,
    "message": "Campaign metrics retrieved successfully",
    "data": [...],  // Array of campaign metrics
    "summary": {...}  // Summary of metrics across all campaigns
  }
  ```

**Implementation Details:**

- Uses the Facebook Ads API to retrieve campaign insights
- Supports filtering by specific campaign IDs
- Calculates summary metrics by aggregating data across all campaigns
- Handles error cases with appropriate error messages

**Example Usage:**

```
GET /campaign_metrics?ad_account_id=act_123456789&metrics=spend,impressions,cpc&since_date=2023-01-01&until_date=2023-01-31&access_token=EAA...
```

### Campaign Metrics CSV

#### `GET /campaign_metrics_csv`

Similar to `/campaign_metrics` but returns the data in CSV format for easy export.

**Request Parameters:**

- Same as `/campaign_metrics`

**Response:**

- Content-Type: text/csv
- Streaming response with CSV data containing campaign details and metrics

**Implementation Details:**

- Uses the same service methods as `/campaign_metrics`
- Formats the data into CSV with appropriate headers
- Adds a summary row at the end of the CSV

**Example Usage:**

```
GET /campaign_metrics_csv?ad_account_id=act_123456789&metrics=spend,impressions,cpc&since_date=2023-01-01&until_date=2023-01-31&access_token=EAA...
```

### Post Metrics

#### `GET /post_metrics`

Retrieves metrics for specific Facebook posts.

**Request Parameters:**

- `page_id` (required): ID of the Facebook Page
- `post_ids` (optional): Comma-separated list of post IDs
- `metrics` (optional, default: "impressions,reach,engaged_users,reactions"): Comma-separated list of metrics
- `since_date` (required): Start date in YYYY-MM-DD format
- `until_date` (required): End date in YYYY-MM-DD format
- `access_token` (required): Facebook access token with page insights permission

**Response:**

- Content-Type: application/json
- JSON object with the following structure:
  ```json
  {
    "success": true,
    "message": "Post metrics retrieved successfully",
    "data": [...],  // Array of post metrics
    "summary": {...}  // Summary of metrics across all posts
  }
  ```

**Implementation Details:**

- If post_ids are provided, fetches metrics only for those specific posts
- If post_ids are not provided, fetches all posts within the date range
- Uses the Facebook Graph API to retrieve post insights
- Calculates summary metrics across all posts

**Example Usage:**

```
GET /post_metrics?page_id=123456789&post_ids=111,222,333&metrics=impressions,reach&since_date=2023-01-01&until_date=2023-01-31&access_token=EAA...
```

### Post Metrics CSV

#### `GET /post_metrics_csv`

Similar to `/post_metrics` but returns the data in CSV format for easy export.

**Request Parameters:**

- Same as `/post_metrics`

**Response:**

- Content-Type: text/csv
- Streaming response with CSV data containing post details and metrics

**Implementation Details:**

- Uses the same service methods as `/post_metrics`
- Formats the data into CSV with appropriate headers
- Adds a summary row at the end of the CSV

**Example Usage:**

```
GET /post_metrics_csv?page_id=123456789&post_ids=111,222,333&metrics=impressions,reach&since_date=2023-01-01&until_date=2023-01-31&access_token=EAA...
```

### Reel Metrics

#### `GET /reel_metrics`

Retrieves metrics specific to Facebook Reels.

**Request Parameters:**

- `page_id` (required): ID of the Facebook Page
- `reel_ids` (optional): Comma-separated list of reel IDs
- `metrics` (optional, default: DEFAULT_REEL_METRICS): Comma-separated list of metrics specific to reels
- `since_date` (required): Start date in YYYY-MM-DD format
- `until_date` (required): End date in YYYY-MM-DD format
- `access_token` (required): Facebook access token with page insights permission

**Response:**

- Content-Type: application/json
- JSON object with the following structure:
  ```json
  {
    "success": true,
    "message": "Reel metrics retrieved successfully",
    "data": [...],  // Array of reel metrics
    "summary": {...}  // Summary of metrics across all reels
  }
  ```

**Implementation Details:**

- Identifies reels by filtering posts with type "reel"
- Uses specialized reel metrics available in the Facebook API
- Handles the different structure of reel insights compared to regular posts

**Example Usage:**

```
GET /reel_metrics?page_id=123456789&metrics=plays,comments,shares&since_date=2023-01-01&until_date=2023-01-31&access_token=EAA...
```

### Reel Metrics CSV

#### `GET /reel_metrics_csv`

Similar to `/reel_metrics` but returns the data in CSV format for easy export.

**Request Parameters:**

- Same as `/reel_metrics`

**Response:**

- Content-Type: text/csv
- Streaming response with CSV data containing reel details and metrics

**Implementation Details:**

- Uses the same service methods as `/reel_metrics`
- Formats the data into CSV with appropriate headers
- Adds a summary row at the end of the CSV

**Example Usage:**

```
GET /reel_metrics_csv?page_id=123456789&metrics=plays,comments,shares&since_date=2023-01-01&until_date=2023-01-31&access_token=EAA...
```

### Available Metrics

#### `GET /available_metrics`

Returns a list of all available metrics that can be used with the API.

**Request Parameters:**

- None

**Response:**

- Content-Type: application/json
- JSON object with the following structure:
  ```json
  {
    "post_metrics": [...],  // Array of available post metrics
    "reel_metrics": [...],  // Array of available reel metrics
    "ads_metrics": [...]    // Array of available ads metrics
  }
  ```

**Implementation Details:**

- Returns constants defined in the application
- Helps users understand which metrics are available for different content types

**Example Usage:**

```
GET /available_metrics
```

### Debug Token

#### `GET /debug_token`

Provides debug information about a Facebook access token.

**Request Parameters:**

- `token` (required): Facebook access token to debug

**Response:**

- Content-Type: application/json
- JSON object containing token information:
  ```json
  {
    "app_id": "123456789",
    "application": "My App",
    "expires_at": "2023-12-31T23:59:59",
    "is_valid": true,
    "scopes": ["email", "public_profile", "pages_show_list"],
    "user_id": "987654321"
  }
  ```

**Implementation Details:**

- Uses the Facebook debug_token API
- Useful for verifying token validity and permissions
- Shows token expiration date and associated app

**Example Usage:**

```
GET /debug_token?token=EAA...
```

### Check Business Pages Access

#### `GET /check_business_pages_access`

Checks access to pages owned by a Facebook Business.

**Request Parameters:**

- `business_id` (required): ID of the Facebook Business

**Response:**

- Content-Type: application/json
- JSON array of page information:
  ```json
  [
    {
      "id": "123456789",
      "name": "My Facebook Page",
      "access_token": "EAA...",
      "category": "Business",
      "has_insights_access": true
    },
    ...
  ]
  ```

**Implementation Details:**

- Retrieves all pages owned by the business
- Tests if the current access token has insights access for each page
- Useful for verifying permissions before attempting to retrieve metrics

**Example Usage:**

```
GET /check_business_pages_access?business_id=123456789
```

## Data Models

### PostInsight

```python
class PostInsight(BaseModel):
    post_id: str
    created_time: datetime
    message: Optional[str]
    type: str
    metrics: Dict[str, Any]
```

### VideoInsight

```python
class VideoInsight(BaseModel):
    video_id: str
    title: Optional[str]
    description: Optional[str]
    created_time: datetime
    metrics: Dict[str, Any]
```

### AdsInsight

```python
class AdsInsight(BaseModel):
    account_id: str
    campaign_id: Optional[str]
    campaign_name: Optional[str]
    adset_id: Optional[str]
    adset_name: Optional[str]
    ad_id: Optional[str]
    ad_name: Optional[str]
    metrics: Dict[str, Any]
    dimensions: Dict[str, Any]
```

### TokenDebugInfo

```python
class TokenDebugInfo(BaseModel):
    app_id: str
    application: str
    expires_at: Optional[datetime]
    is_valid: bool
    scopes: List[str]
    user_id: str
```

### BusinessPage

```python
class BusinessPage(BaseModel):
    id: str
    name: str
    access_token: str
    category: Optional[str]
    has_insights_access: bool
```

### FacebookMetricsResponse

```python
class FacebookMetricsResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None
```

## Error Handling

All API endpoints implement consistent error handling:

1. **Input Validation Errors** (HTTP 400)

   - Invalid date formats
   - Invalid metrics
   - Missing required parameters

2. **Authentication Errors** (HTTP 401)

   - Invalid access token
   - Expired access token
   - Insufficient permissions

3. **Facebook API Errors** (HTTP 400)

   - Wrapped Facebook API error responses with clear messages

4. **Server Errors** (HTTP 500)
   - Unexpected exceptions with logging

## Implementation Services

The API endpoints are backed by several service classes:

1. **FacebookApiManager**

   - Core service for interacting with Facebook Graph API
   - Handles initialization and authentication
   - Provides methods for fetching post and reel insights

2. **FacebookAdsService**

   - Specialized service for Facebook Ads API
   - Retrieves campaign, ad set, and ad metrics
   - Handles pagination and data aggregation

3. **FacebookAuthService**
   - Manages authentication and token validation
   - Handles token refreshing when needed

## Caching Strategy

To optimize performance and reduce API calls to Facebook:

1. Short-term caching (5 minutes) for post and reel data
2. Medium-term caching (1 hour) for campaign metrics
3. Long-term caching (24 hours) for static data like available metrics

## Security Considerations

1. Access tokens are never stored in logs
2. Token validation before processing any request
3. Rate limiting to prevent abuse
4. Input validation to prevent injection attacks

## Usage Examples

### Fetching Post Insights for a Business

```python
import requests

url = "https://api.example.com/facebook/business_post_insights_csv"
params = {
    "business_id": "123456789",
    "metrics": "impressions,reach,engagement",
    "since_date": "2023-01-01",
    "until_date": "2023-01-31"
}

response = requests.get(url, params=params)
with open("post_insights.csv", "wb") as f:
    f.write(response.content)
```

### Fetching Campaign Metrics

```python
import requests
import json

url = "https://api.example.com/facebook/campaign_metrics"
params = {
    "ad_account_id": "act_123456789",
    "metrics": "spend,impressions,clicks,ctr",
    "since_date": "2023-01-01",
    "until_date": "2023-01-31",
    "access_token": "EAA..."
}

response = requests.get(url, params=params)
data = response.json()
print(json.dumps(data, indent=2))
```
