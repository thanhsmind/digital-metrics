# Technical Context

## Project Structure

```
app/
├── api/           # API endpoints
├── core/          # Core configurations
├── integrations/  # External integrations
├── middleware/    # Custom middleware
├── models/        # Data models
├── schemas/       # Pydantic schemas
├── services/      # Business logic services
├── tasks/         # Background tasks
└── utils/         # Utility functions
```

## Technical Stack

- Python/FastAPI
- Environment: Python virtual environment managed by `uv` (typically `.venv`)
  - To create environment: `uv venv .venv` (or `uv venv`)
- Dependencies: requirements.txt
- Configuration: .env files
- Testing: pytest

## Development Environment

- OS: Windows 10
- IDE: Cursor
- Version Control: Git
- Documentation: Markdown

## Current Technical State

- Basic FastAPI project structure set up
- Core directories created
- Environment configuration in place
- Testing framework initialized

## Platform-Specific Notes

- Windows-specific command adaptations required
- Using PowerShell for command execution

## Dependency Management

- **Package Manager**: `uv` is used for Python dependency management. It replaces `pip` for faster and more efficient package installation and resolution.
  - To install dependencies: `uv pip install -r requirements.txt`
  - To add a new package: `uv pip install <package-name>`
  - To freeze dependencies: `uv pip freeze > requirements.txt`

## Notes

- Technical context initialized
