-- Supabase Database Setup for CrossFit Workout RAG System
-- Run this in your Supabase SQL Editor

-- 1. Create the workouts table
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
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Add indexes for common queries
CREATE INDEX idx_workouts_date ON workouts(date);
CREATE INDEX idx_workouts_month_file ON workouts(month_file);

-- 3. Enable full-text search on workout content
ALTER TABLE workouts ADD COLUMN workout_search_vector tsvector;
CREATE INDEX idx_workouts_search ON workouts USING gin(workout_search_vector);

-- 4. Trigger to auto-update search vector
CREATE OR REPLACE FUNCTION update_workout_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.workout_search_vector := to_tsvector('english', NEW.workout || ' ' || COALESCE(NEW.scaling, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_workouts_search_vector
  BEFORE INSERT OR UPDATE ON workouts
  FOR ROW EXECUTE FUNCTION update_workout_search_vector();

-- 5. Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 6. Add vector column for workout embeddings (1536 dimensions for OpenAI embeddings)
ALTER TABLE workouts ADD COLUMN workout_embedding vector(1536);

-- 7. Add index for vector similarity search
CREATE INDEX ON workouts USING ivfflat (workout_embedding vector_cosine_ops)
WITH (lists = 100);

-- Example queries you can use:

-- Full-text search (keyword matching):
/*
SELECT *, ts_rank(workout_search_vector, to_tsquery('english', 'burpee & squat')) as rank
FROM workouts 
WHERE workout_search_vector @@ to_tsquery('english', 'burpee & squat')
ORDER BY rank DESC;
*/

-- Vector search (semantic similarity):
/*
SELECT *, 1 - (workout_embedding <=> '[your_query_embedding_vector]') as similarity
FROM workouts 
ORDER BY workout_embedding <=> '[your_query_embedding_vector]'
LIMIT 10;
*/

-- Hybrid search (combine both):
/*
SELECT *, 
  ts_rank(workout_search_vector, to_tsquery('english', 'burpee')) * 0.3 +
  (1 - (workout_embedding <=> '[query_vector]')) * 0.7 as combined_score
FROM workouts 
WHERE workout_search_vector @@ to_tsquery('english', 'burpee')
ORDER BY combined_score DESC;
*/