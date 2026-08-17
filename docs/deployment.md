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

## Vercel containers

Use two Vercel projects from this repository. The frontend project uses the repository root and `Dockerfile.vercel`; the API project uses `backend` as its Root Directory and `backend/Dockerfile.vercel`.

The API uses the Supabase transaction pooler because Vercel is autoscaling and IPv4-based. Set its pooler `DATABASE_URL`, `DB_SSLMODE=require`, `APP_ENV=production`, `SECRET_KEY`, `CORS_ORIGINS`, `TASK_MODE=local`, and S3-compatible storage variables in the API project's Vercel environment. Set the frontend project's `VITE_API_URL` to the deployed API HTTPS URL. Environment-variable changes require a redeployment.

Supabase Storage uses the private `garment-uploads` bucket. Its S3 access key and secret are server-only credentials that bypass Storage RLS, so store them only as `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in the API project. Use `S3_REGION=ap-south-1` and `S3_ENDPOINT_URL=https://sgrhnvthiydiolldpiwg.storage.supabase.co/storage/v1/s3`.

Vercel web containers do not replace the PostgreSQL, Redis, Celery worker, or persistent volumes in `docker-compose.yml`. Host long-running workers separately if asynchronous Celery processing is required.

## Release policy

- `/health` must return HTTP 200. Database failure returns HTTP 503 and must block rollout.
- `/health/ml` may report `degraded`. The current development model failed its quality gate, so predictions require human review and must not be presented as definitive fibre identification or disposal instructions.
- Production API documentation is disabled by default.
- Review and commit the exact release contents; do not deploy a dirty working tree.
- Keep a previous image tag available for rollback.
