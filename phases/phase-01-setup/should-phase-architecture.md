# معماری فاز ۰۱ (Setup)

- Framework: Django + DRF, Celery, Redis, Postgres, MinIO
- Boundary: سرویس مستقل، بدون ادغام با Helssa
- Components:
  - config/ (ASGI, settings, celery)
  - apps/: patients_core, diab_encounters, diab_labs, diab_medications, records_versioning, ai_summarizer, clinical_refs
  - api/: routers (health)
  - infra/: docker, env
- Data Flow:
  Client → API(health) → DB readiness
- Deploy: Docker Compose (web, worker, beat, db, redis, minio)
- Security: فقط Admin می‌تواند User بسازد (مدل پیش‌فرض)