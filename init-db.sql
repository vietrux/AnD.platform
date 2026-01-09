-- ==============================================================
-- AnD Platform - Complete Database Initialization Script
-- ==============================================================
-- This script initializes both GameCoreServer and Wrapper tables
-- Run this ONCE on a fresh PostgreSQL database
-- 
-- Last Updated: 2026-01-09
-- Includes: Pause tracking, cascade deletes, tick timing
--
-- Usage:
--   docker exec -i andplatform-postgres-1 psql -U postgres -d adg_core < init-db.sql
-- ==============================================================

-- Create database if not exists (run as superuser if needed)
-- CREATE DATABASE adg_core;

-- Connect to database
\c adg_core;

-- ==============================================================
-- EXTENSION: Enable UUID generation
-- ==============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================
-- 1. TEAMS TABLE (Wrapper - for authentication)
-- ==============================================================
CREATE TABLE IF NOT EXISTS teams (
    id              VARCHAR(8) PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    affiliation     VARCHAR(200),
    country         VARCHAR(50),
    ip_address      VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_teams_created ON teams(created_at);

COMMENT ON TABLE teams IS 'Teams for CTF competition - managed by Wrapper';

-- ==============================================================
-- 2. USERS TABLE (Wrapper - authentication/authorization)
-- ==============================================================
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'STUDENT',
    display_name    VARCHAR(100),
    affiliation     VARCHAR(200),
    team_id         VARCHAR(8) REFERENCES teams(id) ON DELETE SET NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_role ON users(role);
CREATE INDEX IF NOT EXISTS ix_users_team ON users(team_id);
CREATE INDEX IF NOT EXISTS ix_users_created ON users(created_at);

COMMENT ON TABLE users IS 'User accounts - ADMIN, TEACHER, STUDENT roles';

-- ==============================================================
-- 3. VULNBOXES TABLE (GameCoreServer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS vulnboxes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL UNIQUE,
    description     TEXT,
    path            VARCHAR(500) NOT NULL,
    docker_image    VARCHAR(200),
    created_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE vulnboxes IS 'Vulnerable box templates for games';

-- ==============================================================
-- 4. CHECKERS TABLE (GameCoreServer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS checkers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL UNIQUE,
    description     TEXT,
    file_path       VARCHAR(500) NOT NULL,
    module_name     VARCHAR(200) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE checkers IS 'Service checker scripts';

-- ==============================================================
-- 5. GAMES TABLE (GameCoreServer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS games (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                    VARCHAR(100) NOT NULL UNIQUE,
    description             TEXT,
    vulnbox_id              UUID REFERENCES vulnboxes(id) ON DELETE SET NULL,
    checker_id              UUID REFERENCES checkers(id) ON DELETE SET NULL,
    vulnbox_path            VARCHAR(500),
    checker_module          VARCHAR(200),
    status                  VARCHAR(20) DEFAULT 'draft' NOT NULL,
    tick_duration_seconds   INTEGER DEFAULT 60 NOT NULL,
    max_ticks               INTEGER,
    current_tick            INTEGER DEFAULT 0 NOT NULL,
    start_time              TIMESTAMP,
    end_time                TIMESTAMP,
    -- Pause tracking for proper tick calculation
    paused_at               TIMESTAMP,
    total_paused_seconds    FLOAT DEFAULT 0.0,
    -- Sequential tick progression (tracks when current tick started)
    current_tick_started_at TIMESTAMP,
    created_at              TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Status check constraint
ALTER TABLE games DROP CONSTRAINT IF EXISTS chk_games_status;
ALTER TABLE games ADD CONSTRAINT chk_games_status 
    CHECK (status IN ('draft', 'deploying', 'running', 'paused', 'finished'));

COMMENT ON TABLE games IS 'Attack-Defense CTF games';
COMMENT ON COLUMN games.paused_at IS 'Timestamp when game was paused (NULL if not paused)';
COMMENT ON COLUMN games.total_paused_seconds IS 'Total seconds spent in paused state';
COMMENT ON COLUMN games.current_tick_started_at IS 'When the current tick started for sequential tick progression';

-- ==============================================================
-- 6. GAME_TEAMS TABLE (GameCoreServer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS game_teams (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id         UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id         VARCHAR(100) NOT NULL,
    token           VARCHAR(64) UNIQUE,
    container_name  VARCHAR(200),
    container_ip    VARCHAR(50),
    ssh_username    VARCHAR(50),
    ssh_password    VARCHAR(100),
    ssh_port        INTEGER,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_game_teams_game_team ON game_teams(game_id, team_id);
CREATE INDEX IF NOT EXISTS ix_game_teams_team ON game_teams(team_id);
CREATE INDEX IF NOT EXISTS ix_game_teams_token ON game_teams(token);

COMMENT ON TABLE game_teams IS 'Teams participating in specific games with container info';

-- ==============================================================
-- 7. GAME_VULNBOXES TABLE (GameCoreServer - multi-vulnbox support)
-- ==============================================================
CREATE TABLE IF NOT EXISTS game_vulnboxes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id         UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    vulnbox_id      UUID NOT NULL REFERENCES vulnboxes(id) ON DELETE CASCADE,
    vulnbox_path    VARCHAR(500),
    docker_image    VARCHAR(200),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_game_vulnboxes_game_vulnbox ON game_vulnboxes(game_id, vulnbox_id);

COMMENT ON TABLE game_vulnboxes IS 'Many-to-many: games can have multiple vulnboxes';

-- ==============================================================
-- 8. TICKS TABLE (GameCoreServer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS ticks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id         UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    tick_number     INTEGER NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    flags_placed    INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_ticks_game_number ON ticks(game_id, tick_number);

-- Status check constraint
ALTER TABLE ticks DROP CONSTRAINT IF EXISTS chk_ticks_status;
ALTER TABLE ticks ADD CONSTRAINT chk_ticks_status 
    CHECK (status IN ('pending', 'active', 'completed', 'error'));

COMMENT ON TABLE ticks IS 'Game ticks/rounds';

-- ==============================================================
-- 9. FLAGS TABLE (GameCoreServer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS flags (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id         UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id         VARCHAR(100) NOT NULL,
    tick_id         UUID NOT NULL REFERENCES ticks(id) ON DELETE CASCADE,
    flag_type       VARCHAR(20) DEFAULT 'user',
    flag_value      VARCHAR(128) NOT NULL UNIQUE,
    valid_until     TIMESTAMP NOT NULL,
    is_stolen       BOOLEAN DEFAULT FALSE,
    stolen_count    INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_flags_team ON flags(team_id);
CREATE INDEX IF NOT EXISTS ix_flags_value ON flags(flag_value);
CREATE UNIQUE INDEX IF NOT EXISTS ix_flags_game_team_tick_type ON flags(game_id, team_id, tick_id, flag_type);

-- Flag type check constraint
ALTER TABLE flags DROP CONSTRAINT IF EXISTS chk_flags_type;
ALTER TABLE flags ADD CONSTRAINT chk_flags_type 
    CHECK (flag_type IN ('user', 'root'));

COMMENT ON TABLE flags IS 'Flags placed in team vulnboxes each tick';

-- ==============================================================
-- 10. FLAG_SUBMISSIONS TABLE (GameCoreServer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS flag_submissions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id             UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    attacker_team_id    VARCHAR(100) NOT NULL,
    flag_id             UUID REFERENCES flags(id) ON DELETE SET NULL,
    submitted_flag      VARCHAR(128) NOT NULL,
    status              VARCHAR(20) NOT NULL,
    points              INTEGER DEFAULT 0,
    submitted_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_submissions_attacker ON flag_submissions(attacker_team_id);
CREATE INDEX IF NOT EXISTS ix_submissions_flag ON flag_submissions(submitted_flag);
CREATE INDEX IF NOT EXISTS ix_submissions_game_attacker ON flag_submissions(game_id, attacker_team_id);
CREATE INDEX IF NOT EXISTS ix_submissions_time ON flag_submissions(submitted_at);

-- Status check constraint
ALTER TABLE flag_submissions DROP CONSTRAINT IF EXISTS chk_submissions_status;
ALTER TABLE flag_submissions ADD CONSTRAINT chk_submissions_status 
    CHECK (status IN ('accepted', 'rejected', 'duplicate', 'expired', 'own_flag', 'invalid'));

COMMENT ON TABLE flag_submissions IS 'Flag submission attempts by attackers';

-- ==============================================================
-- 11. SERVICE_STATUSES TABLE (GameCoreServer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS service_statuses (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id             UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id             VARCHAR(100) NOT NULL,
    tick_id             UUID NOT NULL REFERENCES ticks(id) ON DELETE CASCADE,
    status              VARCHAR(20) DEFAULT 'up',
    sla_percentage      FLOAT DEFAULT 100.0,
    error_message       TEXT,
    check_duration_ms   INTEGER,
    checked_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_service_status_team ON service_statuses(team_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_service_status_game_team_tick ON service_statuses(game_id, team_id, tick_id);

-- Status check constraint
ALTER TABLE service_statuses DROP CONSTRAINT IF EXISTS chk_service_status;
ALTER TABLE service_statuses ADD CONSTRAINT chk_service_status 
    CHECK (status IN ('up', 'down', 'error'));

COMMENT ON TABLE service_statuses IS 'SLA check results per team per tick';

-- ==============================================================
-- 12. SCOREBOARD TABLE (GameCoreServer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS scoreboard (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id         UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id         VARCHAR(100) NOT NULL,
    attack_points   INTEGER DEFAULT 0,
    defense_points  INTEGER DEFAULT 0,
    sla_points      INTEGER DEFAULT 0,
    total_points    INTEGER DEFAULT 0,
    rank            INTEGER DEFAULT 0,
    flags_captured  INTEGER DEFAULT 0,
    flags_lost      INTEGER DEFAULT 0,
    last_updated    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_scoreboard_team ON scoreboard(team_id);
CREATE INDEX IF NOT EXISTS ix_scoreboard_total ON scoreboard(total_points);
CREATE UNIQUE INDEX IF NOT EXISTS ix_scoreboard_game_team ON scoreboard(game_id, team_id);
CREATE INDEX IF NOT EXISTS ix_scoreboard_game_rank ON scoreboard(game_id, rank);

COMMENT ON TABLE scoreboard IS 'Real-time game scoreboard';

-- ==============================================================
-- INITIAL DATA: Default Admin Account
-- ==============================================================
-- Password: admin123 (BCrypt hash)
INSERT INTO users (username, password, role, display_name)
VALUES ('admin', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZRGdjGj/n3YJHgkIvPh2DPFT.Nqje', 'ADMIN', 'Administrator')
ON CONFLICT (username) DO NOTHING;

-- ==============================================================
-- VERIFICATION: Show created tables
-- ==============================================================
\echo ''
\echo '=============================================='
\echo '  Database Initialization Complete!'
\echo '=============================================='
\echo ''

SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

\echo ''
\echo 'Default admin account:'
\echo '  Username: admin'
\echo '  Password: admin123'
\echo ''
\echo 'IMPORTANT: Change the admin password after first login!'
\echo ''
