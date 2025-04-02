# Digital Metrics API Endpoints

This document provides detailed information about all available API endpoints in the Digital Metrics API.

## Table of Contents

- [Facebook Endpoints](#facebook-endpoints)
- [Google Ads Endpoints](#google-ads-endpoints)
- [Authentication Endpoints](#authentication-endpoints)

## Facebook Endpoints

### GET /api/v1/facebook/business_post_insights_csv

Get post insights for a business in CSV format.

**Query Parameters:**

- `business_id` (required): ID of the business
- `metrics` (default: "impressions,reach,engaged_users,reactions"): Comma-separated list of metrics
- `since_date` (required): Start date (YYYY-MM-DD)
- `until_date` (required): End date (YYYY-MM-DD)

**Response:**

- Content-Type: text/csv
- CSV file with headers: post_id, created_time, message, type, [selected metrics]

### GET /api/v1/facebook/business_posts_and_reels_insights_csv

Get combined post and reel insights for a business in CSV format.

**Query Parameters:**

- `business_id` (required): ID of the business
- `post_metrics` (default: "impressions,reach,engaged_users"): Comma-separated list of post metrics
- `reel_metrics` (default: [DEFAULT_REEL_METRICS]): Comma-separated list of reel metrics
- `since_date` (required): Start date (YYYY-MM-DD)
- `until_date` (required): End date (YYYY-MM-DD)

**Response:**

- Content-Type: text/csv
- CSV file with headers: post_id, created_time, message, type, [selected post metrics], [selected reel metrics]

### GET /api/v1/facebook/campaign_metrics

Get metrics of campaigns from Facebook Ads.

**Query Parameters:**

- `ad_account_id` (required): ID của tài khoản quảng cáo
- `campaign_ids` (optional): Danh sách campaign IDs (phân cách bằng dấu phẩy)
- `metrics` (default: "spend,impressions,reach,clicks,ctr"): Comma-separated list of metrics
- `since_date` (required): Start date (YYYY-MM-DD)
- `until_date` (required): End date (YYYY-MM-DD)
- `access_token` (required): Facebook access token

**Response:**

- Content-Type: application/json
- FacebookMetricsResponse object containing metrics data and summary

### GET /api/v1/facebook/campaign_metrics_csv

Get campaign metrics in CSV format.

**Query Parameters:**

- `ad_account_id` (required): ID của tài khoản quảng cáo
- `campaign_ids` (optional): Danh sách campaign IDs (phân cách bằng dấu phẩy)
- `metrics` (default: "spend,impressions,reach,clicks,ctr"): Comma-separated list of metrics
- `since_date` (required): Start date (YYYY-MM-DD)
- `until_date` (required): End date (YYYY-MM-DD)
- `access_token` (required): Facebook access token

**Response:**

- Content-Type: text/csv
- CSV file with campaign metrics data

### GET /api/v1/facebook/available_metrics

Get list of available Facebook metrics.

**Response:**

- Content-Type: application/json
- Object containing post_metrics, reel_metrics lists

### GET /api/v1/facebook/debug_token

Debug and display information about a Facebook access token.

**Query Parameters:**

- `token` (required): Facebook access token to debug

**Response:**

- Content-Type: application/json
- Token debug information

### GET /api/v1/facebook/check_business_pages_access

Check access permissions for a business's pages.

**Query Parameters:**

- `business_id` (required): ID of the business to check

**Response:**

- Content-Type: application/json
- Access information for the business's pages

## Google Ads Endpoints

### GET /api/v1/google/campaigns_csv

Get campaign insights in CSV format.

**Query Parameters:**

- `client_id` (required): ID of the Google Ads client
- `metrics` (default: DEFAULT_GOOGLE_ADS_METRICS): Comma-separated list of metrics
- `dimensions` (default: DEFAULT_GOOGLE_ADS_DIMENSIONS): Comma-separated list of dimensions
- `date_range` (default: 'LAST_30_DAYS'): Date range for the report

**Response:**

- Content-Type: text/csv
- CSV file with campaign insights data

### GET /api/v1/google/ad_groups_csv

Get ad group insights in CSV format.

**Query Parameters:**

- `client_id` (required): ID of the Google Ads client
- `metrics` (default: DEFAULT_GOOGLE_ADS_METRICS): Comma-separated list of metrics
- `dimensions` (default: DEFAULT_GOOGLE_ADS_DIMENSIONS): Comma-separated list of dimensions
- `date_range` (default: 'LAST_30_DAYS'): Date range for the report

**Response:**

- Content-Type: text/csv
- CSV file with ad group insights data

### GET /api/v1/google/available_metrics

Get list of available Google Ads metrics.

**Response:**

- Content-Type: application/json
- Object containing metrics list and default_metrics

### GET /api/v1/google/available_dimensions

Get list of available Google Ads dimensions.

**Response:**

- Content-Type: application/json
- Object containing dimensions list and default_dimensions

## Authentication Endpoints

### GET /api/v1/auth/facebook/callback

Callback endpoint for Facebook OAuth authentication.

**Query Parameters:**

- `code` (required): Authorization code from Facebook
- `state` (optional): State parameter for CSRF protection

**Response:**

- Content-Type: application/json
- Token information including user_id, token_type, expires_at, and scopes

### GET /api/v1/auth/facebook/validate

Validate a Facebook access token.

**Query Parameters:**

- `token` (required): Facebook access token to validate

**Response:**

- Content-Type: application/json
- TokenValidationResponse with token information

### GET /api/v1/auth/facebook/user-pages

Get list of pages that a user has access to.

**Query Parameters:**

- `token` (required): Facebook user access token

**Response:**

- Content-Type: application/json
- List of FacebookPageToken objects

### POST /api/v1/auth/facebook/refresh

Refresh a Facebook access token.

**Query Parameters:**

- `token` (required): Facebook token to refresh

**Response:**

- Content-Type: application/json
- TokenRefreshResponse with information about the new token

### POST /api/v1/auth/facebook/refresh-token

### GET /api/v1/auth/facebook/refresh-token

Force refresh Facebook tokens and start a background task.

**Response:**

- Content-Type: application/json
- Status information about the refresh operation

### POST /api/v1/auth/facebook/encrypt-tokens

Encrypt stored Facebook tokens.

**Response:**

- Content-Type: application/json
- Status information about the encryption operation

### POST /api/v1/auth/facebook/internal/scheduled-refresh

Scheduled token refresh endpoint (internal use).

**Query Parameters:**

- `hours_threshold` (default: 24): Number of hours before token expiration to refresh
- `api_key` (required): Internal API key for authentication

**Response:**

- Content-Type: application/json
- Status information about the scheduled refresh operation
