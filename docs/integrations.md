# Digital Metrics API Integrations

This document provides detailed information about the external service integrations used in the Digital Metrics API.

## Table of Contents

- [Facebook Integration](#facebook-integration)
  - [Overview](#facebook-overview)
  - [Services](#facebook-services)
  - [Data Models](#facebook-data-models)
  - [Authentication Flow](#facebook-authentication-flow)
  - [Key Functionality](#facebook-key-functionality)
- [Google Ads Integration](#google-ads-integration)
  - [Overview](#google-ads-overview)
  - [Services](#google-ads-services)
  - [Data Models](#google-ads-data-models)
  - [Authentication](#google-ads-authentication)
  - [Key Functionality](#google-ads-key-functionality)

## Facebook Integration

### Facebook Overview

The Facebook integration allows the Digital Metrics API to interact with the Facebook Marketing API to retrieve insights and metrics for Facebook posts, reels, and advertising campaigns. This integration enables businesses to analyze their Facebook marketing performance through a standardized API.

### Facebook Services

#### FacebookApiManager

Located in `src/services/facebook/api.py`, this service handles interaction with the Facebook Graph API for retrieving post and page insights.

Key methods:

- `get_business_post_insights`: Retrieves insights for all posts from all pages in a business
- `get_post_insights`: Gets insights for a specific post
- `get_business_pages`: Retrieves all pages owned by a business
- `debug_token`: Debugs a Facebook access token to verify its validity and permissions

#### FacebookAdsService

Located in `src/services/facebook/ads_service.py`, this service handles interaction with the Facebook Ads API for advertising metrics.

Key functionality:

- Retrieving campaign metrics
- Generating CSV reports for campaign performance
- Analyzing ad account performance

#### FacebookAuthService

Located in `src/services/facebook/auth_service.py`, this service manages Facebook authentication.

Key functionality:

- OAuth authentication flow
- Token exchange and validation
- Page access token management
- Permission verification

#### TokenManager

Located in `src/services/facebook/token_manager.py`, this service handles the storage, retrieval, and management of Facebook access tokens.

Key functionality:

- Token encryption and decryption
- Token storage in JSON files
- Token refresh management
- Token validation and debugging

### Facebook Data Models

Located in `src/models/facebook.py`, these models define the data structures used for Facebook API integration:

- `PageToken`: Represents a Facebook page access token
- `PostInsight`: Contains metrics and information about a Facebook post
- `VideoInsight`: Contains metrics and information about a Facebook video
- `AdsInsight`: Contains metrics for Facebook ads
- `TokenDebugInfo`: Contains information about a Facebook token
- `BusinessPage`: Represents a Facebook business page with access information
- `FacebookMetricsRequest`: Model for requesting Facebook metrics
- `FacebookCampaignMetricsRequest`: Model for requesting Facebook campaign metrics
- `FacebookMetricsResponse`: Response model for Facebook metrics

Additional authentication models in `src/models/auth.py`:

- `FacebookUserToken`: Represents a user access token
- `FacebookPageToken`: Contains page token information
- `TokenValidationResponse`: Response for token validation
- `TokenRefreshResponse`: Response for token refresh operations

### Facebook Authentication Flow

1. The user initiates authentication through the `/api/v1/auth/facebook/callback` endpoint
2. The API exchanges the authorization code for an access token using the `exchange_code_for_token` method
3. Token information is stored using the `TokenManager` service
4. The API validates the token and its permissions
5. For page access, the API retrieves page tokens using the `get_user_pages` method
6. Tokens are refreshed before expiration using background tasks

### Facebook Key Functionality

1. **Business Post Insights**: Retrieves performance metrics for posts from business pages
2. **Post and Reel Insights**: Combines metrics for both regular posts and reels
3. **Campaign Metrics**: Analyzes advertising campaign performance
4. **Token Management**: Secures and manages access tokens
5. **Permission Verification**: Validates proper access to requested resources

## Google Ads Integration

### Google Ads Overview

The Google Ads integration allows the Digital Metrics API to connect with the Google Ads API to retrieve campaign, ad group, and ad performance metrics. This integration enables businesses to analyze their Google advertising performance through a standardized API.

### Google Ads Services

#### GoogleAdsManager

Located in `src/services/google/api.py`, this service handles interaction with the Google Ads API.

Key methods:

- `get_campaign_insights`: Retrieves metrics for Google Ads campaigns
- `get_ad_group_insights`: Gets metrics for ad groups within campaigns
- `store_client_token`: Manages client token storage
- `get_client_token`: Retrieves client tokens
- `_build_query`: Creates GAQL (Google Ads Query Language) queries
- `_extract_metrics` and `_extract_dimensions`: Parse metrics and dimensions from API responses

### Google Ads Data Models

Located in `src/models/google.py`, these models define the data structures for Google Ads API integration:

- `CampaignInsight`: Contains metrics and information about a Google Ads campaign
- `AdGroupInsight`: Contains metrics and information about an ad group
- `AdInsight`: Contains metrics for individual ads
- `GoogleAdsConfig`: Configuration for Google Ads API
- `GoogleMetricsRequest`: Model for requesting Google Ads metrics
- `AdGroupPerformance`: Performance metrics for ad groups
- `CampaignPerformance`: Performance metrics for campaigns
- `GoogleAdsReport`: Comprehensive report containing campaign and ad group performance

### Google Ads Authentication

The Google Ads integration uses the following authentication approach:

1. Configuration is loaded from a YAML file specified in settings (`settings.GOOGLE_ADS_CONFIG_FILE`)
2. Client tokens are encrypted and stored in a JSON file (`settings.GOOGLE_TOKEN_FILE`)
3. The `TokenEncryption` utility is used to secure client tokens
4. The integration supports managing multiple client accounts through client_id-based token storage

### Google Ads Key Functionality

1. **Campaign Insights**: Retrieves performance metrics for advertising campaigns
2. **Ad Group Insights**: Analyzes performance at the ad group level
3. **Metrics and Dimensions**: Supports a wide range of metrics (impressions, clicks, conversions) and dimensions (device, date, location)
4. **CSV Export**: Provides data in CSV format for easy analysis
5. **Client Management**: Supports multiple client accounts with separate authentication
