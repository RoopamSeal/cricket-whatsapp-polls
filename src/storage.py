"""
Storage layer bridging frontend calls to PostgreSQL database
"""
import uuid
import logging
import datetime
import streamlit as st
from typing import Dict, List, Optional, Any
from src.db import Database
from src.config import Config

logger = logging.getLogger(__name__)

@st.cache_resource
def get_storage() -> "Storage":
    """Return a cached Storage instance."""
    config = Config()
    return Storage(config)

class Storage:
    def __init__(self, config: Config):
        self.config = config
        self.db = Database()
        logger.info("Storage initialized with Database engine")

    # ============ MATCH MANAGEMENT ============
    def load_fixtures(self, df) -> None:
        """Populates fixtures from DataFrame into the database."""
        for _, row in df.iterrows():
            match_data = {
                'match_id': str(row['match_id']),
                'team_1': str(row['team_1']),
                'team_2': str(row['team_2']),
                'stage': str(row['stage']),
                'match_date': str(row['match_date']),
                'kickoff_time': str(row['kickoff_time']),
                'venue': str(row.get('venue', '')),
                'status': str(row.get('status', 'scheduled')),
                'kickoff_time_ist': str(row.get('kickoff_time_ist', row['kickoff_time']))
            }
            # Using your DB class's generic insert method
            self.db.insert("matches", match_data)
        logger.info(f"Loaded {len(df)} fixtures")

    def get_all_matches(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM matches ORDER BY match_date, kickoff_time")

    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one("SELECT * FROM matches WHERE match_id = %s", (match_id,))

    # ============ USER METHODS ============
    def get_or_create_user_by_email(self, email: str, display_name: str = "") -> Dict[str, Any]:
        """Find existing user by email or create new one."""
        user = self.db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if user:
            return user

        user_id = str(uuid.uuid4())
        user_name = display_name or email.split('@')[0]
        
        new_user = {
            'user_id': user_id,
            'user_name': user_name,
            'email': email,
            'created_at': datetime.datetime.now().isoformat()
        }
        self.db.insert("users", new_user)
        return new_user

    # ============ PREDICTION METHODS ============
    def create_prediction(self, user_id: str, match_id: str, predicted_winner: str) -> bool:
        pred_data = {
            'prediction_id': str(uuid.uuid4()),
            'user_id': user_id,
            'match_id': match_id,
            'predicted_winner': predicted_winner,
            'timestamp': datetime.datetime.now().isoformat()
        }
        return self.db.insert("predictions", pred_data) is not None

    def get_user_prediction_count(self, user_id: str) -> int:
        return self.db.count("predictions", "user_id = %s", (user_id,))

    def get_user_correct_predictions(self, user_id: str) -> int:
        query = """
        SELECT COUNT(*) as count FROM predictions p
        JOIN results r ON p.match_id = r.match_id
        WHERE p.user_id = %s AND p.predicted_winner = r.actual_winner
        """
        result = self.db.fetch_one(query, (user_id,))
        return int(result['count']) if result else 0

    # ============ RESULT METHODS ============
    def save_result(self, match_id: str, actual_winner: str) -> bool:
        res_data = {
            'result_id': str(uuid.uuid4()),
            'match_id': match_id,
            'actual_winner': actual_winner,
            'timestamp': datetime.datetime.now().isoformat()
        }
        success = self.db.insert("results", res_data) is not None
        if success:
            self.db.update("matches", {"status": "completed"}, "match_id = %s", (match_id,))
        return success

    def get_result(self, match_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one("SELECT * FROM results WHERE match_id = %s", (match_id,))

    # ============ STATS METHODS ============
    def get_user_total_points(self, user_id: str) -> int:
        """Fetch total points for a specific user."""
        # Note: If you don't have a user_stats table, this gracefully returns 0
        result = self.db.fetch_one(
            "SELECT total_points FROM user_stats WHERE user_id = %s", (user_id,)
        )
        return int(result['total_points']) if result else 0

    def get_user_prediction_count(self, user_id: str) -> int:
        """Count total predictions made by a user."""
        return self.db.count("predictions", "user_id = %s", (user_id,))

    def get_user_correct_predictions(self, user_id: str) -> int:
        """Count how many predictions a user got exactly right."""
        query = """
        SELECT COUNT(*) as count FROM predictions p
        JOIN results r ON p.match_id = r.match_id
        WHERE p.user_id = %s AND p.predicted_winner = r.actual_winner
        """
        result = self.db.fetch_one(query, (user_id,))
        return int(result['count']) if result else 0

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Calculate and compile all user stats for the dashboard."""
        total_preds = self.get_user_prediction_count(user_id)
        correct_preds = self.get_user_correct_predictions(user_id)
        total_points = self.get_user_total_points(user_id)
        
        accuracy = (correct_preds / total_preds * 100) if total_preds > 0 else 0.0
        
        return {
            'total_predictions': total_preds,
            'correct_predictions': correct_preds,
            'accuracy': accuracy,
            'total_points': total_points
        }
