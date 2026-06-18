"""
CSV-based data storage layer (Lakehouse architecture)
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
from src.config import Config

logger = logging.getLogger(__name__)


class Storage:
    """
    CSV-based data storage layer managing silver and gold tables.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.config.ensure_directories()
    
    def initialize_data_layer(self) -> None:
        """Initialize all data tables if they don't exist."""
        self._ensure_user_master()
        self._ensure_match_master()
        self._ensure_prediction_fact()
        self._ensure_match_result()
        self._ensure_points_fact()
        self._ensure_leaderboard()
        self._ensure_user_accuracy()
        self._ensure_tournament_stats()
        logger.info("Data layer initialized successfully")
    
    # ============ User Management ============
    
    def _ensure_user_master(self) -> None:
        """Ensure user_master table exists with schema."""
        if not self.config.USER_MASTER_PATH.exists():
            df = pd.DataFrame({
                'user_id': pd.Series(dtype='str'),
                'user_name': pd.Series(dtype='str'),
                'email': pd.Series(dtype='str'),
                'country': pd.Series(dtype='str'),
                'registration_date': pd.Series(dtype='str'),
                'status': pd.Series(dtype='str')
            })
            df.to_csv(self.config.USER_MASTER_PATH, index=False)
            logger.info("Created user_master.csv")
    
    def get_or_create_user(self, user_name: str, email: str = "", country: str = "") -> Dict[str, Any]:
        """Get existing user or create new one."""
        df = pd.read_csv(self.config.USER_MASTER_PATH)
        
        # Check if user exists
        existing = df[df['user_name'] == user_name]
        if not existing.empty:
            return existing.iloc[0].to_dict()
        
        # Create new user
        user_id = str(uuid.uuid4())
        new_user = {
            'user_id': user_id,
            'user_name': user_name,
            'email': email,
            'country': country,
            'registration_date': datetime.now(timezone.utc).strftime(self.config.DATETIME_FORMAT),
            'status': 'active'
        }
        
        new_row = pd.DataFrame([new_user])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.config.USER_MASTER_PATH, index=False)
        logger.info(f"Created user: {user_name}")
        
        return new_user
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id."""
        df = pd.read_csv(self.config.USER_MASTER_PATH)
        user = df[df['user_id'] == user_id]
        if user.empty:
            return None
        return user.iloc[0].to_dict()
    
    def get_user_prediction_count(self, user_id: str) -> int:
        """Count total predictions by user."""
        df = pd.read_csv(self.config.PREDICTION_FACT_PATH)
        return len(df[df['user_id'] == user_id])
    
    def get_user_correct_predictions(self, user_id: str) -> int:
        """Count correct predictions by user."""
        predictions_df = pd.read_csv(self.config.PREDICTION_FACT_PATH)
        points_df = pd.read_csv(self.config.POINTS_FACT_PATH)
        
        user_points = points_df[points_df['user_id'] == user_id]
        correct = len(user_points[user_points['points'] > 0])
        return correct
    
    def get_user_total_points(self, user_id: str) -> int:
        """Get total points for user."""
        df = pd.read_csv(self.config.POINTS_FACT_PATH)
        user_points = df[df['user_id'] == user_id]
        return int(user_points['points'].sum()) if not user_points.empty else 0
    
    # ============ Match Management ============
    
    def _ensure_match_master(self) -> None:
        """Ensure match_master table exists."""
        if not self.config.MATCH_MASTER_PATH.exists():
            df = pd.DataFrame({
                'match_id': pd.Series(dtype='str'),
                'team_1': pd.Series(dtype='str'),
                'team_2': pd.Series(dtype='str'),
                'stage': pd.Series(dtype='str'),
                'match_date': pd.Series(dtype='str'),
                'kickoff_time': pd.Series(dtype='str'),
                'venue': pd.Series(dtype='str'),
                'status': pd.Series(dtype='str')
            })
            df.to_csv(self.config.MATCH_MASTER_PATH, index=False)
            logger.info("Created match_master.csv")
    
    def load_fixtures(self, fixtures_df: pd.DataFrame) -> None:
        """Load fixtures from DataFrame into match_master."""
        df = pd.read_csv(self.config.MATCH_MASTER_PATH)
        
        for _, row in fixtures_df.iterrows():
            match_id = str(uuid.uuid4())
            new_match = {
                'match_id': match_id,
                'team_1': row.get('team_1', ''),
                'team_2': row.get('team_2', ''),
                'stage': row.get('stage', ''),
                'match_date': row.get('match_date', ''),
                'kickoff_time': row.get('kickoff_time', ''),
                'venue': row.get('venue', ''),
                'status': 'scheduled'
            }
            new_row = pd.DataFrame([new_match])
            df = pd.concat([df, new_row], ignore_index=True)
        
        df.to_csv(self.config.MATCH_MASTER_PATH, index=False)
        logger.info(f"Loaded {len(fixtures_df)} fixtures")
    
    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get match by match_id."""
        df = pd.read_csv(self.config.MATCH_MASTER_PATH)
        match = df[df['match_id'] == match_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()
    
    def get_all_matches(self) -> List[Dict[str, Any]]:
        """Get all matches."""
        df = pd.read_csv(self.config.MATCH_MASTER_PATH)
        return df.to_dict('records')
    
    def get_matches_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get matches filtered by status."""
        df = pd.read_csv(self.config.MATCH_MASTER_PATH)
        matches = df[df['status'] == status]
        return matches.to_dict('records')
    
    def update_match_status(self, match_id: str, status: str) -> None:
        """Update match status."""
        df = pd.read_csv(self.config.MATCH_MASTER_PATH)
        df.loc[df['match_id'] == match_id, 'status'] = status
        df.to_csv(self.config.MATCH_MASTER_PATH, index=False)
    
    # ============ Prediction Management ============
    
    def _ensure_prediction_fact(self) -> None:
        """Ensure prediction_fact table exists."""
        if not self.config.PREDICTION_FACT_PATH.exists():
            df = pd.DataFrame({
                'prediction_id': pd.Series(dtype='str'),
                'user_id': pd.Series(dtype='str'),
                'match_id': pd.Series(dtype='str'),
                'predicted_winner': pd.Series(dtype='str'),
                'prediction_timestamp': pd.Series(dtype='str')
            })
            df.to_csv(self.config.PREDICTION_FACT_PATH, index=False)
            logger.info("Created prediction_fact.csv")
    
    def save_prediction(self, user_id: str, match_id: str, predicted_winner: str) -> str:
        """Save a prediction."""
        prediction_id = str(uuid.uuid4())
        prediction = {
            'prediction_id': prediction_id,
            'user_id': user_id,
            'match_id': match_id,
            'predicted_winner': predicted_winner,
            'prediction_timestamp': datetime.now(timezone.utc).strftime(self.config.DATETIME_FORMAT)
        }
        
        df = pd.read_csv(self.config.PREDICTION_FACT_PATH)
        new_row = pd.DataFrame([prediction])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.config.PREDICTION_FACT_PATH, index=False)
        
        logger.info(f"Saved prediction {prediction_id} for user {user_id}")
        return prediction_id
    
    def get_user_predictions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all predictions by a user."""
        df = pd.read_csv(self.config.PREDICTION_FACT_PATH)
        user_predictions = df[df['user_id'] == user_id]
        return user_predictions.to_dict('records')
    
    def get_prediction(self, match_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's prediction for a specific match."""
        df = pd.read_csv(self.config.PREDICTION_FACT_PATH)
        prediction = df[(df['match_id'] == match_id) & (df['user_id'] == user_id)]
        if prediction.empty:
            return None
        return prediction.iloc[0].to_dict()
    
    def user_has_predicted(self, user_id: str, match_id: str) -> bool:
        """Check if user has already predicted for a match."""
        return self.get_prediction(match_id, user_id) is not None
    
    # ============ Match Result Management ============
    
    def _ensure_match_result(self) -> None:
        """Ensure match_result table exists."""
        if not self.config.MATCH_RESULT_PATH.exists():
            df = pd.DataFrame({
                'match_id': pd.Series(dtype='str'),
                'actual_winner': pd.Series(dtype='str'),
                'result_timestamp': pd.Series(dtype='str')
            })
            df.to_csv(self.config.MATCH_RESULT_PATH, index=False)
            logger.info("Created match_result.csv")
    
    def save_match_result(self, match_id: str, actual_winner: str) -> None:
        """Save match result."""
        result = {
            'match_id': match_id,
            'actual_winner': actual_winner,
            'result_timestamp': datetime.now(timezone.utc).strftime(self.config.DATETIME_FORMAT)
        }
        
        df = pd.read_csv(self.config.MATCH_RESULT_PATH)
        new_row = pd.DataFrame([result])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.config.MATCH_RESULT_PATH, index=False)
        
        logger.info(f"Saved result for match {match_id}: {actual_winner}")
    
    def get_match_result(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get result for a match."""
        df = pd.read_csv(self.config.MATCH_RESULT_PATH)
        result = df[df['match_id'] == match_id]
        if result.empty:
            return None
        return result.iloc[0].to_dict()
    
    def has_result(self, match_id: str) -> bool:
        """Check if match has a result."""
        return self.get_match_result(match_id) is not None
    
    # ============ Points Management ============
    
    def _ensure_points_fact(self) -> None:
        """Ensure points_fact table exists."""
        if not self.config.POINTS_FACT_PATH.exists():
            df = pd.DataFrame({
                'user_id': pd.Series(dtype='str'),
                'match_id': pd.Series(dtype='str'),
                'points': pd.Series(dtype='int'),
                'processed_timestamp': pd.Series(dtype='str')
            })
            df.to_csv(self.config.POINTS_FACT_PATH, index=False)
            logger.info("Created points_fact.csv")
    
    def save_points(self, user_id: str, match_id: str, points: int) -> None:
        """Save points for a user-match combination."""
        df = pd.read_csv(self.config.POINTS_FACT_PATH)
        
        # Check if points already recorded
        existing = df[(df['user_id'] == user_id) & (df['match_id'] == match_id)]
        if not existing.empty:
            logger.info(f"Points already recorded for user {user_id}, match {match_id}")
            return
        
        points_record = {
            'user_id': user_id,
            'match_id': match_id,
            'points': points,
            'processed_timestamp': datetime.now(timezone.utc).strftime(self.config.DATETIME_FORMAT)
        }
        
        new_row = pd.DataFrame([points_record])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.config.POINTS_FACT_PATH, index=False)
        
        logger.info(f"Recorded {points} points for user {user_id}")
    
    # ============ Leaderboard (Gold Layer) ============
    
    def _ensure_leaderboard(self) -> None:
        """Ensure leaderboard table exists."""
        if not self.config.LEADERBOARD_PATH.exists():
            df = pd.DataFrame({
                'rank': pd.Series(dtype='int'),
                'user_id': pd.Series(dtype='str'),
                'user_name': pd.Series(dtype='str'),
                'total_predictions': pd.Series(dtype='int'),
                'correct_predictions': pd.Series(dtype='int'),
                'accuracy_percentage': pd.Series(dtype='float'),
                'total_points': pd.Series(dtype='int'),
                'last_updated': pd.Series(dtype='str')
            })
            df.to_csv(self.config.LEADERBOARD_PATH, index=False)
            logger.info("Created leaderboard.csv")
    
    def get_leaderboard(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get leaderboard data."""
        df = pd.read_csv(self.config.LEADERBOARD_PATH)
        df = df.sort_values('rank')
        if limit:
            df = df.head(limit)
        return df.to_dict('records')
    
    def get_user_rank(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's leaderboard entry."""
        df = pd.read_csv(self.config.LEADERBOARD_PATH)
        user_rank = df[df['user_id'] == user_id]
        if user_rank.empty:
            return None
        return user_rank.iloc[0].to_dict()
    
    def save_leaderboard(self, leaderboard_df: pd.DataFrame) -> None:
        """Save computed leaderboard."""
        leaderboard_df.to_csv(self.config.LEADERBOARD_PATH, index=False)
        logger.info("Leaderboard updated")
    
    # ============ User Accuracy (Gold Layer) ============
    
    def _ensure_user_accuracy(self) -> None:
        """Ensure user_accuracy table exists."""
        if not self.config.USER_ACCURACY_PATH.exists():
            df = pd.DataFrame({
                'user_id': pd.Series(dtype='str'),
                'user_name': pd.Series(dtype='str'),
                'total_predictions': pd.Series(dtype='int'),
                'correct_predictions': pd.Series(dtype='int'),
                'accuracy_percentage': pd.Series(dtype='float'),
                'last_updated': pd.Series(dtype='str')
            })
            df.to_csv(self.config.USER_ACCURACY_PATH, index=False)
            logger.info("Created user_accuracy.csv")
    
    def save_user_accuracy(self, accuracy_df: pd.DataFrame) -> None:
        """Save computed user accuracy."""
        accuracy_df.to_csv(self.config.USER_ACCURACY_PATH, index=False)
    
    # ============ Tournament Stats (Gold Layer) ============
    
    def _ensure_tournament_stats(self) -> None:
        """Ensure tournament_stats table exists."""
        if not self.config.TOURNAMENT_STATS_PATH.exists():
            df = pd.DataFrame({
                'metric': pd.Series(dtype='str'),
                'value': pd.Series(dtype='str'),
                'last_updated': pd.Series(dtype='str')
            })
            df.to_csv(self.config.TOURNAMENT_STATS_PATH, index=False)
            logger.info("Created tournament_stats.csv")
    
    def save_tournament_stats(self, stats_df: pd.DataFrame) -> None:
        """Save computed tournament stats."""
        stats_df.to_csv(self.config.TOURNAMENT_STATS_PATH, index=False)
    
    def get_tournament_stats(self) -> Dict[str, Any]:
        """Get tournament statistics."""
        try:
            df = pd.read_csv(self.config.TOURNAMENT_STATS_PATH)
            return dict(zip(df['metric'], df['value']))
        except Exception as e:
            logger.error(f"Error reading tournament stats: {e}")
            return {}
    
    # ============ Utility Methods ============
    
    def reset_all_tables(self) -> None:
        """Reset all tables to empty state. USE WITH CAUTION."""
        for path in [
            self.config.USER_MASTER_PATH,
            self.config.MATCH_MASTER_PATH,
            self.config.PREDICTION_FACT_PATH,
            self.config.MATCH_RESULT_PATH,
            self.config.POINTS_FACT_PATH,
            self.config.LEADERBOARD_PATH,
            self.config.USER_ACCURACY_PATH,
            self.config.TOURNAMENT_STATS_PATH
        ]:
            if path.exists():
                path.unlink()
        
        self.initialize_data_layer()
        logger.warning("All tables have been reset")
    
    def get_database_size(self) -> Dict[str, int]:
        """Get row counts for all tables."""
        sizes = {}
        for name, path in [
            ('users', self.config.USER_MASTER_PATH),
            ('matches', self.config.MATCH_MASTER_PATH),
            ('predictions', self.config.PREDICTION_FACT_PATH),
            ('results', self.config.MATCH_RESULT_PATH),
            ('points', self.config.POINTS_FACT_PATH),
        ]:
            try:
                df = pd.read_csv(path)
                sizes[name] = len(df)
            except Exception as e:
                logger.error(f"Error reading {name}: {e}")
                sizes[name] = 0
        return sizes
