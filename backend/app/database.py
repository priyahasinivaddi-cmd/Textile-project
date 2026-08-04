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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_database_schema():
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password VARCHAR")
        )
        connection.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'operator'")
        )
        connection.execute(
            text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS waste_batch_id VARCHAR")
        )
        connection.execute(
            text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS collection_date VARCHAR")
        )
        connection.execute(
            text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'Pending'")
        )
        connection.execute(
            text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS uploaded_by VARCHAR DEFAULT 'Manufacturer'")
        )
        connection.execute(
            text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS assigned_to VARCHAR DEFAULT 'Recycling Facility'")
        )
        connection.execute(
            text(
                "UPDATE inventory "
                "SET waste_batch_id = CONCAT('WB-LEGACY-', id) "
                "WHERE waste_batch_id IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE inventory "
                "SET collection_date = CURRENT_DATE::VARCHAR "
                "WHERE collection_date IS NULL"
            )
        )
        connection.execute(
            text("UPDATE inventory SET status = 'Pending' WHERE status IS NULL")
        )
        connection.execute(
            text(
                "UPDATE inventory "
                "SET uploaded_by = 'Manufacturer' "
                "WHERE uploaded_by IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE inventory "
                "SET assigned_to = 'Recycling Facility' "
                "WHERE assigned_to IS NULL"
            )
        )
        connection.execute(
            text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS image_url VARCHAR")
        )
        connection.execute(
            text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS analysis_results VARCHAR")
        )
        connection.execute(
            text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL")
        )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_inventory_owner_id ON inventory (owner_id)")
        )
        connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users (organization_id)"))
        connection.execute(text("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS quantity_kg DOUBLE PRECISION"))
        connection.execute(text("ALTER TABLE waste_assessments ADD COLUMN IF NOT EXISTS audit_log TEXT DEFAULT '[]'"))
        connection.execute(text("UPDATE waste_assessments SET audit_log = '[]' WHERE audit_log IS NULL"))
