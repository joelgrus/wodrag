-- Migration: Add one_sentence_summary field for workout summaries
-- Date: 2025-08-05

-- Add one_sentence_summary column to workouts table
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS one_sentence_summary TEXT;

-- Create B-tree index for efficient text searches
CREATE INDEX IF NOT EXISTS idx_workouts_one_sentence_summary ON workouts (one_sentence_summary);

-- Create a GIN index for full-text search on the summary
CREATE INDEX IF NOT EXISTS idx_workouts_one_sentence_summary_gin 
ON workouts USING GIN (to_tsvector('english', COALESCE(one_sentence_summary, '')));

-- Example queries for reference:
-- Find workouts with summaries containing "AMRAP":
-- SELECT * FROM workouts WHERE one_sentence_summary ILIKE '%AMRAP%';

-- Full-text search for summaries mentioning "pull-ups and deadlifts":
-- SELECT * FROM workouts 
-- WHERE to_tsvector('english', one_sentence_summary) @@ to_tsquery('english', 'pull-ups & deadlifts');

-- Find workouts with summaries mentioning hero workouts:
-- SELECT * FROM workouts WHERE one_sentence_summary ILIKE '%hero%';