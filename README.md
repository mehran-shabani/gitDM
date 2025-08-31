# GitDM - Diabetes Management System

A version control system for diabetes patients across the care journey, powered by Django REST Framework and AI-assisted tooling. This repository is part of the Med3 project within the Helssa platform.

## 🚀 Quick Start (GitHub Codespaces)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/mehran-shabani/gitDM)

1. Open a Codespace using the button above
2. Wait ~2–3 minutes for automatic setup (SQLite, migrations, static)
3. Access the app via the forwarded port 8000
4. Default credentials (auto-created for dev):
   - Django Admin: `admin` / `admin123`

Note: Codespaces uses SQLite and local storage by default. External services (PostgreSQL/Redis/MinIO) are not started in this mode.

## 💻 Local Development (Docker)

1. Copy `.env.example` to `.env`
2. Start the stack:
   - `./bootstrap.sh`
3. Open `http://localhost:8000`

The Docker stack runs a single `web` service (SQLite + Django). The script applies migrations, collects static files, and ensures an admin user exists.

## 🧑‍💻 Manual (without Docker)

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env`
4. `python manage.py migrate`
5. `python manage.py runserver`

## 📚 API & Docs

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`
- Health Check: `/health/`
- API root: `/api/`

### Authentication

- Obtain token: `/api/token/`
- Refresh token: `/api/token/refresh/`

## 📁 Project Structure (key parts)

```bash
/
├── config/            # Project settings and URLs
├── gateway/           # API routers and health endpoint
├── gitdm/             # Core domain (User/Patient and related views)
├── encounters/        # Encounter app
├── intelligence/      # AI summarization app
├── laboratory/        # Lab results
├── pharmacy/          # Medications
├── references/        # Clinical references
├── versioning/        # Append-only versioning
├── security/          # Security-related utilities
├── cursoragent/       # Agent instructions and coding rules
├── tests/             # Test suite (pytest/pytest-django)
├── .devcontainer/     # Codespaces setup scripts
├── docker/            # Docker-related helpers (if any)
├── scripts/           # Helper scripts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pyproject.toml     # Ruff configuration
```

## 🔗 Helssa Note

This project aligns with Helssa conventions where applicable. Backward compatibility and naming consistency are kept in mind during development.

## 📝 Contributing

- Run tests: `pytest -v`
- Linting is configured via `pyproject.toml` for Ruff; use it if installed
- Follow clear commit messages and small, focused pull requests

## 📖 Additional Documentation

- `CODESPACES_SETUP.md` – details of the simplified Codespaces stack
- `.devcontainer/README.md` – development container workflow
- `cursoragent/AGENT.MD` – agent execution guide
