import os

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, ensure_database_schema
from app.services.model_service import model_service
from app.services.multitask_model_service import multitask_model_service
from app.models import assessment as _assessment_model  # register ORM model before create_all
from app.models import analysis as _analysis_model
from app.models import notification as _notification_model
from app.models import operations as _operations_model
from app.routes import admin, analysis_history, analysis_jobs, analytics, assessments, comprehensive_reports, inventory, model, notifications, pipeline, platform, recommendations, sustainability_reports, user
from app.config import settings
from app.middleware import operations_middleware
from app.services.destination_model_service import destination_model_service

app = FastAPI(
    title="Textile Waste Intelligence API",
    version="1.0.0",
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None if settings.app_env == "production" else "/redoc",
    openapi_url=None if settings.app_env == "production" else "/openapi.json",
)
app.middleware("http")(operations_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
ensure_database_schema()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(user.router)
app.include_router(inventory.router)
app.include_router(assessments.router)
app.include_router(analytics.router)
app.include_router(recommendations.router)
app.include_router(sustainability_reports.router)
app.include_router(comprehensive_reports.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(model.router)
app.include_router(pipeline.router)
app.include_router(analysis_history.router)
app.include_router(analysis_jobs.router)
app.include_router(platform.router)

# Versioned aliases are additive, preserving existing clients while exposing a
# stable production namespace. Existing router prefixes remain visible in the
# generated OpenAPI document during the compatibility period.
for versioned_router in (user.router, inventory.router, assessments.router, analytics.router, recommendations.router, sustainability_reports.router, comprehensive_reports.router, admin.router, notifications.router, model.router, pipeline.router, analysis_history.router):
    app.include_router(versioned_router, prefix="/api/v1", include_in_schema=False)


@app.get("/")
def home():
    return {"name": app.title, "version": app.version, "docs": "/docs"}


@app.get("/health", tags=["operations"])
def health(response: Response):
    database_status = "ready"
    try:
        with engine.connect():
            pass
    except Exception:
        database_status = "unavailable"
    legacy_status = model_service.status()
    multitask_status = multitask_model_service.status()
    model_ready = multitask_status["loaded"] or legacy_status["model_loaded"]
    if database_status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ready" if database_status == "ready" else "degraded",
        "database": database_status,
        "image_model": "ready" if model_ready else "unavailable",
        "analysis_mode": "development_multitask_model" if multitask_status["loaded"] else ("trained_legacy_model" if legacy_status["model_loaded"] else "deterministic_fallback"),
        "quality_gate_passed": multitask_status["quality_gate_passed"] if multitask_status["loaded"] else False,
    }


@app.get("/health/db", tags=["operations"])
def health_database(response: Response):
    try:
        with engine.connect():
            return {"status": "ready"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}


@app.get("/health/ml", tags=["operations"])
def health_ml():
    multitask = multitask_model_service.status()
    destination = destination_model_service.status()
    return {
        "status": "ready" if multitask["loaded"] and destination["loaded"] else "degraded",
        "garment_model": multitask,
        "destination_model": {key: destination.get(key) for key in ("loaded", "trained_at", "quality_gate_passed", "error")},
    }


@app.get("/db-test")
def db_test():
    try:
        with engine.connect():
            return {"status": "DB Connected"}
    except Exception:
        return {"status": "DB Failed"}
