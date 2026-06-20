"""
Prediction logic and scoring
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from src.config import Config
from src.storage import Storage

logger = logging.getLogger(__name__)


class PredictionManager:
    """Manage predictions and scoring."""
    
    def __init__(self, config: Config, storage: Storage):
        self.config = config
        self.storage = storage
    
    def can_predict(self, match_id: str) -> tuple[bool, str]:
        """
        Check if a match can be predicted.
        Returns (can_predict, reason)
        """
        match = self.storage.get_match(match_id)
        if not match:
            return False, "Match not found"
        
        match_datetime_str = f"{match['match_date']} {match['kickoff_time']}"
        match_datetime = datetime.strptime(match_datetime_str, "%Y-%m-%d %H:%M:%S")
        match_datetime = match_datetime.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        
        if match['status'] in ['completed', 'live']:
            return False, f"Match is {match['status']}"
        
        if now >= match_datetime:
            return False, "Prediction deadline passed"
        
        return True, "OK"
    
    def validate_prediction(self, user_id: str, match_id: str, predicted_winner: str) -> tuple[bool, str]:
        """Validate prediction before saving."""
        # Check if user exists
        user = self.storage.get_user(user_id)
        if not user:
            return False, "User not found"
        
        # Check if match exists
        match = self.storage.get_match(match_id)
        if not match:
            return False, "Match not found"
        
        # Check if prediction is still allowed
        can_predict, reason = self.can_predict(match_id)
        if not can_predict:
            return False, reason
        
        # Check if already predicted
        if self.storage.user_has_predicted(user_id, match_id):
            return False, "You have already predicted for this match"
        
        # Validate predicted winner
        valid_winners = [match['team_1'], match['team_2'], 'draw']
        if predicted_winner not in valid_winners:
            return False, f"Invalid prediction. Choose: {', '.join(valid_winners)}"
        
        return True, "OK"
    
    def make_prediction(self, user_id: str, match_id: str, predicted_winner: str) -> tuple[bool, str, Optional[str]]:
        """
        Make a prediction.
        Returns (success, message, prediction_id)
        """
        valid, reason = self.validate_prediction(user_id, match_id, predicted_winner)
        if not valid:
            return False, reason, None
        
        try:
            prediction_id = self.storage.save_prediction(user_id, match_id, predicted_winner)
            logger.info(f"Prediction saved: {prediction_id}")
            return True, "Prediction saved successfully!", prediction_id
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return False, "Error saving prediction", None
    
    def calculate_points(self, predicted_winner: str, actual_winner: str) -> int:
        """
        Calculate points based on prediction accuracy.
        """
        if predicted_winner == actual_winner:
            if actual_winner == 'draw':
                return self.config.POINTS_CORRECT_DRAW
            else:
                return self.config.POINTS_CORRECT_WINNER
        return self.config.POINTS_INCORRECT
    
    def process_match_results(self, match_id: str, actual_winner: str) -> None:
        """
        Process results for a match and calculate points for all predictions.
        """
        predictions = self.storage.db.fetch_all(
            "SELECT * FROM predictions WHERE match_id = %s", (match_id,)
        )
        logger.info(f"Processing results for match {match_id} ({len(predictions)} predictions)")

        for prediction in predictions:
            points = self.calculate_points(prediction['predicted_winner'], actual_winner)
            self.storage.save_points(prediction['user_id'], match_id, points)

    def get_user_prediction_accuracy(self, user_id: str) -> Dict[str, Any]:
        """Calculate user's prediction accuracy."""
        total = self.storage.get_user_prediction_count(user_id)
        if total == 0:
            return {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy_percentage': 0.0
            }

        correct_count = self.storage.get_user_correct_predictions(user_id)
        accuracy = (correct_count / total * 100) if total > 0 else 0

        return {
            'total_predictions': total,
            'correct_predictions': correct_count,
            'accuracy_percentage': round(accuracy, 2)
        }
