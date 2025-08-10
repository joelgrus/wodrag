-- ParadeDB Setup for CrossFit Workout RAG System
-- This script initializes ParadeDB with BM25 search and pgvector support

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_search;

-- 2. Create the workouts table
CREATE TABLE workouts (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    url TEXT,
    raw_text TEXT NOT NULL,
    workout TEXT NOT NULL,
    scaling TEXT,
    has_video BOOLEAN DEFAULT FALSE,
    has_article BOOLEAN DEFAULT FALSE,
    month_file TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata fields
    movements TEXT[],
    equipment TEXT[],
    workout_type TEXT,
    workout_name TEXT,
    one_sentence_summary TEXT,
    
    -- Vector embeddings (1536 dimensions for OpenAI text-embedding-3-small)
    workout_embedding vector(1536),
    summary_embedding vector(1536),
    
    -- Constraints: keep broad enough to cover corpus
    CONSTRAINT chk_workout_type CHECK (workout_type IS NULL OR workout_type IN (
        'strength', 'metcon', 'endurance', 'skill', 'benchmark', 'hero', 'girl', 'rest day'
    ))
);

-- 3. Create standard indexes
CREATE INDEX idx_workouts_date ON workouts(date);
CREATE INDEX idx_workouts_month_file ON workouts(month_file);
CREATE INDEX idx_workouts_type ON workouts(workout_type);

-- 4. Create vector similarity indexes
CREATE INDEX idx_workouts_embedding ON workouts 
USING ivfflat (workout_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_workouts_summary_embedding ON workouts 
USING ivfflat (summary_embedding vector_cosine_ops) WITH (lists = 100);

-- 5. Create ParadeDB BM25 index for full-text search
-- This replaces PostgreSQL's tsvector with ParadeDB's superior BM25 ranking
CREATE INDEX workouts_bm25_idx ON workouts
USING bm25 (id, workout, scaling, one_sentence_summary, workout_name)
WITH (
    key_field='id',
    text_fields='{
        "workout": {"tokenizer": {"type": "en_stem"}},
        "scaling": {"tokenizer": {"type": "en_stem"}}, 
        "one_sentence_summary": {"tokenizer": {"type": "en_stem"}},
        "workout_name": {"tokenizer": {"type": "en_stem"}}
    }'
);

-- 6. Create search views for common operations

-- View for semantic search on summaries
CREATE OR REPLACE VIEW workout_semantic_search AS
SELECT 
    id,
    date,
    workout_name,
    one_sentence_summary,
    movements,
    equipment,
    workout_type,
    summary_embedding
FROM workouts
WHERE summary_embedding IS NOT NULL;

-- View for BM25 text search
CREATE OR REPLACE VIEW workout_text_search AS
SELECT 
    id,
    date,
    workout_name,
    one_sentence_summary,
    workout,
    scaling,
    movements,
    equipment,
    workout_type
FROM workouts;
