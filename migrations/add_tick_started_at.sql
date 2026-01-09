-- Migration: Add current_tick_started_at column for sequential tick progression
-- This field tracks when the current tick started, enabling proper pause/resume behavior
--
-- Run this migration with:
--   docker exec -i andplatform-postgres-1 psql -U postgres -d adg_core < migrations/add_tick_started_at.sql

\echo 'Adding current_tick_started_at column to games table...'

ALTER TABLE games
ADD COLUMN IF NOT EXISTS current_tick_started_at TIMESTAMP;

\echo 'Done! games.current_tick_started_at column added.'
