-- CodeBreak Database Schema
-- Complete schema for multiplayer game with game-specific leaderboards

-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================
-- PLAYER DATA
-- ============================================

-- Players table for game state
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    health INTEGER DEFAULT 100,
    max_health INTEGER DEFAULT 100,
    energy INTEGER DEFAULT 100,
    max_energy INTEGER DEFAULT 100,
    shield INTEGER DEFAULT 0,
    x INTEGER DEFAULT 0,
    y INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    inventory JSONB DEFAULT '{"code_fragments": 0, "energy_cores": 0, "data_shards": 0}'::jsonb,
    crafted_items JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_players_username ON players(username);
CREATE INDEX IF NOT EXISTS idx_players_score ON players(score DESC);

-- ============================================
-- GAME SESSIONS
-- ============================================

-- Active games table for multiplayer sessions
CREATE TABLE IF NOT EXISTS active_games (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255) UNIQUE NOT NULL,
    host_username VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    game_mode VARCHAR(50) DEFAULT 'survival',
    max_players INTEGER DEFAULT 4,
    FOREIGN KEY (host_username) REFERENCES users(username)
);

CREATE INDEX IF NOT EXISTS idx_active_games_game_id ON active_games(game_id);
CREATE INDEX IF NOT EXISTS idx_active_games_host ON active_games(host_username);
CREATE INDEX IF NOT EXISTS idx_active_games_created ON active_games(created_at DESC);

-- Game players junction table
CREATE TABLE IF NOT EXISTS game_players (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255) NOT NULL,
    username VARCHAR(50) NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_ready BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
    UNIQUE(game_id, username)
);

CREATE INDEX IF NOT EXISTS idx_game_players_game_id ON game_players(game_id);
CREATE INDEX IF NOT EXISTS idx_game_players_username ON game_players(username);

-- Game session history (for completed games)
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255) NOT NULL,
    username VARCHAR(50) NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    final_score INTEGER DEFAULT 0,
    final_wave INTEGER DEFAULT 0,
    survival_time FLOAT DEFAULT 0,
    enemies_defeated INTEGER DEFAULT 0,
    resources_collected JSONB,
    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE INDEX IF NOT EXISTS idx_game_sessions_game_id ON game_sessions(game_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_username ON game_sessions(username);
CREATE INDEX IF NOT EXISTS idx_game_sessions_end_time ON game_sessions(end_time DESC);

-- ============================================
-- LEADERBOARDS
-- ============================================

-- Main leaderboard table (supports both global and game-specific)
CREATE TABLE IF NOT EXISTS leaderboard (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    wave_reached INTEGER DEFAULT 0,
    survival_time FLOAT DEFAULT 0,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    game_id VARCHAR(255),  -- NULL for global leaderboard, specific game_id for game leaderboards
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_username ON leaderboard(username);
CREATE INDEX IF NOT EXISTS idx_leaderboard_score ON leaderboard(score DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_game_id ON leaderboard(game_id);
CREATE INDEX IF NOT EXISTS idx_leaderboard_game_score ON leaderboard(game_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_date ON leaderboard(date DESC);

-- Unique constraint: one entry per player per game (or global)
CREATE UNIQUE INDEX IF NOT EXISTS idx_leaderboard_unique_player_game 
ON leaderboard(username, COALESCE(game_id, '')) 
WHERE game_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_leaderboard_unique_player_global 
ON leaderboard(username) 
WHERE game_id IS NULL;

-- ============================================
-- RESOURCE SHARING & TRANSFERS
-- ============================================

-- Resource transfers between players
CREATE TABLE IF NOT EXISTS resource_transfers (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255) NOT NULL,
    from_username VARCHAR(50) NOT NULL,
    to_username VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    amount INTEGER NOT NULL,
    transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_username) REFERENCES players(username) ON DELETE CASCADE,
    FOREIGN KEY (to_username) REFERENCES players(username) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resource_transfers_game_id ON resource_transfers(game_id);
CREATE INDEX IF NOT EXISTS idx_resource_transfers_from ON resource_transfers(from_username);
CREATE INDEX IF NOT EXISTS idx_resource_transfers_to ON resource_transfers(to_username);
CREATE INDEX IF NOT EXISTS idx_resource_transfers_time ON resource_transfers(transferred_at DESC);

-- ============================================
-- GAME WORLD & ITEMS
-- ============================================

-- Items spawned in the game world
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255),
    type VARCHAR(50) NOT NULL,  -- 'resource', 'weapon', 'tool', 'powerup'
    name VARCHAR(100) NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    value INTEGER DEFAULT 1,
    properties JSONB,
    spawned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    collected_by VARCHAR(50),
    FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_items_game_id ON items(game_id);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_position ON items(x, y);

-- ============================================
-- PLAYER ACHIEVEMENTS & STATS
-- ============================================

-- Player statistics and achievements
CREATE TABLE IF NOT EXISTS player_stats (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    total_games_played INTEGER DEFAULT 0,
    total_games_won INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    highest_wave INTEGER DEFAULT 0,
    longest_survival_time FLOAT DEFAULT 0,
    total_enemies_defeated INTEGER DEFAULT 0,
    total_resources_collected INTEGER DEFAULT 0,
    favorite_weapon VARCHAR(100),
    playtime_seconds INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_player_stats_username ON player_stats(username);
CREATE INDEX IF NOT EXISTS idx_player_stats_total_score ON player_stats(total_score DESC);

-- Achievements table
CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    achievement_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(255),
    points INTEGER DEFAULT 0,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Player achievements junction table
CREATE TABLE IF NOT EXISTS player_achievements (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    achievement_key VARCHAR(100) NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
    FOREIGN KEY (achievement_key) REFERENCES achievements(achievement_key) ON DELETE CASCADE,
    UNIQUE(username, achievement_key)
);

CREATE INDEX IF NOT EXISTS idx_player_achievements_username ON player_achievements(username);
CREATE INDEX IF NOT EXISTS idx_player_achievements_unlocked ON player_achievements(unlocked_at DESC);

-- ============================================
-- CHAT & COMMUNICATION
-- ============================================

-- Chat messages (optional - for game chat history)
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255),
    username VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_game_id ON chat_messages(game_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_sent_at ON chat_messages(sent_at DESC);

-- ============================================
-- GAME EVENTS LOG (Optional - for analytics)
-- ============================================

-- Game events for analytics and debugging
CREATE TABLE IF NOT EXISTS game_events (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255),
    username VARCHAR(50),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_game_events_game_id ON game_events(game_id);
CREATE INDEX IF NOT EXISTS idx_game_events_type ON game_events(event_type);
CREATE INDEX IF NOT EXISTS idx_game_events_created ON game_events(created_at DESC);

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View for global leaderboard with player info
CREATE OR REPLACE VIEW v_global_leaderboard AS
SELECT 
    l.id,
    l.username,
    l.score,
    l.wave_reached,
    l.survival_time,
    l.date,
    p.last_login,
    RANK() OVER (ORDER BY l.score DESC) as rank
FROM leaderboard l
LEFT JOIN players p ON l.username = p.username
WHERE l.game_id IS NULL
ORDER BY l.score DESC;

-- View for game-specific leaderboards
CREATE OR REPLACE VIEW v_game_leaderboards AS
SELECT 
    l.id,
    l.game_id,
    l.username,
    l.score,
    l.wave_reached,
    l.survival_time,
    l.date,
    ag.host_username,
    ag.created_at as game_created_at,
    RANK() OVER (PARTITION BY l.game_id ORDER BY l.score DESC) as rank
FROM leaderboard l
INNER JOIN active_games ag ON l.game_id = ag.game_id
WHERE l.game_id IS NOT NULL
ORDER BY l.game_id, l.score DESC;

-- View for active game summary
CREATE OR REPLACE VIEW v_active_game_summary AS
SELECT 
    ag.game_id,
    ag.host_username,
    ag.created_at,
    ag.game_mode,
    ag.max_players,
    COUNT(DISTINCT gp.username) as current_players,
    array_agg(DISTINCT gp.username) as player_list
FROM active_games ag
LEFT JOIN game_players gp ON ag.game_id = gp.game_id
WHERE ag.is_active = TRUE
GROUP BY ag.game_id, ag.host_username, ag.created_at, ag.game_mode, ag.max_players
ORDER BY ag.created_at DESC;

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update last_login timestamp
CREATE OR REPLACE FUNCTION update_last_login()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_login = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for players table
DROP TRIGGER IF EXISTS trigger_update_player_last_login ON players;
CREATE TRIGGER trigger_update_player_last_login
    BEFORE UPDATE ON players
    FOR EACH ROW
    EXECUTE FUNCTION update_last_login();

-- Function to clean up old inactive games
CREATE OR REPLACE FUNCTION cleanup_inactive_games(hours_threshold INTEGER DEFAULT 24)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM active_games 
    WHERE created_at < CURRENT_TIMESTAMP - (hours_threshold || ' hours')::INTERVAL
    AND is_active = FALSE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- INITIAL DATA (Optional)
-- ============================================

-- Insert some default achievements
INSERT INTO achievements (achievement_key, name, description, points, category) VALUES
    ('first_blood', 'First Blood', 'Defeat your first enemy', 10, 'combat'),
    ('wave_5', 'Wave Warrior', 'Reach wave 5', 25, 'survival'),
    ('wave_10', 'Survivor', 'Reach wave 10', 50, 'survival'),
    ('collector', 'Collector', 'Collect 100 resources', 20, 'resources'),
    ('craftsman', 'Craftsman', 'Craft your first item', 15, 'crafting'),
    ('sharpshooter', 'Sharpshooter', 'Defeat 50 enemies', 30, 'combat'),
    ('veteran', 'Veteran', 'Play 10 games', 25, 'general'),
    ('champion', 'Champion', 'Win a multiplayer game', 100, 'multiplayer')
ON CONFLICT (achievement_key) DO NOTHING;

-- ============================================
-- GRANTS (Adjust based on your user)
-- ============================================

-- Grant permissions to codebreak_admin user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO codebreak_admin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO codebreak_admin;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO codebreak_admin;
