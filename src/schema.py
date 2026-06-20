"""
SQLite Database Schema and Initialization
"""
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseSchema:
    """Database schema management for FIFA 2026 Platform"""
    
    def __init__(self, db_path: Path):
        """Initialize with database path"""
        self.db_path = db_path
        # Ensure the directory exists before creating the DB file
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def init_database(self) -> bool:
        """Initializes database tables, relations, and indexes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Enable foreign key support in SQLite
                cursor.execute("PRAGMA foreign_keys = ON;")
                
                # ============ USERS TABLE ============
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    user_name TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    registration_date TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # ============ MATCHES TABLE ============
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT PRIMARY KEY,
                    team_1 TEXT NOT NULL,
                    team_2 TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    match_date TEXT NOT NULL,      -- YYYY-MM-DD
                    kickoff_time TEXT NOT NULL,    -- HH:MM:SS
                    match_datetime TEXT NOT NULL,  -- YYYY-MM-DD HH:MM:SS (UTC)
                    venue TEXT NOT NULL,
                    status TEXT DEFAULT 'scheduled',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # ============ PREDICTIONS TABLE ============
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    match_id TEXT NOT NULL,
                    predicted_winner TEXT NOT NULL,
                    prediction_timestamp TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(match_id) REFERENCES matches(match_id) ON DELETE CASCADE,
                    UNIQUE(user_id, match_id) -- A user can only predict a match once
                )
                """)
                
                # ============ MATCH RESULTS TABLE ============
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS match_results (
                    result_id TEXT PRIMARY KEY,
                    match_id TEXT NOT NULL UNIQUE,
                    actual_winner TEXT NOT NULL,
                    result_timestamp TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(match_id) REFERENCES matches(match_id) ON DELETE CASCADE
                )
                """)
                
                # ============ USER STATISTICS TABLE ============
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    stat_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    total_predictions INTEGER DEFAULT 0,
                    correct_predictions INTEGER DEFAULT 0,
                    accuracy_percentage REAL DEFAULT 0.0,
                    total_points INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """)
                
                # ============ CREATE INDEXES (For Performance) ============
                # Indexes drastically speed up queries for leaderboard and match lookups
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_name ON users(user_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_datetime ON matches(match_datetime)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_points ON user_stats(total_points DESC, accuracy_percentage DESC)")
                
                conn.commit()
                logger.info(f"✅ Database schema initialized successfully at {self.db_path}")
                return True
        
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            return False
