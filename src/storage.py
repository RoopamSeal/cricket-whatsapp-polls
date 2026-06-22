"""
Storage layer bridging frontend calls to Neon PostgreSQL database.
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
        logger.info("Storage initialized with Neon PostgreSQL engine")

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
            # Using ON CONFLICT logic via raw execution if you want to avoid duplicates
            self.db.insert("matches", match_data)

    def get_all_matches(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM matches ORDER BY match_date, kickoff_time")

    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one("SELECT * FROM matches WHERE match_id = %s", (match_id,))

    def update_match_status(self, match_id: str, status: str) -> None:
        self.db.update("matches", {"status": status}, "match_id = %s", (match_id,))

    # ============ USER MANAGEMENT & A/B TESTING ============
    def get_or_create_user(self, user_id: str, user_name: str, email: str = "", country: str = "") -> Dict[str, Any]:
        user = self.db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if user:
            return user
            
        # Assign A/B test group if it exists in session state, else default to control
        ab_group = st.session_state.get('ab_group', 'control')
            
        new_user = {
            'user_id': user_id,
            'user_name': user_name,
            'email': email,
            'country': country,
            'experiment_group': ab_group,
            'created_at': datetime.datetime.now().isoformat()
        }
        self.db.insert("users", new_user)
        return new_user

    def get_or_create_user_by_email(self, email: str, display_name: str = "", country: str = "") -> Dict[str, Any]:
        user = self.db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if user:
            return user

        user_id = str(uuid.uuid4())
        user_name = display_name or email.split('@')[0]
        ab_group = st.session_state.get('ab_group', 'control')
        
        new_user = {
            'user_id': user_id,
            'user_name': user_name,
            'email': email,
            'country': country,
            'experiment_group': ab_group,
            'created_at': datetime.datetime.now().isoformat()
        }
        self.db.insert("users", new_user)
        return new_user

    # ============ PREDICTION METHODS ============
    def create_prediction(self, prediction_id: str, user_id: str, match_id: str, predicted_winner: str, timestamp: str = None) -> bool:
        """Create a prediction with backwards compatibility."""
        pred_data = {
            'prediction_id': prediction_id or str(uuid.uuid4()),
            'user_id': user_id,
            'match_id': match_id,
            'predicted_winner': predicted_winner,
            'prediction_timestamp': timestamp or datetime.datetime.now().isoformat()
        }
        return self.db.insert("predictions", pred_data) is not None

    def get_prediction(self, match_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one(
            "SELECT * FROM predictions WHERE match_id = %s AND user_id = %s",
            (match_id, user_id)
        )

    def get_user_predictions(self, user_id: str) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM predictions WHERE user_id = %s ORDER BY prediction_timestamp DESC", (user_id,))

    # ============ STATS METHODS ============
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

    # ============ RESULTS & API SYNC ============
    def save_result(self, match_id: str, actual_winner: str) -> bool:
        """Safely saves results using the correct match_result_id column."""
        try:
            # Using raw SQL to handle the ON CONFLICT safely with the correct schema
            query = """
            INSERT INTO match_results (match_result_id, match_id, actual_winner, result_timestamp)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (match_id) DO UPDATE SET 
                actual_winner = EXCLUDED.actual_winner,
                result_timestamp = EXCLUDED.result_timestamp
            """
            success = self.db.execute(query, (
                str(uuid.uuid4()), 
                match_id, 
                actual_winner, 
                datetime.datetime.now().isoformat()
            ))
            
            if success:
                self.update_match_status(match_id, 'completed')
            return success
        except Exception as e:
            logger.error(f"Database error saving result: {e}")
            return False

    def get_result(self, match_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one("SELECT * FROM match_results WHERE match_id = %s", (match_id,))

    def sync_results_from_api(self, competition_code: str = "WC") -> int:
        """Fetch finished match results and map them securely to Neon."""
        try:
            from src.api import FootballAPI
            api = FootballAPI()
            api_matches = api.fetch_finished_matches(competition_code)
            updated = 0
            
            for m in api_matches:
                home = m.get('homeTeam', {}).get('name', '')
                away = m.get('awayTeam', {}).get('name', '')
                api_winner = m.get('score', {}).get('winner')
                
                if not api_winner or not home or not away:
                    continue
                    
                # Fetch match ID and exact DB team names using Fuzzy Match
                db_match = self.db.fetch_one(
                    """SELECT match_id, team_1, team_2 FROM matches WHERE status = 'scheduled'
                       AND (
                           (LOWER(team_1) LIKE %s AND LOWER(team_2) LIKE %s)
                           OR (LOWER(team_1) LIKE %s AND LOWER(team_2) LIKE %s)
                       )""",
                    (f"%{home[:5].lower()}%", f"%{away[:5].lower()}%",
                     f"%{away[:5].lower()}%", f"%{home[:5].lower()}%")
                )
                
                if db_match:
                    db_team1 = db_match['team_1']
                    db_team2 = db_match['team_2']
                    
                    if api_winner == 'DRAW':
                        actual_winner = 'draw'
                    elif api_winner == 'HOME_TEAM':
                        actual_winner = db_team1 if db_team1.lower().startswith(home[:4].lower()) else db_team2
                    elif api_winner == 'AWAY_TEAM':
                        actual_winner = db_team1 if db_team1.lower().startswith(away[:4].lower()) else db_team2
                    
                    if self.save_result(db_match['match_id'], actual_winner):
                        updated += 1
                        
            logger.info(f"Successfully synced {updated} results from API.")
            return updated
            
        except ImportError:
            logger.error("Could not import API module")
            return 0
        except Exception as e:
            logger.error(f"API sync error: {e}")
            return 0

    # ============ LEADERBOARD & ADMIN ============
    def get_leaderboard(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            u.user_id,
            u.user_name,
            COUNT(p.prediction_id) as total_predictions,
            COALESCE(SUM(CASE WHEN p.predicted_winner = r.actual_winner THEN 1 ELSE 0 END), 0) as correct_predictions,
            COALESCE(SUM(
                CASE 
                    WHEN p.predicted_winner = r.actual_winner AND r.actual_winner != 'draw' THEN 3
                    WHEN p.predicted_winner = r.actual_winner AND r.actual_winner = 'draw' THEN 2
                    ELSE 0
                END
            ), 0) as total_points,
            RANK() OVER (
                ORDER BY COALESCE(SUM(
                    CASE 
                        WHEN p.predicted_winner = r.actual_winner AND r.actual_winner != 'draw' THEN 3
                        WHEN p.predicted_winner = r.actual_winner AND r.actual_winner = 'draw' THEN 2
                        ELSE 0
                    END
                ), 0) DESC
            ) as rank
        FROM users u
        LEFT JOIN predictions p ON u.user_id = p.user_id
        LEFT JOIN match_results r ON p.match_id = r.match_id
        GROUP BY u.user_id, u.user_name
        ORDER BY total_points DESC, correct_predictions DESC
        """
        if limit:
            query += f" LIMIT {limit}"
            
        results = self.db.fetch_all(query)
        for row in results:
            total = row['total_predictions']
            correct = row['correct_predictions']
            row['accuracy_percentage'] = round((correct / total * 100), 2) if total > 0 else 0.0
        return results

    def get_tournament_stats(self) -> Dict[str, Any]:
        return {
            "Total Users": self.db.count("users"),
            "Total Matches": self.db.count("matches"),
            "Total Predictions": self.db.count("predictions"),
            "Scheduled Matches": self.db.count("matches", "status = %s", ("scheduled",)),
            "Completed Matches": self.db.count("matches", "status = %s", ("completed",)),
        }
