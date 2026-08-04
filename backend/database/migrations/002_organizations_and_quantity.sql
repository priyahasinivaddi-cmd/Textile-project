BEGIN;
CREATE TABLE IF NOT EXISTS organizations (id SERIAL PRIMARY KEY, name VARCHAR NOT NULL UNIQUE);
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users (organization_id);
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS quantity_kg DOUBLE PRECISION;
CREATE INDEX IF NOT EXISTS ix_inventory_quantity_kg ON inventory (quantity_kg);
COMMIT;

-- Ownership and organization values must be backfilled from verified business
-- mappings. Generic uploaded_by labels are intentionally not treated as users.
