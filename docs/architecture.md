# Architecture

The browser uses a React/Vite frontend. FastAPI owns authentication, authorization, uploads, inference orchestration, inventory, analyses, reviews, analytics, notifications, and reports. PostgreSQL is the source of truth; images are stored outside database rows. The EfficientNet service loads the promoted B0 artifact once per API process. Deterministic recommendations and sustainability calculations remain separate from probabilistic model outputs.

Flow: authenticated upload → bounded image validation → EfficientNet multitask inference → transparent fallback/business rules → persisted analysis → manual accept/override → feedback export.

The production Compose stack contains Nginx, FastAPI, PostgreSQL, Redis, and a Celery inference worker. The API persists an analysis job before dispatch, the worker updates progress and stores the final analysis, and the browser polls the authenticated job endpoint. `TASK_MODE=local` retains a lightweight background-task fallback for development.

Uploads use the `StorageProvider` interface. `LocalStorageProvider` writes to the persistent development volume; `S3StorageProvider` uses an S3-compatible bucket configured entirely through environment variables.

Every API response carries a request ID and secure headers. Structured access logs include the endpoint, HTTP status, and latency. Model execution logs include the job, model version, analysis ID, and inference latency.
