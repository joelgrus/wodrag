-- Migration: Add metadata fields for movements, equipment, workout_type, and workout_name
-- Date: 2025-01-04

-- Add new columns to workouts table
ALTER TABLE workouts
ADD COLUMN IF NOT EXISTS movements JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS equipment JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS workout_type TEXT,
ADD COLUMN IF NOT EXISTS workout_name TEXT;

-- Create GIN indexes for efficient JSONB array queries
CREATE INDEX IF NOT EXISTS idx_workouts_movements_gin ON workouts USING GIN (movements);
CREATE INDEX IF NOT EXISTS idx_workouts_equipment_gin ON workouts USING GIN (equipment);

-- Create B-tree indexes for text fields
CREATE INDEX IF NOT EXISTS idx_workouts_workout_type ON workouts (workout_type);
CREATE INDEX IF NOT EXISTS idx_workouts_workout_name ON workouts (workout_name);

-- Add CHECK constraint for workout_type to ensure valid values
ALTER TABLE workouts
ADD CONSTRAINT chk_workout_type CHECK (
    workout_type IS NULL OR 
    workout_type IN ('metcon', 'strength', 'hero', 'benchmark', 'team', 'endurance', 'skill', 'rest')
);

-- Example queries for reference:
-- Find workouts containing pull-ups:
-- SELECT * FROM workouts WHERE movements @> '["pull up"]';

-- Find workouts with barbell OR dumbbell:
-- SELECT * FROM workouts WHERE equipment ?| array['barbell', 'dumbbell'];

-- Find all AMRAPs with pull-ups:
-- SELECT * FROM workouts WHERE workout_type = 'amrap' AND movements @> '["pull up"]';

-- Find workouts containing both pull-ups and deadlifts:
-- SELECT * FROM workouts WHERE movements @> '["pull up", "deadlift"]';

-- Find Hero workout "Murph":
-- SELECT * FROM workouts WHERE workout_name = 'Murph';