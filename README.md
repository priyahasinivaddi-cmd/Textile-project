# Textile Waste Intelligence Platform

React + FastAPI + PostgreSQL platform for image-assisted garment triage, inventory, circularity scoring, sustainability estimates, reports, and human-reviewed AI decisions.

## Local run

1. Copy `.env.example` to `.env` and `backend/.env`; replace secrets.
2. Create `backend/.venv`, install `backend/requirements.txt`, then run `uvicorn main:app --reload` from `backend`.
3. Run `npm install` and `npm run dev` from the project root.
4. Open `http://localhost:5173`; API documentation is at `http://localhost:8000/docs`.

## Docker

Run `docker compose up --build` after creating `.env`. Web runs on port 5173 and API on port 8000.

## Vercel Docker deployment

The repository includes a Vercel container for the frontend (`Dockerfile.vercel`) and one for the API (`backend/Dockerfile.vercel`). Deploy them as two Vercel projects connected to the same Git repository:

1. Create the API project with **Root Directory** set to `backend`. Add `APP_ENV=production`, a strong `SECRET_KEY`, the Supabase transaction-pooler `DATABASE_URL`, `DB_SSLMODE=require`, `TASK_MODE=local`, and the server-only S3 storage settings. Deploy it and copy its HTTPS URL.
2. Create the web project with **Root Directory** left at the repository root. Add `VITE_API_URL` with the API project's HTTPS URL. Deploy it and copy its HTTPS URL.
3. In the API project, set `CORS_ORIGINS` to the exact web-project URL and redeploy both projects.

Vercel detects each `Dockerfile.vercel`, builds the image, and routes the project to its HTTP container. The frontend Nginx configuration handles React routes such as `/login` and `/dashboard`.

Docker Compose remains the local/full-stack setup. Its PostgreSQL, Redis, Celery worker, and persistent volumes are not deployed by these two web containers. Production must use an external PostgreSQL database and S3-compatible upload storage. Long-running Celery work requires a separate worker host; `TASK_MODE=local` keeps jobs inside API requests and is the compatible Vercel setting.

For Supabase Storage use `STORAGE_BACKEND=s3`, `S3_BUCKET=garment-uploads`, `S3_REGION=ap-south-1`, and `S3_ENDPOINT_URL=https://sgrhnvthiydiolldpiwg.storage.supabase.co/storage/v1/s3`. Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` only in the API project's Vercel environment; never expose them through a `VITE_*` variable.

## Dataset and training

The pinned CC BY 4.0 source is `fnauman/fashion-second-hand-front-only-rgb`. Run `ml/data/download_dataset.py`, the validation/cleaning scripts, and then `ml/training/train_multitask.py --backbone b0 --allow-cpu` (omit `--allow-cpu` on GPU). B0 and B2 measured results are stored under `ml/artifacts/multitask`.

The promoted B0 checkpoint is a development model. Its quality gate failed, so every prediction is probabilistic and human review is required. RGB imagery is not laboratory fibre identification. Environmental outputs are configured estimates, not measurements.

## Validation

- Backend: `backend/.venv/Scripts/python -m pytest -q`
- Frontend: `npm run lint && npm run build`
- Health: `GET /health`
- Model: `GET /api/model/multitask/status`

See [docs](docs/architecture.md) for architecture, API, ML, database, deployment, and the measured model card.
