import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, ensure_database_schema
from app.routes import inventory, model, pipeline, user
from app.services.model_service import model_service

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
ensure_database_schema()

# Create static directory if not exists and mount it
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(user.router)
app.include_router(inventory.router)
app.include_router(pipeline.router)
app.include_router(model.router)


@app.on_event("startup")
def load_composition_model() -> None:
    """Load the trained model once when this API process starts."""
    model_service.load()


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
