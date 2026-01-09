-- Add pause tracking to games table
-- This migration adds fields to track pause/resume state for proper tick calculation

-- Add pause tracking columns to games table
ALTER TABLE games 
ADD COLUMN IF NOT EXISTS paused_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS total_paused_seconds FLOAT DEFAULT 0.0;

-- Add comment for documentation
COMMENT ON COLUMN games.paused_at IS 'Timestamp when game was paused (NULL if not paused)';
COMMENT ON COLUMN games.total_paused_seconds IS 'Total seconds spent in paused state';

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'games' 
AND column_name IN ('paused_at', 'total_paused_seconds');
