import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@localhost:5432/textile_db",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def ensure_database_schema():
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password VARCHAR")
        )
        connection.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'operator'")
        )
