"""
Database Migration Script for CodeBreak Game
==============================================
This script applies database schema changes to existing databases.
It can be run safely multiple times (idempotent).

Usage:
    python migrate_database.py

The script will:
1. Check current database schema
2. Apply missing migrations incrementally
3. Report success or errors for each migration step
"""

import psycopg2
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Database configuration
DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "codebreak_db"),
    "user": os.getenv("DB_USER", "codebreak_admin"),
    "password": os.getenv("DB_PASSWORD", "%w>Iq3ry!"),
    "port": int(os.getenv("DB_PORT", 5432))
}

class DatabaseMigration:
    """Handles database schema migrations"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.migrations_applied = []
        self.migrations_failed = []
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**DB_PARAMS)
            self.cursor = self.connection.cursor()
            print(f"✓ Connected to database: {DB_PARAMS['database']}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("✓ Database connection closed")
    
    def check_column_exists(self, table_name, column_name):
        """Check if a column exists in a table"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name=%s AND column_name=%s
                )
            """, (table_name, column_name))
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"  ✗ Error checking column {table_name}.{column_name}: {e}")
            return False
    
    def check_table_exists(self, table_name):
        """Check if a table exists"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name=%s
                )
            """, (table_name,))
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"  ✗ Error checking table {table_name}: {e}")
            return False
    
    def check_constraint_exists(self, constraint_name, table_name):
        """Check if a constraint exists"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name=%s AND table_name=%s
                )
            """, (constraint_name, table_name))
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"  ✗ Error checking constraint {constraint_name}: {e}")
            return False
    
    def check_index_exists(self, index_name):
        """Check if an index exists"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname=%s
                )
            """, (index_name,))
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"  ✗ Error checking index {index_name}: {e}")
            return False
    
    def apply_migration(self, migration_name, sql, check_func=None):
        """Apply a single migration with error handling"""
        try:
            # Check if migration is needed
            if check_func and check_func():
                print(f"  ⊙ {migration_name} - Already applied, skipping")
                return True
            
            print(f"  → Applying: {migration_name}...")
            self.cursor.execute(sql)
            self.connection.commit()
            print(f"  ✓ {migration_name} - Success")
            self.migrations_applied.append(migration_name)
            return True
        except Exception as e:
            self.connection.rollback()
            print(f"  ✗ {migration_name} - Failed: {e}")
            self.migrations_failed.append((migration_name, str(e)))
            return False
    
    def run_migrations(self):
        """Execute all database migrations"""
        print("\n" + "="*60)
        print("Starting Database Migration")
        print("="*60 + "\n")
        
        # Migration 1: Add game_id column to leaderboard
        print("Migration 1: Add game_id to leaderboard table")
        self.apply_migration(
            "Add game_id column",
            """
            ALTER TABLE leaderboard ADD COLUMN game_id VARCHAR(255);
            """,
            lambda: self.check_column_exists('leaderboard', 'game_id')
        )
        
        # Migration 2: Create indexes on leaderboard.game_id
        print("\nMigration 2: Create leaderboard indexes")
        self.apply_migration(
            "Create idx_leaderboard_game_id",
            """
            CREATE INDEX idx_leaderboard_game_id ON leaderboard(game_id);
            """,
            lambda: self.check_index_exists('idx_leaderboard_game_id')
        )
        
        self.apply_migration(
            "Create idx_leaderboard_game_score",
            """
            CREATE INDEX idx_leaderboard_game_score ON leaderboard(game_id, score DESC);
            """,
            lambda: self.check_index_exists('idx_leaderboard_game_score')
        )
        
        # Migration 3: Add foreign key constraint
        print("\nMigration 3: Add foreign key constraints")
        self.apply_migration(
            "Add FK constraint on leaderboard.game_id",
            """
            ALTER TABLE leaderboard 
            ADD CONSTRAINT fk_leaderboard_game 
            FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE SET NULL;
            """,
            lambda: self.check_constraint_exists('fk_leaderboard_game', 'leaderboard')
        )
        
        # Migration 4: Add unique constraints
        print("\nMigration 4: Add unique constraints to prevent duplicate scores")
        self.apply_migration(
            "Create unique index for game-specific scores",
            """
            CREATE UNIQUE INDEX idx_leaderboard_unique_player_game 
            ON leaderboard(username, game_id) WHERE game_id IS NOT NULL;
            """,
            lambda: self.check_index_exists('idx_leaderboard_unique_player_game')
        )
        
        self.apply_migration(
            "Create unique index for global scores",
            """
            CREATE UNIQUE INDEX idx_leaderboard_unique_player_global 
            ON leaderboard(username) WHERE game_id IS NULL;
            """,
            lambda: self.check_index_exists('idx_leaderboard_unique_player_global')
        )
        
        # Migration 5: Create game_sessions table
        print("\nMigration 5: Create game_sessions table")
        self.apply_migration(
            "Create game_sessions table",
            """
            CREATE TABLE game_sessions (
                session_id SERIAL PRIMARY KEY,
                game_id VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                duration_seconds INTEGER,
                total_players INTEGER DEFAULT 0,
                winner_username VARCHAR(255),
                game_mode VARCHAR(50) DEFAULT 'standard',
                FOREIGN KEY (winner_username) REFERENCES players(username),
                FOREIGN KEY (game_id) REFERENCES active_games(game_id) ON DELETE CASCADE
            );
            """,
            lambda: self.check_table_exists('game_sessions')
        )
        
        self.apply_migration(
            "Create game_sessions indexes",
            """
            CREATE INDEX idx_game_sessions_game_id ON game_sessions(game_id);
            CREATE INDEX idx_game_sessions_winner ON game_sessions(winner_username);
            """,
            lambda: self.check_index_exists('idx_game_sessions_game_id')
        )
        
        # Migration 6: Create player_stats table
        print("\nMigration 6: Create player_stats table")
        self.apply_migration(
            "Create player_stats table",
            """
            CREATE TABLE player_stats (
                stat_id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                total_games_played INTEGER DEFAULT 0,
                total_games_won INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                highest_score INTEGER DEFAULT 0,
                total_playtime_seconds INTEGER DEFAULT 0,
                enemies_defeated INTEGER DEFAULT 0,
                resources_collected INTEGER DEFAULT 0,
                last_played TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES players(username) ON DELETE CASCADE
            );
            """,
            lambda: self.check_table_exists('player_stats')
        )
        
        self.apply_migration(
            "Create player_stats indexes",
            """
            CREATE INDEX idx_player_stats_username ON player_stats(username);
            CREATE INDEX idx_player_stats_total_score ON player_stats(total_score DESC);
            """,
            lambda: self.check_index_exists('idx_player_stats_username')
        )
        
        # Migration 7: Create achievements tables
        print("\nMigration 7: Create achievements system")
        self.apply_migration(
            "Create achievements table",
            """
            CREATE TABLE achievements (
                achievement_id SERIAL PRIMARY KEY,
                achievement_name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                points INTEGER DEFAULT 0,
                icon_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            lambda: self.check_table_exists('achievements')
        )
        
        self.apply_migration(
            "Create player_achievements table",
            """
            CREATE TABLE player_achievements (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                achievement_id INTEGER NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES players(username) ON DELETE CASCADE,
                FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id) ON DELETE CASCADE,
                UNIQUE(username, achievement_id)
            );
            """,
            lambda: self.check_table_exists('player_achievements')
        )
        
        self.apply_migration(
            "Create player_achievements indexes",
            """
            CREATE INDEX idx_player_achievements_username ON player_achievements(username);
            CREATE INDEX idx_player_achievements_achievement ON player_achievements(achievement_id);
            """,
            lambda: self.check_index_exists('idx_player_achievements_username')
        )
        
        # Migration 8: Insert default achievements
        print("\nMigration 8: Insert default achievements")
        self.apply_migration(
            "Insert default achievement data",
            """
            INSERT INTO achievements (achievement_name, description, points) VALUES
                ('First Blood', 'Defeat your first enemy', 10),
                ('Score Master', 'Reach a score of 1000', 25),
                ('Survivor', 'Survive for 10 minutes', 50),
                ('Resource Hoarder', 'Collect 100 resources', 15),
                ('Legendary Collector', 'Collect 500 resources', 50),
                ('Victory Royale', 'Win your first game', 100)
            ON CONFLICT (achievement_name) DO NOTHING;
            """
        )
        
        # Migration 9: Initialize player_stats for existing players
        print("\nMigration 9: Initialize player_stats for existing players")
        self.apply_migration(
            "Backfill player_stats from existing data",
            """
            INSERT INTO player_stats (username, total_score, highest_score)
            SELECT 
                username,
                COALESCE(SUM(score), 0) as total_score,
                COALESCE(MAX(score), 0) as highest_score
            FROM leaderboard
            GROUP BY username
            ON CONFLICT (username) DO NOTHING;
            """
        )
        
        # Print summary
        print("\n" + "="*60)
        print("Migration Summary")
        print("="*60)
        print(f"✓ Migrations applied: {len(self.migrations_applied)}")
        print(f"✗ Migrations failed: {len(self.migrations_failed)}")
        
        if self.migrations_applied:
            print("\nSuccessful migrations:")
            for migration in self.migrations_applied:
                print(f"  ✓ {migration}")
        
        if self.migrations_failed:
            print("\nFailed migrations:")
            for migration, error in self.migrations_failed:
                print(f"  ✗ {migration}")
                print(f"    Error: {error}")
            return False
        
        print("\n✓ All migrations completed successfully!")
        return True

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("CodeBreak Database Migration Tool")
    print("="*60)
    
    # Create migration instance
    migrator = DatabaseMigration()
    
    # Connect to database
    if not migrator.connect():
        print("\n✗ Migration aborted due to connection failure")
        sys.exit(1)
    
    try:
        # Run all migrations
        success = migrator.run_migrations()
        
        # Disconnect
        migrator.disconnect()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Migration interrupted by user")
        migrator.disconnect()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error during migration: {e}")
        migrator.disconnect()
        sys.exit(1)

if __name__ == "__main__":
    main()
