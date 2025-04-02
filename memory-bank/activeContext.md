# Active Context

## Current Focus

- **Task:** Refactor endpoint `GET /business_posts_and_reels_insights_csv`
- **Objective:** Update the endpoint to use the correct service method, CSV utility, dependency injection, and handle combined post/reel data for CSV output.
- **Status:** Starting planning.

- **Task:** Implement CSV generation logic
- **Objective:** Create a reusable utility function in `app/utils/` to generate CSV `StreamingResponse` from lists of data, handling headers and BOM.
- **Status:** Starting planning.

- **Task:** Implement `get_all_business_posts_and_reels_insights` in `FacebookAdsService`
- **Objective:** Implement method to fetch both post and reel insights across all business pages concurrently, aggregating results separately.
- **Status:** Starting implementation planning.

- **Task:** Update PostInsight model
- **Objective:** Verify and potentially update the `PostInsight` model (`app/models/facebook.py`) for the Facebook Business Post Insights feature, ensuring it meets requirements and has adequate documentation (docstrings, examples).
- **Status:** Starting verification and planning.

- **Task:** Implement GET /available_metrics endpoint
- **Objective:** Create the FastAPI endpoint to return lists of available Facebook metrics for posts, reels, and ads, potentially using cached constants.
- **Status:** Starting implementation.

## Recent Changes

- Fixed JWEError import in encryption.py by replacing it with JOSEError
- Added ConfigError class to app.utils.errors module to fix import error
- Replaced Redis with JSON file-based cache storage
- Fixed virtual environment setup issue by recreating it with virtualenv
- Implemented Facebook Reel metrics retrieval functionality
- Added get_reel_metrics method to FacebookAdsService
- Added /facebook/reel_metrics and /facebook/reel_metrics_csv endpoints
- Implemented Facebook Post metrics retrieval functionality
- Added get_post_metrics method to FacebookAdsService
- Added /facebook/post_metrics and /facebook/post_metrics_csv endpoints
- Documented all external integrations (Facebook, Google Ads)
- Documented all existing API endpoints
- Memory Bank initialization
- Project structure documentation
- Technical context updates
- Environment configuration setup

## Recent Completions

- Refactored endpoint `GET /business_posts_and_reels_insights_csv`. Updated to use `FacebookAdsService`, `generate_csv_response` utility, dependency injection, combined data handling (posts+reels), and specific error handling.
- Refactored endpoint `GET /business_post_insights_csv`. Updated to use `FacebookAdsService`, `generate_csv_response` utility, dependency injection, date types, and specific error handling.
- Implemented reusable CSV generation utility (`app/utils/csv_utils.py::generate_csv_response`). Handles dynamic headers, data flattening, BOM, and `StreamingResponse` creation.
- Implemented `get_all_business_posts_and_reels_insights` method in `FacebookAdsService`. Reuses page fetching helper, concurrently gets posts and reels insights per page, aggregates separately, returns tuple `(posts, reels)`.
- Implemented `get_business_post_insights` method in `FacebookAdsService` (`app/services/facebook_ads.py`). Fetches pages for a business (with caching), then concurrently gets post insights for each page using `get_post_insights` and aggregates results.
- Verified `PostInsight` model structure in `app/models/facebook.py` against TDD. No structural or documentation changes were needed.
- Fixed API startup errors (JWEError import issue and missing date module)
- Next focus is on implementing Facebook caching

## Implementation Details

- Project structure follows FastAPI best practices
- Core directories established for modular development
- Environment configuration using .env files
- Testing framework set up with pytest
- Documentation system initialized
- API endpoints documented in docs/api_endpoints.md
- Integrations documented in docs/integrations.md
- Using file-based JSON storage for caching instead of Redis

## Implementation Notes

- **DateRange Model:**
  - Created `app/models/common.py`.
  - Defined `DateRange` and `OptionalDateRange` Pydantic models.
  - Included `start_date` and `end_date` fields (type `date`).
  - Added validation to ensure `end_date` >= `start_date`.
  - Added docstrings and schema examples.
- **AdsInsight Model:**
  - Located and updated existing `AdsInsight` model in `app/models/facebook.py`.
  - Added `date_start: Optional[str]` and `date_stop: Optional[str]` fields.
  - Made other identifier fields optional with `None` default.
  - Added comprehensive docstring explaining the model and its fields.
  - Added a `schema_extra` example for documentation.
- **FacebookCampaignMetricsRequest Model:**
  - Verified existing model in `app/models/facebook.py`.
  - Corrected import path for `DateRange` to `app.models.common`.
  - Added `schema_extra` examples for documentation.
- **FacebookMetricsResponse Model:**
  - Verified existing model in `app/models/facebook.py`.
  - Updated docstring for `data` field to clarify content type.
  - Added `schema_extra` examples for success and error cases.
- **FacebookAdsService Structure:**
  - Created `app/services/facebook_ads.py`.
  - Defined `FacebookAdsService` class with `__init__(cache_service)`.
  - Added helper `_get_api_instance(access_token)` for API initialization.
  - Defined placeholder async methods: `get_campaign_insights`, `get_post_insights`, `get_reel_insights`.
  - Included necessary imports, type hints, docstrings, basic logging, and TODOs.
- **FacebookAdsService `get_campaign_insights`:**
  - Implemented method logic in `app/services/facebook_ads.py`.
  - Added cache check using `cache_service.get` and key generation.
  - Initialized API instance using `_get_api_instance`.
  - Constructed `fields`
