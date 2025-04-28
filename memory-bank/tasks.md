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
- [x] Fix app.utils.jwe import error in auth.py
  - [x] Replace with direct imports from jose library
  - [x] Successfully tested app startup

### Facebook Token Management Enhancement

1. ✅ Tạo model FacebookBusinessToken
2. ✅ Tạo model TokenPermissionCheckResponse
3. ✅ Mở rộng TokenManager để lưu trữ và truy xuất Business Token
4. ✅ Mở rộng TokenManager để kiểm tra quyền của token
5. ✅ Mở rộng FacebookAuthService để lấy Business Token từ User Token
6. ✅ Mở rộng FacebookAuthService để xử lý mở rộng quyền token
7. ✅ Tạo TokenMiddleware để xử lý hết hạn token trong quá trình request
8. ✅ Tạo endpoint lấy Business Token
9. ✅ Tạo endpoint mở rộng quyền token
10. ✅ Tạo endpoint kiểm tra quyền token
11. ✅ Cập nhật các endpoint hiện tại để sử dụng TokenManager
12. ✅ Triển khai mã hóa token (High Priority)

#### Tasks A1-A4: API Endpoints for Token Management - ✅ HOÀN THÀNH

- ✅ A1: Tạo endpoint để lấy Business Token
- ✅ A2: Tạo endpoint để mở rộng quyền của token
- ✅ A3: Tạo endpoint để kiểm tra quyền của token
- ✅ A4: Cập nhật các endpoint hiện tại để sử dụng TokenManager và TokenMiddleware

#### Tasks SE1-SE2: Security cho Token Management - Đang tiến hành

- ✅ SE1: Triển khai mã hóa token trong kho lưu trữ
- [ ] SE2: Kiểm soát truy cập dựa trên phạm vi token

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

## Facebook Token Management Enhancements

### Tasks M1-M2: Tạo các Model mới cho Token Management (P0)

- **Mô tả**: Xây dựng các model Pydantic cần thiết cho việc quản lý token
- **Trạng thái**: Hoàn thành
- **Chi tiết**:
  - [x] Tạo model FacebookBusinessToken trong app/models/facebook.py
  - [x] Tạo model TokenPermissionCheckResponse trong app/models/facebook.py
  - [x] Đảm bảo tương thích với Pydantic V2

### Tasks S1-S5: Mở rộng các Service cho Token Management (P0)

- **Mô tả**: Nâng cấp hệ thống service để hỗ trợ đầy đủ các loại token và xử lý hết hạn
- **Trạng thái**: Hoàn thành
- **Chi tiết**:
  - [x] Mở rộng TokenManager để hỗ trợ Business Tokens
  - [x] Thêm phương thức kiểm tra quyền token
  - [x] Triển khai cơ chế tự động làm mới token
  - [x] Mở rộng FacebookAuthService
  - [x] Tạo TokenMiddleware xử lý token hết hạn tự động

### Tasks A1-A4: Phát triển các API Endpoint mới cho Token Management (P1)

- **Mô tả**: Tạo và cập nhật các API endpoint liên quan đến token
- **Trạng thái**: Hoàn thành
- **Chi tiết**:
  - [x] Tạo endpoint lấy Business Token
  - [x] Tạo endpoint mở rộng quyền token
  - [x] Tạo endpoint kiểm tra quyền token
  - [x] Cập nhật các endpoint hiện có

### Tasks T1-T3: Testing cho Token Management (P1)

- **Mô tả**: Phát triển các test case cho các tính năng token mới
- **Trạng thái**: Chưa bắt đầu
- **Chi tiết**:
  - Viết unit tests cho TokenManager
  - Viết unit tests cho FacebookAuthService
  - Viết integration tests với Facebook API

### Tasks SE1-SE2: Security cho Token Management (P0)

- **Mô tả**: Triển khai các biện pháp bảo mật cho token
- **Trạng thái**: Đang tiến hành
- **Chi tiết**:
  - [x] SE1: Triển khai mã hóa token trong kho lưu trữ
  - [ ] SE2: Kiểm soát truy cập dựa trên phạm vi token

## Notes

- Task tracking initialized on 2024-03-31
- Using single source of truth for task status
- Following FastAPI best practices for implementation
- Tasks are organized by feature and priority
- High priority tasks are marked with "(High Priority)"

## Nhiệm vụ trong Sprint hiện tại

### Facebook Token Management Enhancement

- [x] Task 8: Tạo endpoint lấy Business Token
- [x] Task 9: Tạo endpoint mở rộng quyền token
- [x] Task 10: Tạo endpoint kiểm tra quyền token
- [x] Task 11: Cập nhật endpoint thống kê Insights để tự động xử lý token hết hạn
- [x] Task 12: Cải thiện hệ thống mã hóa token - chuyển từ giải pháp mã hóa tạm thời (Base64) sang giải pháp mã hóa an toàn (JWE) với xử lý lỗi tốt hơn

### Tasks A1-A4: Multiple Dashboard Support

- [ ] A1: Design database schema for multiple dashboards
- [ ] A2: Create API for dashboard management
- [ ] A3: Implement dashboard data service
- [ ] A4: Update UI for dashboard selection

Status: Đang tiến hành

## Upcoming Tasks
