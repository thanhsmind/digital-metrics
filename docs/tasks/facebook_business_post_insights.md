# Task Breakdown: Facebook Business Post Insights

## Models

- [ ] Task 1: Cập nhật PostInsight model (High Priority)
  - [ ] Thêm các fields cần thiết và validation rules
  - [ ] Đảm bảo compatibility với cả posts và reels

## Services

- [ ] Task 2: Implement phương thức get_business_post_insights trong FacebookApiManager (High Priority)

  - [ ] Lấy tất cả pages thuộc business
  - [ ] Lấy tất cả posts từ các pages
  - [ ] Lấy metrics cho mỗi post
  - [ ] Tổng hợp dữ liệu

- [ ] Task 3: Implement phương thức get_all_business_posts_and_reels_insights

  - [ ] Extend logic từ get_business_post_insights
  - [ ] Thêm xử lý cho reels
  - [ ] Phân biệt metrics giữa posts và reels

- [ ] Task 4: Implement CSV generation logic
  - [ ] Tạo CSV output format
  - [ ] Thêm UTF-8 BOM cho Excel compatibility
  - [ ] Đảm bảo proper escaping và formatting

## API Endpoints

- [ ] Task 5: Implement endpoint GET /business_post_insights_csv (High Priority)

  - [ ] Validate request parameters
  - [ ] Gọi service method tương ứng
  - [ ] Trả về StreamingResponse với CSV data
  - [ ] Set proper headers và content type

- [ ] Task 6: Implement endpoint GET /business_posts_and_reels_insights_csv
  - [ ] Validate request parameters
  - [ ] Phân biệt giữa post_metrics và reel_metrics
  - [ ] Gọi service method tương ứng
  - [ ] Trả về StreamingResponse với CSV data

## Caching & Performance

- [ ] Task 7: Implement caching logic

  - [ ] Cache pages của business (30 phút)
  - [ ] Cache posts/reels metadata (15 phút)
  - [ ] Implement cache invalidation

- [ ] Task 8: Tối ưu performance
  - [ ] Sử dụng async/await cho non-blocking IO
  - [ ] Implement batch operations
  - [ ] Tối ưu StreamingResponse

## Error Handling & Security

- [ ] Task 9: Implement error handling

  - [ ] Validate input parameters
  - [ ] Xử lý FacebookRequestError
  - [ ] Cung cấp meaningful error messages
  - [ ] Logging không lưu sensitive information

- [ ] Task 10: Implement security measures
  - [ ] Sử dụng tokens từ api auth
  - [ ] Validate và sanitize input
  - [ ] Đảm bảo exception handling không expose sensitive information

## Testing

- [ ] Task 11: Viết unit tests

  - [ ] Tests cho validation logic
  - [ ] Tests cho CSV generation
  - [ ] Tests cho error handling

- [ ] Task 12: Viết integration tests

  - [ ] Mocks cho Facebook API responses
  - [ ] End-to-end flow tests
  - [ ] Error scenario tests

- [ ] Task 13: Viết performance tests
  - [ ] Response time tests
  - [ ] Load tests với nhiều concurrent requests
  - [ ] Memory usage tests với large datasets

## Documentation

- [ ] Task 14: Cập nhật API documentation

  - [ ] Thêm chi tiết cho endpoints mới
  - [ ] Thêm examples và error responses
  - [ ] Document các loại metrics khả dụng

- [ ] Task 15: Viết usage guide
  - [ ] Hướng dẫn sử dụng API
  - [ ] Best practices cho việc lấy metrics
  - [ ] Troubleshooting common issues
