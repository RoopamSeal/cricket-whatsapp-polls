"""
Prediction management.
"""

import logging
from datetime import datetime, timezone, timedelta
import uuid

logger = logging.getLogger(__name__)


class PredictionManager:
    """Manages predictions."""
    
    def __init__(self, config, storage):
        """Initialize."""
        self.config = config
        self.storage = storage
    
    def can_predict(self, match_id: str) -> tuple:
        """Check if can predict."""
        try:
            match = self.storage.get_match(match_id)
            
            if not match:
                return False, "Match not found"
            
            if match.get('status', '').lower() != 'scheduled':
                return False, "Match not scheduled"
            
            return True, ""
        except Exception as e:
            logger.error(f"Error: {e}")
            return True, ""
    
    def make_prediction(self, user_id: str, match_id: str, predicted_winner: str) -> tuple:
        """Make a prediction."""
        try:
            # Validate
            if not user_id or not match_id or not predicted_winner:
                return False, "Missing fields", None
            
            # Check if can predict
            can_pred, reason = self.can_predict(match_id)
            if not can_pred:
                return False, reason, None
            
            # Check if already predicted
            existing = self.storage.get_prediction(match_id, user_id)
            if existing:
                return False, "Already predicted", None
            
            # Create prediction
            pred_id = str(uuid.uuid4())
            
            try:
                success = self.storage.create_prediction(
                    pred_id,
                    user_id,
                    match_id,
                    predicted_winner,
                    datetime.now(timezone.utc).isoformat()
                )
                
                if success:
                    logger.info(f"Prediction created: {pred_id}")
                    return True, f"✅ Predicted {predicted_winner}!", pred_id
                else:
                    return False, "Failed to save", None
            
            except Exception as e:
                logger.error(f"Error creating prediction: {e}")
                return False, f"Error: {str(e)}", None
        
        except Exception as e:
            logger.error(f"Error in make_prediction: {e}")
            return False, f"Error: {str(e)}", None
