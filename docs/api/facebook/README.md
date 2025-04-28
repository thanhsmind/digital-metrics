# Facebook API Documentation

## Overview

This directory contains comprehensive documentation for the Facebook API endpoints in the Digital Metrics application. The documentation covers business insights, campaign metrics, and utility endpoints.

## Directory Structure

```
docs/api/facebook/
├── endpoints/
│   ├── business-insights.md
│   ├── campaign-metrics.md
│   └── utility.md
├── postman/
│   └── facebook_api_collection.json
├── guides/
│   └── testing.md
└── README.md
```

## Documentation Contents

### Endpoint Documentation

1. [Business Insights](endpoints/business-insights.md)

   - GET /business_post_insights_csv
   - GET /business_posts_and_reels_insights_csv

2. [Campaign Metrics](endpoints/campaign-metrics.md)

   - GET /campaign_metrics
   - GET /campaign_metrics_csv

3. [Utility Endpoints](endpoints/utility.md)
   - GET /available_metrics
   - GET /debug_token
   - GET /check_business_pages_access

### Reference Guides

1. [Metrics Guide](guides/metrics-guide.md)
   - Default metrics
   - Available metrics
   - Usage examples

### Testing Resources

1. [Postman Collection](postman/facebook_api_collection.json)

   - Ready-to-use requests for all endpoints
   - Environment variables configuration
   - Example test data

2. [Testing Guide](guides/testing.md)
   - Setup instructions
   - Test data samples
   - Common test cases
   - Error handling tests
   - Performance testing guidelines
   - Troubleshooting tips

## Quick Start

1. Review the endpoint documentation in the `endpoints/` directory
2. Import the Postman collection from `postman/facebook_api_collection.json`
3. Follow the testing guide in `guides/testing.md`

## Authentication

All endpoints require a valid Facebook access token with appropriate permissions:

- `ads_read` for campaign metrics
- `pages_read_engagement` for post and reel insights
- `pages_show_list` for page access
- `business_management` for business-level operations

## Common Features

1. **CSV Generation**

   - UTF-8 encoding with BOM
   - Dynamic headers based on requested metrics
   - Proper handling of special characters

2. **Date Handling**

   - All dates in YYYY-MM-DD format
   - Automatic timezone conversion
   - Date range validation

3. **Error Handling**

   - Consistent error response format
   - Detailed error messages
   - HTTP status code mapping

4. **Rate Limiting**
   - Respects Facebook API rate limits
   - Implements exponential backoff
   - Clear rate limit error messages

## Best Practices

1. **Token Management**

   - Regularly refresh access tokens
   - Store tokens securely
   - Monitor token expiration

2. **Performance**

   - Use appropriate date ranges
   - Request only needed metrics
   - Implement caching when possible

3. **Error Handling**

   - Implement proper error handling
   - Log all API errors
   - Monitor error rates

4. **Testing**
   - Follow testing sequence
   - Use provided test data
   - Monitor API responses

## Support

For issues and questions:

1. Review the [Testing Guide](guides/testing.md)
2. Check Facebook Marketing API documentation
3. Contact the development team
4. Submit issues through the project repository

## Updates

The documentation is maintained alongside the codebase. For the latest updates:

1. Check the repository's commit history
2. Review Facebook Marketing API changelog
3. Monitor documentation updates
4. Follow team announcements
