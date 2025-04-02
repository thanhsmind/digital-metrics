# Project Brief: Digital Metrics API

## Overview

FastAPI-based API for digital metrics collection and analysis. Xây dựng các API giúp có thể lấy các metrics từ các nguồn (Facebook page, facebook ads, google ads)

## Core Requirements

- FastAPI implementation
- Digital metrics collection
- Data analysis capabilities

## Technical Stack

- Python/FastAPI
- Facebook SDK
- Google Ads API
- Database: Json file

## Project Goals

- Hệ thống sẽ lấy metrics trên Facebook, Google như:
  - Facebook
    - Facebook Ads
    - Facebook Page
  - Google Ads
- Tự động có thể quản lý các tokens Auth riêng biệt của từng nhóm dịch vụ (Facebook, Google) và lưu những token này vào jsonfile liên quan
  - Có hệ thống tự động refresh new token khi chúng sắp hết hạn.
- Create efficient metrics collection system
- Implement secure data handling
- Provide comprehensive analytics capabilities
