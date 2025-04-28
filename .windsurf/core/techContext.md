# Technology Context

## Backend

- **Framework**: FastAPI (Python)
- **Language**: Python 3.10+
- **Storage**: JSON files
- **Configuration**: Pydantic Settings (reading from `.env` files)
- **Testing**: Pytest

## External APIs

- **Facebook Business API**: For accessing Facebook Ads and related data.
- **Google Ads API**: For accessing Google Ads campaign data.
- Potentially others based on client needs.

## Infrastructure (Assumed/Typical)

- **Containerization**: Docker, Docker Compose (for local development)
- **CI/CD**: GitHub Actions (or similar like GitLab CI, Jenkins)
- **Hosting**: Cloud provider (AWS, GCP, Azure) or on-premise servers.

## Authentication & Security

- **JWT**: `python-jose` likely used for handling JSON Web Tokens.
- **Password Hashing**: `passlib` for securely hashing passwords.
- **Validation**: Pydantic for data validation at the API layer.

## Development Tools

- **Version Control**: Git (hosted on GitHub, GitLab, etc.)
- **Package Management**: `pip` with `requirements.txt`.
- **Linting/Formatting**: Tools like Black, Flake8, isort (common in Python projects).

## Windsurf Memory Bank

- **Format**: Markdown (.md)
- **Structure**: Defined by `.windsurfrules`.
- **Purpose**: Maintain project knowledge, context, and history.

## Notes

- Specific library versions are listed in `requirements.txt`.
- Configuration for external APIs (like Google Ads keys) might be stored in separate config files (e.g., `google-ads.yaml`) or environment variables, as referenced by Pydantic Settings.
