# API

## Production endpoints

- `POST /api/v1/analysis/jobs` queues a validated garment image and returns HTTP 202.
- `GET /api/v1/analysis/jobs/{job_id}` returns persisted progress and the final result.
- `GET /api/v1/search?q=` searches authorized garments and analyses.
- `GET /api/v1/models/insights` exposes measured artifact metadata.
- `POST /api/v1/models/registry/sync` registers artifacts for administrator review.
- `POST /api/v1/models/registry/{id}/promote` promotes only candidates that passed their quality gate.
- `GET /health`, `/health/db`, and `/health/ml` provide separate readiness probes.

Legacy routes remain available during the compatibility period. Authentication, authorization and rate limiting apply equally to versioned endpoints.

Interactive OpenAPI documentation is available at `/docs`.

Core groups:

- `/user`: register, login, profile, administrator user management.
- `/pipeline/analyze`: authenticated analysis upload and persistence.
- `/api/model`: legacy and multitask status/prediction.
- `/api/analyses`: history, details, human review, feedback CSV.
- `/inventory`: scoped CRUD and PDF reports.
- `/api/assessments`, `/api/analytics`, `/api/recommendations`: circularity services.
- `/api/reports`, `/api/sustainability/reports`: database-backed PDF/CSV/Excel.
- `/api/notifications`: authenticated alerts and announcements.

Bearer access tokens are required unless an operation is explicitly public. OpenAPI response schemas expose model confidence, manual-review status, model version, and the AI disclaimer.
