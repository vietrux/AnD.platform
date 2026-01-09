-- Migration: Fix ALL foreign key constraints to cascade on game deletion
-- 
-- Problem: Multiple tables reference games without ON DELETE CASCADE,
-- which prevents games with related data from being deleted.
--
-- Solution: Drop and recreate all foreign key constraints with ON DELETE CASCADE
--
-- Run this migration with:
--   docker exec -i andplatform-postgres-1 psql -U postgres -d adg_core < migrations/fix_flag_submissions_cascade.sql

\echo '========================================='
\echo 'Fixing foreign key constraints for games'
\echo '========================================='

-- 1. flag_submissions -> games
\echo 'Fixing: flag_submissions.game_id...'
ALTER TABLE flag_submissions
DROP CONSTRAINT IF EXISTS flag_submissions_game_id_fkey;
ALTER TABLE flag_submissions
ADD CONSTRAINT flag_submissions_game_id_fkey
FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE;

-- 2. flags -> games
\echo 'Fixing: flags.game_id...'
ALTER TABLE flags
DROP CONSTRAINT IF EXISTS flags_game_id_fkey;
ALTER TABLE flags
ADD CONSTRAINT flags_game_id_fkey
FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE;

-- 3. game_teams -> games
\echo 'Fixing: game_teams.game_id...'
ALTER TABLE game_teams
DROP CONSTRAINT IF EXISTS game_teams_game_id_fkey;
ALTER TABLE game_teams
ADD CONSTRAINT game_teams_game_id_fkey
FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE;

-- 4. scoreboard -> games
\echo 'Fixing: scoreboard.game_id...'
ALTER TABLE scoreboard
DROP CONSTRAINT IF EXISTS scoreboard_game_id_fkey;
ALTER TABLE scoreboard
ADD CONSTRAINT scoreboard_game_id_fkey
FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE;

-- 5. service_statuses -> games
\echo 'Fixing: service_statuses.game_id...'
ALTER TABLE service_statuses
DROP CONSTRAINT IF EXISTS service_statuses_game_id_fkey;
ALTER TABLE service_statuses
ADD CONSTRAINT service_statuses_game_id_fkey
FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE;

-- 6. ticks -> games
\echo 'Fixing: ticks.game_id...'
ALTER TABLE ticks
DROP CONSTRAINT IF EXISTS ticks_game_id_fkey;
ALTER TABLE ticks
ADD CONSTRAINT ticks_game_id_fkey
FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE;

\echo ''
\echo '========================================='
\echo 'All foreign key constraints fixed!'
\echo 'Games can now be deleted properly.'
\echo '========================================='

