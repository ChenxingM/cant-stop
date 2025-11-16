-- Migration: Add Encounter System Tables
-- Date: 2025-01-16
-- Description: Adds tables for encounter states, player effects, and encounter history

-- Table: player_encounter_states
-- Stores active encounter states for players
CREATE TABLE IF NOT EXISTS player_encounter_states (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id VARCHAR(50) NOT NULL,
    encounter_name VARCHAR(100) NOT NULL,
    state VARCHAR(20) NOT NULL,  -- waiting_choice, processing, completed, follow_up
    selected_choice VARCHAR(100),
    follow_up_trigger VARCHAR(100),
    context_data TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE INDEX IF NOT EXISTS idx_encounter_states_player ON player_encounter_states(player_id);
CREATE INDEX IF NOT EXISTS idx_encounter_states_state ON player_encounter_states(state);

-- Table: player_effects
-- Stores buffs and delayed effects for players
CREATE TABLE IF NOT EXISTS player_effects (
    effect_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id VARCHAR(50) NOT NULL,
    effect_type VARCHAR(50) NOT NULL,  -- buff, delayed_effect
    effect_name VARCHAR(100) NOT NULL,
    effect_data TEXT,  -- JSON
    duration INTEGER DEFAULT 1,  -- -1 for permanent
    remaining_turns INTEGER,
    trigger_turn INTEGER,  -- For delayed effects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE INDEX IF NOT EXISTS idx_player_effects_player ON player_effects(player_id);
CREATE INDEX IF NOT EXISTS idx_player_effects_type ON player_effects(effect_type);
CREATE INDEX IF NOT EXISTS idx_player_effects_trigger ON player_effects(trigger_turn);

-- Table: encounter_history
-- Stores encounter history for achievements and statistics
CREATE TABLE IF NOT EXISTS encounter_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id VARCHAR(50) NOT NULL,
    encounter_name VARCHAR(100) NOT NULL,
    selected_choice VARCHAR(100),
    result TEXT,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE INDEX IF NOT EXISTS idx_encounter_history_player ON encounter_history(player_id);
CREATE INDEX IF NOT EXISTS idx_encounter_history_name ON encounter_history(encounter_name);
CREATE INDEX IF NOT EXISTS idx_encounter_history_time ON encounter_history(triggered_at);

-- Update game_sessions table to add encounter-related fields if they don't exist
-- Note: SQLite doesn't support ALTER TABLE IF COLUMN NOT EXISTS, so we check manually
-- These columns might need to be added manually if the table already exists:
-- - next_dice_count INTEGER
-- - has_extra_dice_risk INTEGER (0 or 1 as boolean)
-- - extra_dice_risk_value INTEGER

-- Add comment for future reference
-- Run this migration with: sqlite3 cant_stop.db < migrations/001_add_encounter_tables.sql
