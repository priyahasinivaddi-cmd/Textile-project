import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, ensure_database_schema
from app.models import assessment as _assessment_model  # register ORM model before create_all
from app.routes import analytics, assessments, inventory, model, pipeline, recommendations, sustainability_reports, user

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
app.include_router(model.router)
app.include_router(pipeline.router)


@app.get("/")
def home():
    return {"message": "FastAPI Backend Running"}


@app.get("/db-test")
def db_test():
    try:
        with engine.connect():
            return {"status": "DB Connected"}
    except Exception:
        return {"status": "DB Failed"}
