"""
Test script to verify database schema after migration
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "codebreak_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "port": int(os.getenv("DB_PORT", 5432))
}

def test_schema():
    """Test that all schema elements exist"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        print("="*60)
        print("Database Schema Verification")
        print("="*60 + "\n")
        
        # Test 1: Check game_id column exists
        print("Test 1: Checking leaderboard.game_id column...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='leaderboard' AND column_name='game_id'
            )
        """)
        assert cursor.fetchone()[0], "game_id column missing!"
        print("  ✓ game_id column exists\n")
        
        # Test 2: Check indexes
        print("Test 2: Checking indexes...")
        indexes = [
            'idx_leaderboard_game_id',
            'idx_leaderboard_game_score',
            'idx_leaderboard_unique_player_game',
            'idx_leaderboard_unique_player_global'
        ]
        for idx in indexes:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname=%s)", (idx,))
            assert cursor.fetchone()[0], f"{idx} missing!"
            print(f"  ✓ {idx}")
        print()
        
        # Test 3: Check foreign key constraint
        print("Test 3: Checking foreign key constraints...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name='fk_leaderboard_game' AND table_name='leaderboard'
            )
        """)
        assert cursor.fetchone()[0], "fk_leaderboard_game constraint missing!"
        print("  ✓ fk_leaderboard_game constraint exists\n")
        
        # Test 4: Check new tables
        print("Test 4: Checking new tables...")
        tables = ['game_sessions', 'player_stats', 'achievements', 'player_achievements']
        for table in tables:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s)", (table,))
            assert cursor.fetchone()[0], f"{table} table missing!"
            print(f"  ✓ {table} table exists")
        print()
        
        # Test 5: Check achievements data
        print("Test 5: Checking default achievements...")
        cursor.execute("SELECT COUNT(*) FROM achievements")
        count = cursor.fetchone()[0]
        assert count >= 6, f"Expected at least 6 achievements, found {count}"
        print(f"  ✓ Found {count} achievements\n")
        
        # Test 6: List all achievements
        print("Default Achievements:")
        cursor.execute("SELECT achievement_name, description, points FROM achievements ORDER BY points")
        for name, desc, points in cursor.fetchall():
            print(f"  • {name} ({points} pts) - {desc}")
        print()
        
        # Test 7: Check table structures
        print("Test 7: Verifying table structures...")
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'game_sessions'
            ORDER BY ordinal_position
        """)
        game_sessions_cols = cursor.fetchall()
        assert len(game_sessions_cols) >= 7, "game_sessions missing columns"
        print(f"  ✓ game_sessions has {len(game_sessions_cols)} columns")
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'player_stats'
            ORDER BY ordinal_position
        """)
        player_stats_cols = cursor.fetchall()
        assert len(player_stats_cols) >= 10, "player_stats missing columns"
        print(f"  ✓ player_stats has {len(player_stats_cols)} columns")
        print()
        
        # Test 8: Check foreign key relationships
        print("Test 8: Checking foreign key relationships...")
        cursor.execute("""
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ('leaderboard', 'game_sessions', 'player_stats', 'player_achievements')
            ORDER BY tc.table_name
        """)
        fks = cursor.fetchall()
        print(f"  Found {len(fks)} foreign key constraints:")
        for fk in fks:
            print(f"    • {fk[1]}.{fk[2]} → {fk[3]}.{fk[4]}")
        print()
        
        cursor.close()
        conn.close()
        
        print("="*60)
        print("✓ ALL TESTS PASSED - Schema is valid!")
        print("="*60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = test_schema()
    sys.exit(0 if success else 1)
