"""
Storage module for FIFA World Cup Polls.

Handles all database operations for matches, predictions, users, and results.
Supports both SQLite and PostgreSQL backends.
"""

import sqlite3
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
import json
import os

logger = logging.getLogger(__name__)


class Storage:
    """Database storage handler for polls and predictions."""
    
    def __init__(self, db_path: str = "database.db"):
        """
        Initialize storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database connection and tables."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            # Create tables if they don't exist
            self._create_tables()
            
            logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _create_tables(self):
        """Create necessary database tables."""
        cursor = self.conn.cursor()
        
        try:
            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                user_name TEXT UNIQUE NOT NULL,
                email TEXT,
                country TEXT,
                registration_date TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Matches table
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
            
            # Predictions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                match_id TEXT NOT NULL,
                predicted_winner TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                points_earned INTEGER DEFAULT 0,
                is_processed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(match_id) REFERENCES matches(match_id),
                UNIQUE(user_id, match_id)
            )
            """)
            
            # Match results table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_results (
                result_id TEXT PRIMARY KEY,
                match_id TEXT NOT NULL UNIQUE,
                actual_winner TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(match_id) REFERENCES matches(match_id)
            )
            """)
            
            # User stats table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                stat_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                accuracy_percentage REAL DEFAULT 0.0,
                total_points INTEGER DEFAULT 0,
                last_updated TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
            """)
            
            # Leaderboard table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                leaderboard_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                rank INTEGER NOT NULL,
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                accuracy_percentage REAL DEFAULT 0.0,
                total_points INTEGER DEFAULT 0,
                last_updated TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_stats ON user_stats(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leaderboard_rank ON leaderboard(rank)")
            
            self.conn.commit()
            logger.info("Database tables created/verified")
        
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    # ============ USER METHODS ============
    
    def get_or_create_user(self, user_id: str, user_name: str, email: str = "", country: str = "") -> Dict:
        """
        Get or create a user.
        
        Args:
            user_id: User ID
            user_name: Username
            email: Email address
            country: Country
        
        Returns:
            User dictionary
        """
        try:
            # Check if user exists
            user = self.get_user(user_id)
            if user:
                return user
            
            # Create new user
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO users (user_id, user_name, email, country, registration_date)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, user_name, email, country, datetime.now(timezone.utc).isoformat()))
            
            self.conn.commit()
            
            # Create user stats record
            self._create_user_stats(user_id)
            
            logger.info(f"User created: {user_id}")
            return self.get_user(user_id)
        
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
        
        Returns:
            User dictionary or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def _create_user_stats(self, user_id: str) -> bool:
        """Create user stats record."""
        try:
            import uuid
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT OR IGNORE INTO user_stats (stat_id, user_id)
            VALUES (?, ?)
            """, (str(uuid.uuid4()), user_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating user stats: {e}")
            return False
    
    # ============ MATCH METHODS ============
    
    def create_match(self, match_id: str, team_1: str, team_2: str, stage: str,
                    match_date: str, kickoff_time: str, venue: str = "") -> bool:
        """
        Create a new match.
        
        Args:
            match_id: Match ID
            team_1: First team
            team_2: Second team
            stage: Tournament stage
            match_date: Match date (YYYY-MM-DD)
            kickoff_time: Kickoff time (HH:MM)
            venue: Match venue
        
        Returns:
            Success status
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT OR IGNORE INTO matches 
            (match_id, team_1, team_2, stage, match_date, kickoff_time, venue, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled')
            """, (match_id, team_1, team_2, stage, match_date, kickoff_time, venue))
            
            self.conn.commit()
            logger.info(f"Match created: {team_1} vs {team_2}")
            return True
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            return False
    
    def get_match(self, match_id: str) -> Optional[Dict]:
        """
        Get match by ID.
        
        Args:
            match_id: Match ID
        
        Returns:
            Match dictionary or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting match: {e}")
            return None
    
    def get_all_matches(self) -> List[Dict]:
        """
        Get all matches.
        
        Returns:
            List of match dictionaries
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM matches ORDER BY match_date, kickoff_time")
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all matches: {e}")
            return []
    
    def get_matches_by_date(self, match_date: str) -> List[Dict]:
        """
        Get matches for a specific date.
        
        Args:
            match_date: Date in YYYY-MM-DD format
        
        Returns:
            List of matches for that date
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM matches WHERE match_date = ? ORDER BY kickoff_time",
                (match_date,)
            )
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting matches by date: {e}")
            return []
    
    def update_match_status(self, match_id: str, status: str) -> bool:
        """
        Update match status.
        
        Args:
            match_id: Match ID
            status: New status
        
        Returns:
            Success status
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE matches SET status = ? WHERE match_id = ?",
                (status, match_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating match status: {e}")
            return False
    
    # ============ PREDICTION METHODS ============
    
    def create_prediction(self, prediction_id: str, user_id: str, match_id: str,
                         predicted_winner: str, timestamp: str = None) -> bool:
        """
        Create a new prediction.
        
        Args:
            prediction_id: Unique prediction ID
            user_id: User ID
            match_id: Match ID
            predicted_winner: Predicted winner
            timestamp: Prediction timestamp
        
        Returns:
            Success status
        """
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
    
    def get_prediction(self, match_id: str, user_id: str) -> Optional[Dict]:
        """
        Get a specific prediction.
        
        Args:
            match_id: Match ID
            user_id: User ID
        
        Returns:
            Prediction dictionary or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM predictions WHERE match_id = ? AND user_id = ?",
                (match_id, user_id)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting prediction: {e}")
            return None
    
    def get_user_predictions(self, user_id: str) -> List[Dict]:
        """
        Get all predictions for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of predictions
        """
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
    
    def get_match_predictions(self, match_id: str) -> List[Dict]:
        """
        Get all predictions for a match.
        
        Args:
            match_id: Match ID
        
        Returns:
            List of predictions
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM predictions WHERE match_id = ?",
                (match_id,)
            )
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting match predictions: {e}")
            return []
    
    def update_prediction_points(self, prediction_id: str, points: int) -> bool:
        """
        Update points for a prediction.
        
        Args:
            prediction_id: Prediction ID
            points: Points earned
        
        Returns:
            Success status
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE predictions SET points_earned = ?, is_processed = 1 WHERE prediction_id = ?",
                (points, prediction_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating prediction points: {e}")
            return False
    
    # ============ RESULT METHODS ============
    
    def save_match_result(self, match_id: str, actual_winner: str) -> bool:
        """
        Save match result.
        
        Args:
            match_id: Match ID
            actual_winner: Actual winner
        
        Returns:
            Success status
        """
        try:
            import uuid
            result_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()
            
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO match_results 
            (result_id, match_id, actual_winner, timestamp)
            VALUES (?, ?, ?, ?)
            """, (result_id, match_id, actual_winner, timestamp))
            
            self.conn.commit()
            
            # Update match status
            self.update_match_status(match_id, 'completed')
            
            logger.info(f"Match result saved: {match_id} = {actual_winner}")
            return True
        except Exception as e:
            logger.error(f"Error saving match result: {e}")
            return False
    
    def get_match_result(self, match_id: str) -> Optional[Dict]:
        """
        Get match result.
        
        Args:
            match_id: Match ID
        
        Returns:
            Result dictionary or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM match_results WHERE match_id = ?",
                (match_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting match result: {e}")
            return None
    
    # ============ STATS METHODS ============
    
    def update_user_stats(self, user_id: str) -> bool:
        """
        Update user statistics.
        
        Args:
            user_id: User ID
        
        Returns:
            Success status
        """
        try:
            predictions = self.get_user_predictions(user_id)
            
            total = len(predictions)
            correct = 0
            total_points = 0
            
            for pred in predictions:
                result = self.get_match_result(pred['match_id'])
                
                if result:
                    if result['actual_winner'] == pred['predicted_winner']:
                        correct += 1
                        if pred['predicted_winner'] == 'draw':
                            total_points += 2
                        else:
                            total_points += 3
            
            accuracy = (correct / total * 100) if total > 0 else 0.0
            
            cursor = self.conn.cursor()
            cursor.execute("""
            UPDATE user_stats SET 
                total_predictions = ?,
                correct_predictions = ?,
                accuracy_percentage = ?,
                total_points = ?,
                last_updated = ?
            WHERE user_id = ?
            """, (total, correct, accuracy, total_points, datetime.now(timezone.utc).isoformat(), user_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """
        Get user statistics.
        
        Args:
            user_id: User ID
        
        Returns:
            Stats dictionary or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM user_stats WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return None
    
    # ============ LEADERBOARD METHODS ============
    
    def refresh_leaderboard(self) -> int:
        """
        Refresh leaderboard rankings.
        
        Returns:
            Number of users updated
        """
        try:
            users = self.get_all_users()
            count = 0
            
            for user in users:
                self.update_user_stats(user['user_id'])
            
            # Rebuild leaderboard
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM leaderboard")
            
            # Get users sorted by points
            cursor.execute("""
            SELECT u.user_id, u.user_name, s.total_predictions, s.correct_predictions, s.accuracy_percentage, s.total_points
            FROM users u
            LEFT JOIN user_stats s ON u.user_id = s.user_id
            WHERE u.status = 'active'
            ORDER BY s.total_points DESC, s.accuracy_percentage DESC
            """)
            
            rows = cursor.fetchall()
            
            import uuid
            for rank, row in enumerate(rows, 1):
                cursor.execute("""
                INSERT INTO leaderboard 
                (leaderboard_id, user_id, rank, total_predictions, correct_predictions, accuracy_percentage, total_points, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    row[0],
                    rank,
                    row[2] or 0,
                    row[3] or 0,
                    row[4] or 0.0,
                    row[5] or 0,
                    datetime.now(timezone.utc).isoformat()
                ))
            
            self.conn.commit()
            logger.info(f"Leaderboard refreshed: {len(rows)} users")
            return len(rows)
        except Exception as e:
            logger.error(f"Error refreshing leaderboard: {e}")
            return 0
    
    def get_leaderboard(self, limit: int = 100) -> List[Dict]:
        """
        Get leaderboard.
        
        Args:
            limit: Maximum number of entries
        
        Returns:
            List of leaderboard entries
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM leaderboard ORDER BY rank LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    def get_user_rank(self, user_id: str) -> Optional[Dict]:
        """
        Get user's leaderboard rank.
        
        Args:
            user_id: User ID
        
        Returns:
            Rank entry or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM leaderboard WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user rank: {e}")
            return None
    
    # ============ UTILITY METHODS ============
    
    def get_all_users(self) -> List[Dict]:
        """
        Get all users.
        
        Returns:
            List of users
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE status = 'active'")
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Global storage instance
_storage = None


def get_storage(db_path: str = "database.db") -> Storage:
    """
    Get or create storage instance.
    
    Args:
        db_path: Path to database file
    
    Returns:
        Storage instance
    """
    global _storage
    
    if _storage is None:
        _storage = Storage(db_path)
    
    return _storage


def reset_storage():
    """Reset storage instance."""
    global _storage
    _storage = None
