-- Database initialization script for CodeBreak
-- Run this to create all required tables

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Players table for game state
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    health INTEGER DEFAULT 100,
    x INTEGER DEFAULT 0,
    y INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    inventory JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leaderboard table for high scores
CREATE TABLE IF NOT EXISTS leaderboard (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    score INTEGER NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    waves_survived INTEGER DEFAULT 0,
    enemies_defeated INTEGER DEFAULT 0,
    time_survived INTEGER DEFAULT 0
);

-- Active games table for multiplayer sessions
CREATE TABLE IF NOT EXISTS active_games (
    game_id VARCHAR(255) PRIMARY KEY,
    host_username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game players table to track which players are in which games
CREATE TABLE IF NOT EXISTS game_players (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE CASCADE,
    UNIQUE(game_id, username)
);

-- Resource transfers table (if needed)
CREATE TABLE IF NOT EXISTS resource_transfers (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255) NOT NULL,
    from_username VARCHAR(255) NOT NULL,
    to_username VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL,
    transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_username) REFERENCES players(username),
    FOREIGN KEY (to_username) REFERENCES players(username),
    FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_players_username ON players(username);
CREATE INDEX IF NOT EXISTS idx_leaderboard_score ON leaderboard(score DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_username ON leaderboard(username);
CREATE INDEX IF NOT EXISTS idx_active_games_host ON active_games(host_username);
CREATE INDEX IF NOT EXISTS idx_game_players_game_id ON game_players(game_id);
CREATE INDEX IF NOT EXISTS idx_game_players_username ON game_players(username);

-- Display confirmation
SELECT 'Database tables created successfully!' AS status;
