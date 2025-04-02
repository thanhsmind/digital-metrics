# Testing Facebook APIs

This directory contains documentation and test data for the Digital Metrics Facebook APIs.

## Files

- `facebook_endpoints.md` - Comprehensive documentation of all Facebook endpoints
- `facebook_api_collection.json` - Postman collection for testing the APIs

## Getting Started

1. Import the Postman collection:

   - Open Postman
   - Click "Import"
   - Select `facebook_api_collection.json`
   - The collection will be imported with all endpoints configured

2. Configure environment variables:

   - Create a new environment in Postman
   - Set the following variables:
     - `base_url`: Your API base URL (e.g., `http://localhost:8000`)
     - `access_token`: Your Facebook access token

3. Test the endpoints:

   1. Start with utility endpoints:

      - Use `/facebook/debug_token` to verify your access token
      - Use `/facebook/check_business_pages_access` to verify business access
      - Use `/facebook/available_metrics` to see available metrics

   2. Test business insights:

      - Use business post insights endpoints with your business ID
      - Test both regular endpoints and CSV exports

   3. Test campaign metrics:
      - Use campaign metrics endpoints with your ad account ID
      - Test both JSON and CSV responses

## Test Data

Sample IDs for testing (replace with your actual IDs):

```json
{
  "business_id": "675341657897354",
  "page_id": "123456789",
  "ad_account_id": "act_123456789",
  "campaign_ids": ["23456789", "34567890"],
  "post_ids": ["123_456", "123_457"]
}
```

## Common Metrics

### Post Metrics

- post_impressions
- post_reach
- post_engaged_users
- post_reactions_by_type_total

### Reel Metrics

- video_total_views
- video_avg_time_watched
- video_view_time

### Campaign Metrics

- spend
- impressions
- reach
- clicks
- ctr

## Error Handling

The APIs use standard HTTP status codes:

- 400: Bad Request (invalid parameters)
- 401: Unauthorized (invalid token)
- 403: Forbidden (insufficient permissions)
- 500: Internal Server Error

Error responses include a detail message explaining the issue.

## Notes

1. All date parameters should be in YYYY-MM-DD format
2. CSV responses include a BOM character for Excel compatibility
3. All CSV files use UTF-8 encoding
4. Access tokens must have appropriate permissions for the requested data

## Troubleshooting

1. Invalid token errors:

   - Verify token using `/facebook/debug_token`
   - Check token permissions
   - Ensure token hasn't expired

2. No data in responses:

   - Verify date range
   - Check if metrics are valid
   - Ensure IDs are correct
   - Verify permissions for the requested data

3. CSV encoding issues:
   - Ensure your application handles UTF-8 with BOM
   - For Excel, open the file directly rather than importing
