# Database

PostgreSQL stores users, organizations, inventory, sustainability assessments, platform announcements, and analysis review records. SQL migrations are in `backend/database/migrations`.

Analysis records preserve the original model output, model version, AI destination/confidence, review state, human destination, reviewer, reason, and timestamps. Images are referenced by URL and are not stored as PostgreSQL blobs.

Apply numbered SQL migrations in order for existing deployments. New installations also register ORM models during application startup.
