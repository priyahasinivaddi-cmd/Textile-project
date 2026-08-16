# Deployment

## Before the first deployment

1. Copy `.env.example` to `.env`.
2. Set `APP_ENV=production`.
3. Generate unique values for `POSTGRES_PASSWORD` and `SECRET_KEY`. The JWT secret must be at least 32 random characters and must not contain example placeholders.
4. Set `VITE_API_URL` to the public HTTPS API URL and `CORS_ORIGINS` to the exact public HTTPS web origin. Do not leave localhost values.
5. Choose durable upload storage. For multi-instance hosting use `STORAGE_BACKEND=s3` and configure the bucket; for one server, back up the `uploads` Docker volume.
6. Run `npm run check`, `npm audit --omit=dev`, and `backend/.venv/Scripts/python -m pytest -q`.
7. On a machine with Docker, run `docker compose config`, `docker compose build`, and `docker compose up -d`. Confirm `/health`, `/health/db`, and `/health/ml`.

Terminate TLS at a trusted reverse proxy or load balancer. Do not expose PostgreSQL or Redis publicly. Back up the PostgreSQL and upload volumes, test restoration, and mount only reviewed model artifacts.

## Release policy

- `/health` must return HTTP 200. Database failure returns HTTP 503 and must block rollout.
- `/health/ml` may report `degraded`. The current development model failed its quality gate, so predictions require human review and must not be presented as definitive fibre identification or disposal instructions.
- Production API documentation is disabled by default.
- Review and commit the exact release contents; do not deploy a dirty working tree.
- Keep a previous image tag available for rollback.
