from celery import Celery
from app.config import settings

celery_app = Celery("textile", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"], task_track_started=True)


@celery_app.task(name="analysis.execute")
def execute(job_id: str):
    from app.services.analysis_job_service import execute_analysis_job
    execute_analysis_job(job_id)
