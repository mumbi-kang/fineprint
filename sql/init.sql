-- Runs automatically the first time the Postgres container starts.
CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector, for later weeks

CREATE TABLE IF NOT EXISTS contracts (
    id          SERIAL PRIMARY KEY,
    title       TEXT UNIQUE NOT NULL,
    source      TEXT NOT NULL DEFAULT 'upload',          -- 'cuad' or 'upload'
    split       TEXT CHECK (split IN ('dev', 'test')),   -- NULL for user uploads
    char_len    INTEGER,
    text_file   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ground truth from CUAD. Model predictions get their own table in week 3.
CREATE TABLE IF NOT EXISTS clause_labels (
    id           SERIAL PRIMARY KEY,
    contract_id  INTEGER NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    clause_type  TEXT NOT NULL,
    span_text    TEXT NOT NULL,
    span_start   INTEGER NOT NULL,
    span_end     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_labels_contract ON clause_labels(contract_id);
CREATE INDEX IF NOT EXISTS idx_labels_type ON clause_labels(clause_type);
