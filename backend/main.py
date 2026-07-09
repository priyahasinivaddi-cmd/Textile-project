from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, ensure_database_schema
from app.routes import inventory, user

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

app.include_router(user.router)
app.include_router(inventory.router)


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
