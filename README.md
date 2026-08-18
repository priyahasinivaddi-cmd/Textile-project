# Textile Waste Intelligence Platform

React + FastAPI + PostgreSQL platform for image-assisted garment triage, inventory, circularity scoring, sustainability estimates, reports, and human-reviewed AI decisions.

## Local run

1. Copy `.env.example` to `.env` and `backend/.env`; replace secrets.
2. Create `backend/.venv`, install `backend/requirements.txt`, then run `uvicorn main:app --reload` from `backend`.
3. Run `npm install` and `npm run dev` from the project root.
4. Open `http://localhost:5173`; API documentation is at `http://localhost:8000/docs`.

## Docker

Run `docker compose up --build` after creating `.env`. Web runs on port 5173 and API on port 8000.

## AWS EC2 deployment

The supported demo deployment runs the frontend, API, Celery worker, PostgreSQL, and Redis together on an AWS EC2 instance using `docker-compose.aws-demo.yml`. Start with [the AWS deployment guide](docs/aws-demo.md).

The frontend and API are served from the same public origin through Nginx. Configure that address as `PUBLIC_ORIGIN` in `.env.aws-demo`; the image build sets `VITE_API_URL` from it and the API uses it for CORS. PostgreSQL, Redis, and uploaded files use named Docker volumes on the EC2 host, so back them up before replacing or terminating the instance.

## Dataset and training

The pinned CC BY 4.0 source is `fnauman/fashion-second-hand-front-only-rgb`. Run `ml/data/download_dataset.py`, the validation/cleaning scripts, and then `ml/training/train_multitask.py --backbone b0 --allow-cpu` (omit `--allow-cpu` on GPU). B0 and B2 measured results are stored under `ml/artifacts/multitask`.

The promoted B0 checkpoint is a development model. Its quality gate failed, so every prediction is probabilistic and human review is required. RGB imagery is not laboratory fibre identification. Environmental outputs are configured estimates, not measurements.

## Validation

- Backend: `backend/.venv/Scripts/python -m pytest -q`
- Frontend: `npm run lint && npm run build`
- Health: `GET /health`
- Model: `GET /api/model/multitask/status`

See [docs](docs/architecture.md) for architecture, API, ML, database, deployment, and the measured model card.
