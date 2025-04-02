# Task Breakdown: Facebook Post và Reel Metrics

## Models

- [ ] Task 1: Implement/Update PostInsight model (High Priority)

  - [ ] Định nghĩa tất cả các fields cần thiết
  - [ ] Đảm bảo support cho các loại posts khác nhau
  - [ ] Validate format của fields

- [ ] Task 2: Implement VideoInsight model

  - [ ] Định nghĩa các trường dành riêng cho videos/reels
  - [ ] Đảm bảo support cho metrics đặc thù của reels
  - [ ] Validate format của fields

- [ ] Task 3: Implement FacebookMetricsResponse model
  - [ ] Định nghĩa response structure
  - [ ] Support cho summary data
  - [ ] Đảm bảo consistent format

## API Endpoints - Posts

- [ ] Task 4: Implement GET /post_metrics endpoint (High Priority)

  - [ ] Validate request parameters
  - [ ] Handle optional post_ids parameter
  - [ ] Support cho filters và date ranges
  - [ ] Format JSON response đúng structure

- [ ] Task 5: Implement GET /post_metrics_csv endpoint
  - [ ] Reuse logic từ post_metrics endpoint
  - [ ] Convert data sang CSV format
  - [ ] Streaming response implementation
  - [ ] Set headers và content type phù hợp

## API Endpoints - Reels

- [ ] Task 6: Implement GET /reel_metrics endpoint

  - [ ] Validate request parameters
  - [ ] Handle reel-specific metrics
  - [ ] Support cho filters và date ranges
  - [ ] Format JSON response đúng structure

- [ ] Task 7: Implement GET /reel_metrics_csv endpoint
  - [ ] Reuse logic từ reel_metrics endpoint
  - [ ] Convert data sang CSV format
  - [ ] Streaming response implementation
  - [ ] Set headers và content type phù hợp

## Services

- [ ] Task 8: Update FacebookAdsService và FacebookApiManager (High Priority)

  - [ ] Extend base services cho post và reel metrics
  - [ ] Implement kết nối tới Facebook Graph API
  - [ ] Xử lý token authentication

- [ ] Task 9: Implement get_post_metrics method

  - [ ] Truy vấn metrics cho posts cụ thể hoặc tất cả posts
  - [ ] Aggregate và summarize data
  - [ ] Format data theo response model
  - [ ] Support filtering by date range

- [ ] Task 10: Implement get_post_insights method

  - [ ] Lấy insights cho một post cụ thể
  - [ ] Support multiple metrics
  - [ ] Format response theo structure

- [ ] Task 11: Implement determine_post_type method
  - [ ] Phân biệt giữa post thường và reel
  - [ ] Handle edge cases và unknown types

## Caching & Performance

- [ ] Task 12: Implement caching logic

  - [ ] Cache post insights (15 phút)
  - [ ] Cache post metadata (1 giờ)
  - [ ] Cache page metadata (24 giờ)
  - [ ] Implement cache invalidation

- [ ] Task 13: Optimize performance
  - [ ] Implement async/await cho non-blocking I/O
  - [ ] Batch processing cho multiple posts
  - [ ] Pagination cho large result sets
  - [ ] Limit metrics để giảm payload size

## Error Handling & Security

- [ ] Task 14: Implement error handling

  - [ ] Xử lý validation errors
  - [ ] Handle FacebookRequestError
  - [ ] Implement retry logic
  - [ ] Provide meaningful error messages

- [ ] Task 15: Implement security measures
  - [ ] Validate access tokens
  - [ ] Sanitize input parameters
  - [ ] Không lưu tokens trong logs
  - [ ] Verify token quyền truy cập

## CSV Generation

- [ ] Task 16: Implement CSV generation logic (High Priority)
  - [ ] Create reusable CSV generator
  - [ ] Handle special characters
  - [ ] Support Unicode và encoding options
  - [ ] Include headers và formatting options

## Testing

- [ ] Task 17: Write unit tests

  - [ ] Test validation logic
  - [ ] Test data processing
  - [ ] Test type determination

- [ ] Task 18: Write integration tests

  - [ ] Tests với Facebook Graph API
  - [ ] End-to-end flow tests
  - [ ] Mock API responses

- [ ] Task 19: Write performance và edge case tests
  - [ ] Large dataset tests
  - [ ] Posts không có metrics
  - [ ] Expired tokens
  - [ ] Rate limit tests

## Documentation

- [ ] Task 20: Create API documentation

  - [ ] Document tất cả endpoints
  - [ ] Liệt kê metrics available cho mỗi loại nội dung
  - [ ] Add examples

- [ ] Task 21: Create usage guide
  - [ ] Best practices cho việc sử dụng API
  - [ ] Common workflows
  - [ ] Troubleshooting
