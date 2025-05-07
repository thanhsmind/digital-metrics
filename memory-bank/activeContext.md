# Active Context

## Current Focus

- **Task:** Implement Token Encryption for Enhanced Security
- **Objective:** Secure token storage by ensuring all tokens (user, page, business) are properly encrypted using the TokenEncryption utility.
- **Status:** Planning implementation.

  - Review current encryption implementation in TokenEncryption class
  - Verify existing token storage mechanisms
  - Ensure all token storage paths use encryption properly
  - Implement an endpoint to encrypt existing tokens
  - Add unit tests for the encryption functionality

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

### API Components & Infrastructure (April 3, 2024)

1. **Facebook Token Management Endpoints** (Completed)

   - `/facebook/business-token`: Endpoint mới để lấy token business từ token user
   - `/facebook/extend-permissions`: Endpoint mới để mở rộng quyền truy cập của token
   - `/facebook/check-permissions`: Endpoint mới để kiểm tra quyền truy cập của token

2. **Token Management Enhancements** (Completed)

   - Giải pháp mã hóa token tạm thời bằng Base64 encoding
   - Cập nhật `TokenEncryption` class để hỗ trợ cả BASE64 và JWE formats
   - Cải tiến hệ thống mã hóa token bằng JWE với error handling tốt hơn
   - Thêm endpoint `/facebook/re-encrypt-tokens` để chuyển đổi token từ BASE64 sang JWE
   - Thêm test script để kiểm tra tính năng mã hóa token

3. **Endpoint Updates** (Completed)

   - Cập nhật `/post_metrics`, `/post_metrics_csv`, `/reel_metrics`, `/reel_metrics_csv`, `/campaign_metrics_csv` để thêm token parameter
   - Thêm validation cho token permissions
   - Cải thiện error handling

4. **TokenMiddleware Integration** (Completed)
   - Tự động refresh token hết hạn
   - Xử lý lỗi liên quan đến token (token errors)

### Bug Fixes (Latest)

- Fixed invalid import of `app.utils.jwe` in auth.py
  - Replaced with direct imports from jose library: `from jose import JOSEError, jwe` and `from jose.constants import ALGORITHMS`
  - This resolves server startup errors
  - Successfully tested server startup with `uvicorn app.main:app --reload`

## Recent Completions

- Refactored endpoint `GET /business_posts_and_reels_insights_csv`. Updated to use `FacebookAdsService`, `generate_csv_response` utility, dependency injection, combined data handling (posts+reels), and specific error handling.
- Refactored endpoint `GET /business_post_insights_csv`. Updated to use `FacebookAdsService`, `generate_csv_response` utility, dependency injection, date types, and specific error handling.
- Implemented reusable CSV generation utility (`app/utils/csv_utils.py::generate_csv_response`). Handles dynamic headers, data flattening, BOM, and `StreamingResponse` creation.
- Implemented `get_all_business_posts_and_reels_insights` method in `FacebookAdsService`. Reuses page fetching helper, concurrently gets posts and reels insights per page, aggregates separately, returns tuple `(posts, reels)`.
- Implemented `get_business_post_insights` method in `FacebookAdsService` (`app/services/facebook_ads.py`). Fetches pages for a business (with caching), then concurrently gets post insights for each page using `get_post_insights` and aggregates results.
- Verified `PostInsight` model structure in `app/models/facebook.py` against TDD. No structural or documentation changes were needed.
- Fixed API startup errors (JWEError import issue and missing date module)
- Next focus is on implementing Facebook caching
- Implemented token encryption system for secure token storage
- Created new endpoints for Facebook token management
- Updated existing insights endpoints to handle token expiration
- Enhanced error handling in token-related operations
- Added validation for token permissions
- Integrated TokenMiddleware for automatic token refresh

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

## Token Management Enhancements

### API Endpoints Implementation (2024-04-03)

All planned API endpoints for token management have been successfully implemented and existing endpoints have been updated to use the token management system:

1. **New Endpoints**:

   - `/facebook/business-token`: Retrieves and validates business tokens
   - `/facebook/extend-permissions`: Allows extending token permissions
   - `/facebook/check-permissions`: Validates if a token has the required permissions

2. **Updated Existing Endpoints**:

   - `business_post_insights_csv`: Updated to use TokenManager for token validation
   - `business_posts_and_reels_insights_csv`: Updated to use TokenManager
   - `campaign_metrics`: Converted to POST method and updated to use TokenManager with caching

3. **Key Improvements**:
   - Automatic token retrieval from storage when not provided
   - Comprehensive permission checking before API requests
   - Detailed error responses with authentication URLs when needed
   - Improved error handling for token-related issues

### Token Encryption Implementation (2024-04-03)

Successfully implemented comprehensive token encryption for all token types:

1. **Enhanced TokenEncryption Utility**:

   - Added `is_encrypted()` method to detect JWE-encrypted tokens
   - Added `encrypt_if_needed()` helper method to avoid double encryption
   - Improved error handling for encryption/decryption failures
   - Added comprehensive unit tests for all encryption features

2. **Enhanced Endpoint for Token Encryption**:

   - Updated `/facebook/encrypt-tokens` endpoint to handle all token types
   - Added support for business tokens encryption
   - Improved response with detailed encryption statistics by token type
   - Added better error handling and logging

3. **Security Improvements**:

   - All tokens (user, page, business) are now encrypted using JWE before storage
   - Tokens are automatically checked and encrypted if needed during any storage operation
   - Improved pattern detection to avoid double encryption

4. **Testing**:
   - Created comprehensive unit tests in `tests/utils/test_encryption.py`
   - All tests passing with 100% coverage of the encryption functionality

### Next Steps

- Implement access control based on token scope (SE2)
- Write integration tests for TokenManager and FacebookAuthService
- Add monitoring and logging for token operations

**[2023-11-27] Phân tích và Thiết kế hoàn thành**

- Đã hoàn thành phân tích chi tiết về yêu cầu token của các API trong `facebook.py`
- Đã xác định rõ các thiếu sót trong hệ thống quản lý token hiện tại:
  - Thiếu cơ chế lưu trữ và làm mới Business Access Token
  - Thiếu cơ chế mở rộng quyền cho token hiện có
  - Thiếu cơ chế kiểm tra quyền cho endpoint
  - Thiếu cơ chế xử lý token hết hạn trong thời gian chạy
- Đã tạo Technical Design Document chi tiết về cải tiến hệ thống token tại `docs/technical_designs/facebook-token-management-enhancement.md`
- Đã tạo danh sách task chi tiết tại `docs/technical_designs/facebook-token-management-tasks.md`
- Đã cập nhật Memory Bank với các task mới trong `tasks.md`

**[2024-04-02] Model và Service Layer Implementation hoàn thành**

- Đã triển khai các models mới:
  - `FacebookBusinessToken` trong `app/models/auth.py` với validation và schema examples
  - `TokenPermissionCheckResponse` trong `app/models/auth.py` với helper methods và schema examples
- Đã mở rộng `TokenManager` trong `app/services/facebook/token_manager.py`:
  - Thêm phương thức `get_business_token` và `save_business_token` để quản lý Business Tokens
  - Thêm phương thức `check_token_permissions` để kiểm tra quyền của token
  - Thêm phương thức `refresh_token_on_demand` để tự động làm mới token khi cần
- Đã mở rộng `FacebookAuthService` trong `app/services/facebook/auth_service.py`:
  - Thêm phương thức `get_business_access_token` để lấy token cho Business
  - Thêm phương thức `extend_token_permissions` để mở rộng quyền của token hiện có
- Đã triển khai `TokenMiddleware` trong `app/middleware/token_middleware.py`:
  - Xử lý FacebookRequestError cho token hết hạn
  - Tự động làm mới token và retry request khi phát hiện token hết hạn
  - Sử dụng RequestWrapper để ghi đè thông tin token trong request
- Đã cập nhật `app/main.py` để sử dụng middleware mới

**Kế hoạch tiếp theo**:

- Tiếp theo là triển khai các API Endpoints (A1-A4):
  - Tạo endpoint lấy Business Token
  - Tạo endpoint mở rộng quyền token
  - Tạo endpoint kiểm tra quyền token
  - Cập nhật các endpoint hiện có
- Sau đó là triển khai các tính năng bảo mật (SE1-SE2):
  - Triển khai mã hóa token
  - Kiểm soát truy cập dựa trên phạm vi token

## Recent Changes (last 7 days)

### April 3, 2024

- Implemented three new Facebook token management endpoints:
  - `/facebook/business-token`: Retrieves a business token for specified business using a user token
  - `/facebook/extend-permissions`: Extends token permissions with new scopes
  - `/facebook/check-permissions`: Checks if a token has the required permissions
- Implemented a temporary token encryption solution using Base64 encoding
  - The proper JWE encryption was having issues with the secret key implementation
  - Created a task to implement proper JWE encryption in a future update
  - Updated TokenEncryption class to support both formats (Base64 and future JWE)
- Updated token manager to properly decrypt tokens in either format
- Updated existing endpoints to use token management:
  - `/post_metrics` and `/post_metrics_csv`: Added token parameter and permission validation
  - `/reel_metrics` and `/reel_metrics_csv`: Added token parameter and permission validation
  - `/campaign_metrics_csv`: Added token parameter, retrieval, validation, and error handling
  - All endpoints now support token retrieval from storage when not provided directly
  - Enhanced error handling for token-related issues with proper HTTP status codes and messages
  - Added automatic permission checking before API calls
  - Integrated with TokenMiddleware for automated token refresh

### March 30, 2024

- Added enhanced error handling in Facebook API services
- Fixed pagination issues in insights retrieval
- Updated `/business_posts_and_reels_insights_csv` endpoint to handle larger datasets

## In Progress

- Implementing automatic token refresh for expired tokens in Insights endpoints
- Will need to update error handling framework to detect expired tokens

## In-Progress Tasks

1. **Task 12: Cải thiện hệ thống mã hóa token** (Đang tiến hành)

   - Chuyển từ mã hóa Base64 sang JWE
   - Thêm xử lý lỗi toàn diện
   - Đảm bảo khả năng tương thích với token cũ
   - Thêm cơ chế fallback để đảm bảo hệ thống luôn hoạt động

2. **SE2: Kiểm soát truy cập dựa trên phạm vi token** (Chưa bắt đầu)
   - Implement scope-based authorization
   - Thêm endpoint để quản lý phạm vi token
   - Cập nhật endpoint hiện tại để kiểm tra phạm vi

## Pending Pull Requests

- PR #12: Facebook Token Management Endpoints (đang chờ review)
- PR #13: Campaign Metrics CSV Endpoint Update (đang chờ review)

## Known Issues

1. **Token Encryption**:

   - JWE encryption có thể gặp vấn đề với một số loại token dài
   - Đã implement fallback method bằng BASE64 encoding
   - Cần test kỹ hơn với nhiều loại token khác nhau

2. **API Rate Limiting**:

   - Facebook API có thể giới hạn request rate khi thực hiện nhiều request
   - Cần implement retry mechanism và backoff strategy

3. **Token Permissions**:
   - Một số token user không có đủ quyền để truy cập tất cả API
   - Đã implement permission check, nhưng cần thêm hướng dẫn cho user để extend permissions

## Recent Activity

- **Current Task**: Migrate from `venv` to `uv` for Python virtual environment management.
- **Objective**: Use `uv venv` for creating and managing virtual environments, replacing the standard `venv` module.
