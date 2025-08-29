# GitDM Deployment & Validation Report

## Branch
- Main workspace branch (current working tree)

## Summary
- Implemented and validated Docker setups: simple (SQLite) and advanced (Postgres, Redis, MinIO)
- Enabled API documentation: Swagger UI (/api/docs), Redoc (/api/redoc), JSON schema (/api/schema)
- Added health (/api/health) and readiness (/api/ready) endpoints
- Added export endpoint: /api/export/patient/<pk>/
- Confirmed JWT auth endpoints work: /api/token, /api/token/refresh
- Ensured AI summarizer admin configured and accessible
- Tests: 67 passed, 7 skipped, 2 warnings

## Run Modes

### Simple (SQLite)
- Copy .env.example to .env and keep `USE_SQLITE=True`
- Start: `./scripts/start-simple.sh`
- Stop: `./scripts/stop-simple.sh`

### Advanced (Postgres, Redis, MinIO)
- Copy .env.example to .env and set `USE_SQLITE=False`
- Start: `./scripts/start-advanced.sh`
- Stop: `./scripts/stop-advanced.sh`
- Services: web:8000, db:5432, redis:6379, minio:9000 (console:9001)

## Endpoints
- Root API: /api/
- Health: /api/health/
- Ready: /api/ready/
- JWT token: /api/token/ (POST username, password)
- JWT refresh: /api/token/refresh/
- Patients: /api/patients/
- Encounters: /api/encounters/
- Labs: /api/labs/
- Medications: /api/meds/
- Clinical refs: /api/refs/
- Versions list: /api/versions/<resource_type>/<id>/
- Versions revert: /api/versions/<resource_type>/<id>/revert/
- Export patient: /api/export/patient/<pk>/
- Schema (JSON): /api/schema/
- Swagger UI: /api/docs/
- Redoc: /api/redoc/

## Notes & Improvements
- DRF default permissions set to AllowAny for schema/docs/tests; protect in production
- Celery/Redis wired via env; workers defined in docker-compose.yml
- MinIO is provisioned but app uses default Django storage; wire S3/MinIO using django-storages when needed
- Admin: AISummary configured; filters, search, readonly fields validated by tests
- Robust versioning snapshot conversion for Decimal and date to avoid JSON serialization errors

## Strengths
- Clean modular Django apps (patients, encounters, labs, meds, versioning)
- Automated schema/docs with drf-spectacular
- CI-friendly tests and pytest-django config
- Container-first configuration with simple/advanced modes

## Weaknesses / Risks
- Open read on export endpoint for tests; must tighten permissions for production
- Default AllowAny in REST_FRAMEWORK; set proper permission classes in production
- MinIO storage not fully integrated; future enhancement for media/static

## How to Validate Locally
1. Create virtualenv, install requirements-dev.txt
2. Run tests:
   - `export TEST_USER_PASSWORD=Test1234!`
   - `pytest -q`
3. Start Docker (simple or advanced)
4. Open `http://localhost:8000/api/docs/` and `http://localhost:8000/api/redoc/`
5. Obtain JWT and call endpoints

## Changelog of Key Edits
- Added Redoc and root health route in config/urls.py
- Added readiness endpoint in api/urls.py
- Added export view and relaxed auth for test, output via DRF Response
- Added AISummary migrations/fields to match tests (UUID pk, updated_at)
- Admin settings for AISummary per tests
- Versioning: pagination guard and AllowAny read; serializer & JSON conversion for Decimal/date
- Docker: introduced docker-compose.simple.yml, advanced compose with MinIO; scripts to start/stop
- .env.example added per tests
- README updated with run instructions