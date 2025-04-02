# Task Breakdown: Facebook Utility APIs

## Models

- [ ] Task 1: Implement TokenDebugInfo model (High Priority)

  - [ ] Định nghĩa tất cả các fields cần thiết
  - [ ] Validate format của expires_at
  - [ ] Support cho scopes list

- [ ] Task 2: Implement BusinessPage model
  - [ ] Định nghĩa tất cả các fields cần thiết
  - [ ] Thêm has_insights_access field
  - [ ] Xử lý optional fields

## API Endpoints

- [ ] Task 3: Implement GET /available_metrics endpoint (High Priority)

  - [ ] Define constants cho post, reel, và ads metrics
  - [ ] Implement endpoint handler
  - [ ] Format JSON response

- [ ] Task 4: Implement GET /debug_token endpoint

  - [ ] Validate token parameter
  - [ ] Integrate với FacebookApiManager.debug_token()
  - [ ] Xử lý error cases
  - [ ] Format response theo TokenDebugInfo model

- [ ] Task 5: Implement GET /check_business_pages_access endpoint
  - [ ] Validate business_id parameter
  - [ ] Integrate với FacebookApiManager.get_business_pages()
  - [ ] Lấy và test quyền truy cập cho mỗi page
  - [ ] Format response với list của BusinessPage objects

## Services

- [ ] Task 6: Extend FacebookApiManager (High Priority)

  - [ ] Cập nhật service cho utility functions
  - [ ] Implement connection management
  - [ ] Xử lý authentication

- [ ] Task 7: Implement FacebookAuthService

  - [ ] Implement authentication helpers
  - [ ] Quản lý tokens và sessions
  - [ ] Connect với token storage

- [ ] Task 8: Implement debug_token method

  - [ ] Gọi Facebook API's debug_token endpoint
  - [ ] Parse response
  - [ ] Validate token data
  - [ ] Return TokenDebugInfo object

- [ ] Task 9: Implement get_business_pages method

  - [ ] Lấy tất cả pages thuộc business
  - [ ] Verify permissions
  - [ ] Return list của BusinessPage objects

- [ ] Task 10: Implement test_insights_access method

  - [ ] Test quyền truy cập insights cho một page
  - [ ] Xử lý permissions errors
  - [ ] Return access status

- [ ] Task 11: Implement update_access_token method
  - [ ] Update token trong session
  - [ ] Validate token mới
  - [ ] Reset cached data nếu cần

## Caching

- [ ] Task 12: Implement caching cho available metrics (24 giờ)

  - [ ] Setup cache mechanism
  - [ ] Store và retrieve metrics list
  - [ ] Implement invalidation

- [ ] Task 13: Implement caching cho token debug info (15 phút)

  - [ ] Cache token info với expiry
  - [ ] Check cache trước khi gọi API
  - [ ] Handle cache misses

- [ ] Task 14: Implement caching cho business pages (30 phút)
  - [ ] Cache pages list theo business ID
  - [ ] Update cache khi test insights access
  - [ ] Implement cache invalidation

## Error Handling & Security

- [ ] Task 15: Implement error handling (High Priority)

  - [ ] Handle invalid tokens
  - [ ] Handle missing permissions
  - [ ] Handle Facebook API errors
  - [ ] Provide meaningful error messages

- [ ] Task 16: Implement security measures
  - [ ] Mask tokens trong logs
  - [ ] Validate input parameters
  - [ ] Remove sensitive info từ responses
  - [ ] Implement rate limiting

## Performance

- [ ] Task 17: Optimize business pages check

  - [ ] Implement parallel processing
  - [ ] Batch API calls khi có thể
  - [ ] Lazy loading cho data không cần thiết ngay

- [ ] Task 18: Optimize API calls
  - [ ] Minimize số lượng calls tới Facebook
  - [ ] Implement proper timeouts
  - [ ] Retry logic cho failed calls

## Testing

- [ ] Task 19: Write unit tests

  - [ ] Test model validation
  - [ ] Test response formatting
  - [ ] Test error handling

- [ ] Task 20: Write integration tests

  - [ ] Tests với Facebook API sandbox
  - [ ] End-to-end flow tests
  - [ ] Permission tests

- [ ] Task 21: Write security và edge case tests
  - [ ] Invalid token tests
  - [ ] Expired token tests
  - [ ] Missing permission tests
  - [ ] Rate limit tests

## Documentation

- [ ] Task 22: Create API documentation

  - [ ] Document tất cả endpoints
  - [ ] Document available metrics
  - [ ] Add examples cho mỗi endpoint

- [ ] Task 23: Create usage guide
  - [ ] Debugging tokens guide
  - [ ] Checking permissions guide
  - [ ] Best practices for token management
