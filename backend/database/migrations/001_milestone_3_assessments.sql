-- Milestone 3 schema migration for projects that do not yet use Alembic.
-- Back up the database before running this script in production.

BEGIN;

ALTER TABLE inventory
    ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_inventory_owner_id ON inventory (owner_id);

CREATE TABLE IF NOT EXISTS waste_assessments (
    id SERIAL PRIMARY KEY,
    waste_batch_id INTEGER NOT NULL UNIQUE REFERENCES inventory(id) ON DELETE CASCADE,
    quantity_kg DOUBLE PRECISION NOT NULL,
    recyclability_score DOUBLE PRECISION NOT NULL,
    condition_score DOUBLE PRECISION NOT NULL,
    reuse_score DOUBLE PRECISION NOT NULL,
    environmental_benefit_score DOUBLE PRECISION NOT NULL,
    processing_feasibility_score DOUBLE PRECISION NOT NULL,
    material_recovery_score DOUBLE PRECISION NOT NULL,
    sustainability_score DOUBLE PRECISION NOT NULL,
    circularity_score DOUBLE PRECISION NOT NULL,
    circularity_category VARCHAR NOT NULL,
    co2_saved_kg DOUBLE PRECISION NOT NULL,
    water_saved_litres DOUBLE PRECISION NOT NULL,
    landfill_reduction_kg DOUBLE PRECISION NOT NULL,
    recoverable_material_kg DOUBLE PRECISION NOT NULL,
    recommended_action VARCHAR NOT NULL,
    recommended_processing_method VARCHAR NOT NULL,
    recommendation_reason TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_waste_assessments_waste_batch_id ON waste_assessments (waste_batch_id);
CREATE INDEX IF NOT EXISTS ix_waste_assessments_circularity_category ON waste_assessments (circularity_category);

COMMIT;
