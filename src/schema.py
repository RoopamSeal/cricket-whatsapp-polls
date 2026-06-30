"""
PostgreSQL Database Schema and Initialization
"""
import psycopg2
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class DatabaseSchema:
    """Database schema management for FIFA 2026 Platform"""

    def __init__(self):
        db = st.secrets["database"]
        self.conn_params = dict(
            host=db["HOST"],
            port=int(db.get("PORT", 5432)),
            user=db["USER"],
            password=db["PASSWORD"],
            dbname=db["DBNAME"],
            sslmode="require",
            connect_timeout=10,
        )

    def init_database(self) -> bool:
        """Initializes database tables, relations, and indexes in PostgreSQL."""
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cursor:
                    # ============ USERS TABLE ============
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        user_name TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        registration_date TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                    """)
                    
                    # ============ MATCHES TABLE ============
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS matches (
                        match_id TEXT PRIMARY KEY,
                        team_1 TEXT NOT NULL,
                        team_2 TEXT NOT NULL,
                        stage TEXT NOT NULL,
                        match_date TEXT NOT NULL,
                        kickoff_time TEXT NOT NULL,
                        match_datetime TEXT NOT NULL,
                        venue TEXT NOT NULL,
                        status TEXT DEFAULT 'scheduled',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                        FOREIGN KEY(match_id) REFERENCES matches(match_id) ON DELETE CASCADE,
                        UNIQUE(user_id, match_id)
                    )
                    """)
                    
                    # ============ MATCH RESULTS TABLE ============
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS match_results (
                        result_id TEXT PRIMARY KEY,
                        match_id TEXT NOT NULL UNIQUE,
                        actual_winner TEXT NOT NULL,
                        result_timestamp TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
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
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                    """)
                    
                    # ============ CREATE INDEXES ============
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_name ON users(user_name)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id)")
                    
                    # ============ ALTER TABLES FOR GOALS ============
                    cursor.execute("ALTER TABLE predictions ADD COLUMN IF NOT EXISTS predicted_goals INTEGER DEFAULT -1")
                    cursor.execute("ALTER TABLE match_results ADD COLUMN IF NOT EXISTS actual_goals INTEGER DEFAULT -1")

                conn.commit()
                logger.info("✅ PostgreSQL database schema initialized successfully!")
                return True
        
        except Exception as e:
            logger.error(f"❌ Error initializing PostgreSQL database: {e}")
            return False
