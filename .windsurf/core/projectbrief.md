# Project Brief: Digital Metrics API

## Overview

The Digital Metrics API is a Python-based service designed to consolidate advertising performance data from Facebook Ads and Google Ads.

## Core Goals

- Provide a unified API interface to retrieve metrics from multiple advertising platforms (Facebook, Google).
- Fetch insights for various ad components like Facebook posts, reels, campaigns, and Google campaigns, ad groups.
- Support a range of metrics and dimensions specific to each platform.
- Enable data export in CSV format for easy analysis.
- Offer clear API documentation for developers.

## Key Features (Based on README)

- Facebook Ads integration:
  - Business post insights
  - Reels insights
  - Ad campaign information retrieval
  - CSV export
- Google Ads integration:
  - Campaign insights
  - Ad group insights
  - CSV export
- API documentation endpoint (`/docs`).

## Project Structure

- **`/app`**: Main FastAPI application source code (endpoints, services, models).
- **`/config`**: Configuration files (e.g., external API keys/settings).
- **`/services`**: External service integrations or standalone utility modules.
- **`/tests`**: Automated tests (Pytest).
- **`/docs`**: General project documentation (separate from Memory Bank).
- **`/tokens`**: Storage for temporary tokens/credentials.
- **`.windsurf/`**: Windsurf Memory Bank files.
- **`requirements.txt`**: Python package dependencies.
- **`.env*`**: Environment variable files for configuration.
- **`README.md`**: Project overview and setup instructions.
