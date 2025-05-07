# Digital Metrics API

API service để lấy metrics từ Facebook Ads và Google Ads.

## Tính năng

### Facebook Ads

- Lấy insights từ các posts của business
- Lấy insights từ reels
- Lấy thông tin về ads campaigns
- Hỗ trợ nhiều loại metrics khác nhau
- Export dữ liệu dưới dạng CSV

### Google Ads

- Lấy insights từ campaigns
- Lấy insights từ ad groups
- Hỗ trợ nhiều metrics và dimensions
- Export dữ liệu dưới dạng CSV

## Cài đặt

1. Clone repository:

```bash
git clone <repository-url>
cd digital-metrics
```

2. Tạo virtual environment:

```bash
uv venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Cài đặt dependencies:

```bash
uv pip install -r requirements.txt
```

4. Tạo file .env:

```bash
cp .env.example .env
```

5. Cập nhật các biến môi trường trong .env:

```bash
# Facebook configuration
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token

# Google Ads configuration
GOOGLE_ADS_CONFIG_FILE=google-ads.yaml
```

6. Chạy ứng dụng:

```bash
uv run uvicorn app.main:app --reload
#uvicorn app.main:app --reload
```

## API Documentation

Sau khi chạy ứng dụng, bạn có thể truy cập:

- API documentation: http://localhost:8000/docs
- OpenAPI specification: http://localhost:8000/api/v1/openapi.json

### Facebook Endpoints

#### GET /api/v1/facebook/business_post_insights_csv

Lấy insights của posts từ một business dưới dạng CSV.

#### GET /api/v1/facebook/business_posts_and_reels_insights_csv

Lấy insights của cả posts và reels từ một business dưới dạng CSV.

#### GET /api/v1/facebook/available_metrics

Xem danh sách các metrics có sẵn.

### Google Ads Endpoints

#### GET /api/v1/google/campaigns_csv

Lấy insights của campaigns dưới dạng CSV.

#### GET /api/v1/google/ad_groups_csv

Lấy insights của ad groups dưới dạng CSV.

#### GET /api/v1/google/available_metrics

Xem danh sách các metrics có sẵn.

#### GET /api/v1/google/available_dimensions

Xem danh sách các dimensions có sẵn.

## Link mẫu báo cáo Facebook

Các link dưới đây có thể được sử dụng để lấy báo cáo Facebook Ads cho `business_id=1602411516748597` trong 30 ngày gần nhất.

### Báo cáo post insights

http://127.0.0.1:8000/api/v1/facebook/business_post_insights_csv?business_id=1602411516748597&since_date=2023-06-01&until_date=2023-06-30&metrics=impressions

```
# Báo cáo post insights với các metrics mặc định (impressions, reach, engaged_users, reactions)
http://localhost:8000/api/v1/facebook/business_post_insights_csv?business_id=1602411516748597&since_date=2024-02-21&until_date=2024-03-21

# Báo cáo với metrics tùy chỉnh
http://localhost:8000/api/v1/facebook/business_post_insights_csv?business_id=1602411516748597&metrics=impressions,reach,engaged_users,reactions,clicks,like,love,video_views&since_date=2024-02-21&until_date=2024-03-21

# Báo cáo tập trung vào video
http://localhost:8000/api/v1/facebook/business_post_insights_csv?business_id=1602411516748597&metrics=video_views,video_views_10s,video_avg_time_watched,video_length&since_date=2024-02-21&until_date=2024-03-21
```

### Báo cáo posts và reels insights

```
# Báo cáo post và reels với metrics mặc định
http://localhost:8000/api/v1/facebook/business_posts_and_reels_insights_csv?business_id=1602411516748597&since_date=2024-02-21&until_date=2024-03-21

# Báo cáo với post metrics tùy chỉnh
http://localhost:8000/api/v1/facebook/business_posts_and_reels_insights_csv?business_id=1602411516748597&post_metrics=impressions,reach,engaged_users,clicks&reel_metrics=impressions,reach,reactions&since_date=2024-02-21&until_date=2024-03-21

# Báo cáo tập trung vào reels
http://localhost:8000/api/v1/facebook/business_posts_and_reels_insights_csv?business_id=1602411516748597&post_metrics=impressions,reach&reel_metrics=reels_total_number_milliseconds,reels_total_comment_share,reactions,reach,impressions&since_date=2024-02-21&until_date=2024-03-21
```

### Kiểm tra và debug

```
# Kiểm tra các metrics có sẵn
http://localhost:8000/api/v1/facebook/available_metrics

# Kiểm tra quyền truy cập vào các trang trong business
http://localhost:8000/api/v1/facebook/check_business_pages_access?business_id=1602411516748597

# Debug token
http://localhost:8000/api/v1/facebook/debug_token?token={access_token}
```

Lưu ý: Các link này giả định rằng API đang chạy ở localhost trên cổng 8000. Điều chỉnh URL phù hợp với environment thực tế của bạn.

## Development

### Project Structure

```

```
