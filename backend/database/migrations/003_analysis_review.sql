CREATE TABLE IF NOT EXISTS analysis_records (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_url VARCHAR NOT NULL,
    model_name VARCHAR NOT NULL,
    model_version VARCHAR NOT NULL,
    ai_destination VARCHAR,
    ai_confidence DOUBLE PRECISION,
    manual_review_required BOOLEAN NOT NULL DEFAULT TRUE,
    result_json TEXT NOT NULL,
    review_status VARCHAR NOT NULL DEFAULT 'pending',
    final_destination VARCHAR,
    reviewer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    review_reason TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_analysis_records_user_id ON analysis_records(user_id);
CREATE INDEX IF NOT EXISTS ix_analysis_records_review_status ON analysis_records(review_status);
CREATE INDEX IF NOT EXISTS ix_analysis_records_created_at ON analysis_records(created_at);
