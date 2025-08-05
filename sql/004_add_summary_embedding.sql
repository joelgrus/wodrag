-- Add summary_embedding column to store embeddings generated from one_sentence_summary
-- This allows us to maintain both full-text embeddings and summary embeddings for comparison

ALTER TABLE workouts
ADD COLUMN summary_embedding vector(1536);

-- Create an index for efficient similarity search on summary embeddings
CREATE INDEX IF NOT EXISTS workouts_summary_embedding_idx 
ON workouts 
USING ivfflat (summary_embedding vector_cosine_ops)
WITH (lists = 100);

-- Add comment explaining the column
COMMENT ON COLUMN workouts.summary_embedding IS 'Embedding vector generated from one_sentence_summary field using OpenAI text-embedding-3-small model';