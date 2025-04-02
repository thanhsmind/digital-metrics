# Tasks

## Active Tasks

### Facebook Integration ([details](mdc:../docs/tasks/Facebook.md) | [TDD](mdc:../docs/technical_designs/technical_design.md))

- [x] Create Facebook request/response models
- [x] Implement FacebookAuthService
- [x] Implement FacebookAdsService (High Priority)
  - [x] Campaign metrics retrieval
  - [x] Post metrics retrieval
    - [x] Verify/Update `PostInsight` model in `app/models/facebook.py`
    - [x] Implement `get_post_insights` method logic
    - [x] Add caching (get/set)
    - [x] Construct API parameters (metrics, period, time_range)
    - [x] Call Page `get_insights` edge (or Post `get_insights`)
    - [x] Handle pagination and process results into `PostInsight` models
    - [x] Add error handling
  - [x] Reel metrics retrieval
    - [x] Verify/Update `VideoInsight` model in `app/models/facebook.py`
    - [x] Implement `get_reel_insights` method logic
    - [x] Add caching (get/set)
    - [x] Fetch videos/reels within date range (`page.get_videos`)
    - [x] Fetch insights per video/reel (`video.get_insights`)
    - [x] Handle pagination/concurrency and process results into `VideoInsight` models
    - [x] Add error handling
- [x] Create Facebook campaigns endpoint
- [x] Create Facebook metrics endpoints
- [x] Create metrics export endpoint

### Facebook Business Post Insights ([details](mdc:../docs/tasks/facebook_business_post_insights.md) | [TDD](mdc:../docs/technical_designs/facebook_business_post_insights.md))

- [x] Cập nhật PostInsight model (High Priority)
  - [x] Read `PostInsight` model definition (`app/models/facebook.py`)
  - [x] Verify model structure against TDD and usage patterns
  - [x] Add/Update docstrings and schema examples if needed
  - [x] Mark parent task complete
- [x] Implement phương thức get_business_post_insights trong FacebookApiManager (High Priority)
  - [x] Define method signature in `FacebookAdsService`
  - [x] Add logging
  - [x] Clarify/Assume Business API token requirements
  - [x] Fetch Business Pages (with Caching)
  - [x] Fetch Insights Concurrently using `get_post_insights`
  - [x] Aggregate Results
  - [x] Implement Error Handling
  - [x] Add Docstrings
  - [x] Mark parent task complete
- [ ] Implement phương thức get_all_business_posts_and_reels_insights
  - [x] Define method signature in `FacebookAdsService`
  - [x] Add logging
  - [x] Initialize API & Fetch Business Pages (reuse/refactor)
  - [x] Fetch Post & Reel Insights Concurrently (gather)
  - [x] Aggregate Post & Reel Results Separately
  - [x] Implement Error Handling
  - [x] Add Docstrings
  - [x] Mark parent task complete
- [x] Implement CSV generation logic
  - [x] Create `app/utils/csv_utils.py`
  - [x] Define `generate_csv_response` function signature
  - [x] Handle empty data case
  - [x] Implement dynamic header generation (incl. flattening)
  - [x] Implement in-memory CSV writing (`csv.DictWriter`)
  - [x] Create `StreamingResponse` with headers & BOM
  - [x] Add imports and docstrings
  - [x] Mark parent task complete
- [ ] Implement endpoint GET /business_post_insights_csv (High Priority)
  - [x] Locate existing endpoint route
  - [x] Update dependencies (inject service, token)
  - [x] Update query parameters (use `date` type)
  - [x] Update input validation (metrics parsing, date range)
  - [x] Call correct service method (`service.get_business_post_insights`)
  - [x] Add specific error handling (`FacebookRequestError`, `HTTPException`)
  - [x] Replace manual CSV logic with `generate_csv_response` call
  - [x] Update imports and docstrings
  - [x] Mark parent task complete
- [ ] Implement endpoint GET /business_posts_and_reels_insights_csv
  - [x] Locate existing endpoint route
  - [x] Update dependencies (inject service, token)
  - [x] Update query parameters (use `date` type, defaults)
  - [x] Update input validation (post/reel metrics, dates)
  - [x] Call `service.get_all_business_posts_and_reels_insights`
  - [x] Add specific error handling (`FacebookRequestError`, `HTTPException`)
  - [x] Combine post/reel results (add `content_type`)
  - [x] Call `generate_csv_response` with combined data
  - [x] Update imports and docstrings
  - [x] Mark parent task complete

### Facebook Campaign Metrics ([details](mdc:../docs/tasks/facebook_campaign_metrics.md) | [TDD](mdc:../docs/technical_designs/facebook_campaign_metrics.md))

- [x] Implement DateRange model (High Priority)
  - [x] Define model structure in `app/models/common.py`
  - [x] Add `start_date` and `end_date` fields (`datetime.date`)
  - [x] Implement validation (`end_date` >= `start_date`)
  - [x] Add docstrings and examples
- [x] Implement AdsInsight model
  - [x] Define model structure in `app/models/facebook.py`
  - [x] Add core fields (`campaign_id`, `campaign_name`, `date_start`, `date_stop`)
  - [x] Add common metrics fields (`impressions`, `reach`, `spend`, etc.) with appropriate types
  - [x] Use `Dict[str, Any]` for flexibility with other metrics
  - [x] Add docstrings and examples
- [x] Implement FacebookCampaignMetricsRequest model
  - [x] Locate existing model in `app/models/facebook.py`
  - [x] Verify fields (`ad_account_id`, `campaign_ids`, `date_range`, `metrics`, `dimensions`)
  - [x] Ensure correct types (including `DateRange` import)
  - [x] Add/Update docstrings and examples
- [x] Implement FacebookMetricsResponse model
  - [x] Locate existing model in `app/models/facebook.py`
  - [x] Verify fields (`success`, `message`, `data`, `summary`)
  - [x] Ensure correct types (esp. `data` as `List[Dict[str, Any]]` for generality)
  - [x] Add/Update docstrings and examples
- [x] Develop FacebookAdsService base structure (High Priority)
  - [x] Create `app/services/facebook_ads.py` if not exists
  - [x] Import necessary models and config
  - [x] Define `FacebookAdsService` class with `__init__`
  - [x] Define placeholder method `get_campaign_insights`
  - [x] Define placeholder method `get_post_insights`
  - [x] Define placeholder method `get_reel_insights`

### Facebook Post và Reel Metrics ([details](mdc:../docs/tasks/facebook_post_reel_metrics.md) | [TDD](mdc:../docs/technical_designs/facebook_post_reel_metrics.md))

- [x] Implement/Update PostInsight model (High Priority)
- [x] Implement VideoInsight model
- [x] Implement FacebookMetricsResponse model
- [x] Implement GET /post_metrics endpoint (High Priority)
  - [x] Define endpoint in `app/api/v1/endpoints/facebook.py`
  - [x] Add dependencies (Auth token, FacebookAdsService)
  - [x] Define input parameters (page_id, metrics, start_date, end_date)
  - [x] Validate input metrics
  - [x] Call `service.get_post_insights`
  - [x] Handle errors and return response/HTTPException
- [x] Implement GET /reel_metrics endpoint
  - [x] Locate and modify existing endpoint in `app/api/v1/endpoints/facebook.py`
  - [x] Add dependencies (Auth token, FacebookAdsService)
  - [x] Update input parameters (use `date` type, remove `reel_ids`)
  - [x] Validate input metrics against `AVAILABLE_REEL_METRICS`
  - [x] Call `service.get_reel_insights`
  - [x] Update response model to `List[VideoInsight]`
  - [x] Update error handling

### Facebook Utility APIs ([details](mdc:../docs/tasks/facebook_utility_apis.md) | [TDD](mdc:../docs/technical_designs/facebook_utility_apis.md))

- [ ] Implement TokenDebugInfo model (High Priority)
- [ ] Implement BusinessPage model
- [x] Implement GET /available_metrics endpoint (High Priority)
  - [x] Define/Locate metric constants (Post, Reel, Campaign)
  - [x] Define endpoint in `app/api/v1/endpoints/facebook.py`
  - [x] Set response model `Dict[str, List[str]]`
  - [x] Return dictionary with constant lists
  - [x] (Optional) Add caching
- [ ] Implement GET /debug_token endpoint
- [ ] Implement GET /check_business_pages_access endpoint

### Google Ads Integration ([details](mdc:../docs/tasks/Google_Ads_Integration.md) | [TDD](mdc:../docs/technical_designs/technical_design.md))

- [x] Create Google request models
- [ ] Implement GoogleAuthService (High Priority)
- [ ] Implement GoogleAdsService
- [ ] Implement caching for Google
- [ ] Create Google campaigns endpoint
- [ ] Create Google metrics endpoints
- [ ] Create export functionality

### Testing [details](mdc:../docs/tasks/Google_Ads_Integration.md#testing)

- [ ] Unit Tests
  - [ ] Test models
  - [ ] Test services
  - [ ] Test API endpoints
- [ ] Integration Tests
  - [ ] Facebook integration tests
  - [ ] Google integration tests
- [ ] Performance Tests
  - [ ] Load testing
  - [ ] Stress testing

### Infrastructure & Deployment [details](mdc:../docs/tasks/SetupInfrastructure.md)

- [x] Fix virtual environment setup
- [x] Replace Redis with JSON file-based cache
- [ ] Setup development environment
- [ ] Configure CI/CD pipeline
- [ ] Setup monitoring and logging
- [ ] Configure production environment

### Documentation [details](mdc:../docs/tasks/Documentation.md)

- [ ] API documentation
- [ ] Integration guides
- [ ] Deployment guides
- [ ] Troubleshooting guides

### Bug Fixes

- [x] Fix JWEError import in encryption.py
  - [x] Replace JWEError with JOSEError
  - [x] Test API startup
  - [x] Fix missing app.models.date module

## Completed Tasks

### Fix ConfigError Import Issue

- [x] Add ConfigError class to app.utils.errors module
- [x] Test ConfigError implementation
- [x] Document the fix

### Facebook Token Refresh API [details](mdc:../docs/tasks/refresh-tokens-api-tasks.md)

- [x] Analyze existing code
- [x] Enhance TokenManager
- [x] Improve background tasks
- [x] Create new API endpoints
- [x] Security improvements
- [x] Configuration updates
- [x] Testing implementation
- [x] Deployment setup

## Notes

- Task tracking initialized on 2024-03-31
- Using single source of truth for task status
- Following FastAPI best practices for implementation
- Tasks are organized by feature and priority
- High priority tasks are marked with "(High Priority)"
