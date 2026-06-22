"""
Simple storage module for FIFA World Cup Polls.
"""

import sqlite3
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
import uuid

logger = logging.getLogger(__name__)


class Storage:
    """Simple database storage handler."""
    
    def __init__(self, db_path: str = "database.db"):
        """Initialize storage."""
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._create_tables()
            logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            user_name TEXT UNIQUE NOT NULL,
            email TEXT,
            country TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Matches
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            team_1 TEXT NOT NULL,
            team_2 TEXT NOT NULL,
            stage TEXT NOT NULL,
            match_date TEXT NOT NULL,
            kickoff_time TEXT NOT NULL,
            venue TEXT,
            status TEXT DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Predictions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            match_id TEXT NOT NULL,
            predicted_winner TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(match_id) REFERENCES matches(match_id),
            UNIQUE(user_id, match_id)
        )
        """)
        
        # Results
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            result_id TEXT PRIMARY KEY,
            match_id TEXT NOT NULL UNIQUE,
            actual_winner TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(match_id) REFERENCES matches(match_id)
        )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id)")
        
        self.conn.commit()
        logger.info("Database tables created")
    
    # ============ USER METHODS ============
    
    def get_or_create_user(self, user_id: str, user_name: str, email: str = "", country: str = ""):
        """Get or create user."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            
            # Create new user
            cursor.execute("""
            INSERT INTO users (user_id, user_name, email, country)
            VALUES (?, ?, ?, ?)
            """, (user_id, user_name, email, country))
            
            self.conn.commit()
            logger.info(f"User created: {user_id}")
            
            return self.get_user(user_id)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def get_user(self, user_id: str):
        """Get user by ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    # ============ MATCH METHODS ============
    
    def create_match(self, match_id: str, team_1: str, team_2: str, stage: str,
                    match_date: str, kickoff_time: str, venue: str = ""):
        """Create a match."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT OR IGNORE INTO matches 
            (match_id, team_1, team_2, stage, match_date, kickoff_time, venue)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (match_id, team_1, team_2, stage, match_date, kickoff_time, venue))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            return False
    
    def get_match(self, match_id: str):
        """Get match by ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,))
            match = cursor.fetchone()
            return dict(match) if match else None
        except Exception as e:
            logger.error(f"Error getting match: {e}")
            return None
    
    def get_all_matches(self):
        """Get all matches as list of dicts."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM matches ORDER BY match_date, kickoff_time")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting matches: {e}")
            return []
    
    def get_matches_by_date(self, match_date: str):
        """Get matches for a date."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM matches WHERE match_date = ? ORDER BY kickoff_time",
                (match_date,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting matches: {e}")
            return []
    
    # ============ PREDICTION METHODS ============
    
    def create_prediction(self, prediction_id: str, user_id: str, match_id: str,
                         predicted_winner: str, timestamp: str = None):
        """Create a prediction."""
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc).isoformat()
            
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO predictions 
            (prediction_id, user_id, match_id, predicted_winner, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """, (prediction_id, user_id, match_id, predicted_winner, timestamp))
            
            self.conn.commit()
            logger.info(f"Prediction created: {prediction_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating prediction: {e}")
            return False
    
    def get_prediction(self, match_id: str, user_id: str):
        """Get a specific prediction."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM predictions WHERE match_id = ? AND user_id = ?",
                (match_id, user_id)
            )
            pred = cursor.fetchone()
            return dict(pred) if pred else None
        except Exception as e:
            logger.error(f"Error getting prediction: {e}")
            return None
    
    def get_user_predictions(self, user_id: str):
        """Get all predictions for a user."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM predictions WHERE user_id = ? ORDER BY timestamp DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user predictions: {e}")
            return []
    
    def get_user_stats(self, user_id: str):
        """Get user statistics."""
        try:
            predictions = self.get_user_predictions(user_id)
            
            if not predictions:
                return {
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'accuracy': 0.0,
                    'total_points': 0
                }
            
            total = len(predictions)
            correct = 0
            total_points = 0
            
            for pred in predictions:
                result = self.get_result(pred['match_id'])
                if result and result['actual_winner'] == pred['predicted_winner']:
                    correct += 1
                    total_points += 3 if pred['predicted_winner'] != 'draw' else 2
            
            accuracy = (correct / total * 100) if total > 0 else 0.0
            
            return {
                'total_predictions': total,
                'correct_predictions': correct,
                'accuracy': accuracy,
                'total_points': total_points
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0.0,
                'total_points': 0
            }
    
    # ============ RESULT METHODS ============
    
    def save_result(self, match_id: str, actual_winner: str):
        """Save match result."""
        try:
            result_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()
            
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO results 
            (result_id, match_id, actual_winner, timestamp)
            VALUES (?, ?, ?, ?)
            """, (result_id, match_id, actual_winner, timestamp))
            
            # Update match status
            cursor.execute("UPDATE matches SET status = 'completed' WHERE match_id = ?", (match_id,))
            
            self.conn.commit()
            logger.info(f"Result saved: {match_id} = {actual_winner}")
            return True
        except Exception as e:
            logger.error(f"Error saving result: {e}")
            return False
    
    def get_result(self, match_id: str):
        """Get match result."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM results WHERE match_id = ?", (match_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting result: {e}")
            return None
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


# Global instance
_storage = None


def get_storage(db_path: str = "database.db"):
    """Get storage instance."""
    global _storage
    if _storage is None:
        _storage = Storage(db_path)
    return _storage
