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
    """Return a single cached Storage instance."""
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
            match_date = str(row['match_date'])
            kickoff = str(row['kickoff_time'])
            
            match_data = {
                'match_id': str(row['match_id']),
                'team_1': str(row['team_1']),
                'team_2': str(row['team_2']),
                'stage': str(row['stage']),
                'match_date': match_date,
                'kickoff_time': kickoff,
                'kickoff_time_ist': str(row.get('kickoff_time_ist', kickoff)),
                'match_datetime': f"{match_date} {kickoff}",
                'venue': str(row.get('venue', '')),
                'status': str(row.get('status', 'scheduled'))
            }
            self.db.insert("matches", match_data)

    def get_all_matches(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM matches ORDER BY match_date, kickoff_time")

    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one("SELECT * FROM matches WHERE match_id = %s", (match_id,))

    def update_match_status(self, match_id: str, status: str) -> None:
        self.db.update("matches", {"status": status}, "match_id = %s", (match_id,))

    # ============ USER MANAGEMENT ============
    def get_or_create_user(self, user_id: str, user_name: str, email: str = "", country: str = "") -> Dict[str, Any]:
        """Get or create a user (Used by Home page manual registration)."""
        user = self.db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if user:
            return user
            
        new_user = {
            'user_id': user_id,
            'user_name': user_name,
            'email': email,
            'country': country,
            'created_at': datetime.datetime.now().isoformat()
        }
        self.db.insert("users", new_user)
        return new_user

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

    # ============ PREDICTION & STATS ============
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
        JOIN match_results r ON p.match_id = r.match_id
        WHERE p.user_id = %s AND p.predicted_winner = r.actual_winner
        """
        result = self.db.fetch_one(query, (user_id,))
        return int(result['count']) if result else 0

    def get_user_total_points(self, user_id: str) -> int:
        """Calculate total points (3 for correct win, 2 for correct draw)."""
        query = """
        SELECT SUM(
            CASE 
                WHEN p.predicted_winner = r.actual_winner AND r.actual_winner != 'draw' THEN 3
                WHEN p.predicted_winner = r.actual_winner AND r.actual_winner = 'draw' THEN 2
                ELSE 0
            END
        ) as total_points
        FROM predictions p
        JOIN match_results r ON p.match_id = r.match_id
        WHERE p.user_id = %s
        """
        result = self.db.fetch_one(query, (user_id,))
        return int(result['total_points']) if result and result['total_points'] else 0

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
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

    # ============ RESULTS & ADMIN API ============
    def save_match_result(self, match_id: str, actual_winner: str) -> bool:
        res_data = {
            'result_id': str(uuid.uuid4()),
            'match_id': match_id,
            'actual_winner': actual_winner,
            'result_timestamp': datetime.datetime.now().isoformat()
        }
        success = self.db.insert("match_results", res_data) is not None
        if success:
            self.update_match_status(match_id, "completed")
        return success

    def get_match_result(self, match_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one("SELECT * FROM match_results WHERE match_id = %s", (match_id,))

    def sync_results_from_api(self, competition_code: str):
        """Fetches results from football-data.org and updates the database."""
        try:
            from src.api import FootballAPI
            api = FootballAPI()
            matches = api.fetch_finished_matches(competition_code)
            
            count = 0
            for match in matches:
                match_id = str(match['id'])
                score_info = match.get('score', {})
                winner_key = score_info.get('winner')
                
                if winner_key == 'HOME_TEAM':
                    winner_name = match['homeTeam']['name']
                elif winner_key == 'AWAY_TEAM':
                    winner_name = match['awayTeam']['name']
                else:
                    winner_name = 'draw'
                    
                if not self.get_match_result(match_id):
                    self.save_match_result(match_id, winner_name)
                    count += 1
            
            logger.info(f"Synced {count} new results from API")
        except ImportError:
            logger.error("Could not import API module")
