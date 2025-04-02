# System Patterns

## Architecture Overview

- FastAPI-based REST API
- Modular directory structure
- Service-based architecture
- Environment-based configuration
- Sử dụng directory structure chuẩn cho FastAPI apps
- Tổ chức code theo functional modules
- Tách biệt API endpoints, business logic, và data models
- Sử dụng APIRouter để nhóm endpoints có liên quan
- Đặt API versioning trong URL path (/api/v1/...)

## Directory Structure Pattern

Directory Structure

```
digital-metrics/
├── app                      # Nơi chứa app FastAPI
│   ├── api/                 # Nơi chứa các endpoint của project
│   ├── core/                # Nơi chứa các config liên quan
│   ├── models/              # Nơi chứa models
│   ├── services/            # External service integrations
│   ├── middleware/          # python middleware
│   ├── utils/               # Utility functions (math, sorting, spatial hashing)
│   ├── main.py              # file main run app
├── services/                # Chứa các file config các services liên quan tới project
├── tests/                   # Chứa các test liên quan tới project
├── docs/                    # Chứa tất cả các tài liệu liên quan tới project
├── index.html               # Basic HTML page with root div
├── requirements.txt         # Chứa các gói cần thiết trong project python
└── tsconfig.json            # TypeScript configuration
```

Following FastAPI best practices:

- API routes in `api/`
- Core config in `core/`
- Data models in `models/`
- Business logic in `services/`
- Schema definitions in `schemas/`
- External integrations in `integrations/`
- Background tasks in `tasks/`
- Utilities in `utils/`

## Design Patterns

- Dependency injection for services
- Pydantic models for data validation
- Middleware for cross-cutting concerns
- Background tasks for async operations

## Coding Standards

- PEP 8 compliance
- Type hints usage
- Docstring documentation
- Unit test coverage

## Security Patterns

- Environment-based secrets
- Configuration isolation
- Authentication (to be implemented)
- Authorization (to be implemented)

## Implementation Patterns

- RESTful endpoint design
- Consistent error handling
- Comprehensive logging

## Notes

- Pattern documentation initialized
