Bạn là một software engineer hiểu sâu về python, fastapi, facebook sdk, google sdk, cẩn thận và chi tiết trong dự án Digital Metrics.
we have some issues in the codebase.

your goal is to fix my issues

<problems>
Khi tôi chạy http://127.0.0.1:8000/api/v1/auth/facebook/refresh-token thì kết quả nhận được là
lỗi code 500
{
  "detail": "Error refreshing token: 'TokenManager' object has no attribute 'refresh_all_tokens'"
}

</problems>

This is the Technical Design Document we are currently working on:@docs/technical_design/facebook_auth_service_design.md

Output:

- output every file which has been changed + filename
  Tôi chạy để lấy toke facebook bằng api
  https://www.facebook.com/v22.0/dialog/oauth?client_id=1134157884360846&redirect_uri=http://localhost:8000/api/v1/auth/facebook/callback&state=FuFawtYh59gugE8Zvag3kDT3rJ9hx6wtHXJCYQalw5s&scope=public_profile,pages_show_list,pages_read_engagement,ads_read&response_type=code
  nhưng kết quả trả về bị báo lỗi
  Authentication error: Failed to exchange code for token: Failed to initialize Facebook API: 'NoneType' object has no attribute 'encode'"
