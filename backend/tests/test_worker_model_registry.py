from app.database import Base
from app.services import analysis_job_service  # noqa: F401
from sqlalchemy.orm import configure_mappers


def test_worker_registers_users_and_analysis_tables():
    configure_mappers()
    assert {"users", "analysis_jobs", "analysis_records", "notifications"}.issubset(Base.metadata.tables)
    assert Base.metadata.tables["analysis_jobs"].c.user_id.foreign_keys
