-- Migration: Add game_vulnboxes junction table for multi-vulnbox support
-- Run this after updating to the new code

CREATE TABLE IF NOT EXISTS game_vulnboxes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    vulnbox_id UUID NOT NULL REFERENCES vulnboxes(id) ON DELETE CASCADE,
    vulnbox_path VARCHAR(500),
    docker_image VARCHAR(200),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
);

-- Create unique index to prevent duplicate vulnbox assignments
CREATE UNIQUE INDEX IF NOT EXISTS ix_game_vulnboxes_game_vulnbox 
ON game_vulnboxes(game_id, vulnbox_id);

-- Optional: Migrate existing vulnbox assignments from games table
INSERT INTO game_vulnboxes (game_id, vulnbox_id, vulnbox_path)
SELECT id, vulnbox_id, vulnbox_path 
FROM games 
WHERE vulnbox_id IS NOT NULL
ON CONFLICT DO NOTHING;
