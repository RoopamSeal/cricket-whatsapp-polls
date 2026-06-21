"""
Prediction management module with timezone support.

Handles checking if predictions can be made, creating predictions,
and managing prediction logic with proper ET/IST timezone handling.
"""

import logging
from datetime import datetime, timezone, timedelta
import uuid

logger = logging.getLogger(__name__)


class PredictionManager:
    """Manages poll predictions with timezone awareness."""
    
    def __init__(self, config, storage):
        """Initialize prediction manager."""
        self.config = config
        self.storage = storage
    
    def can_predict(self, match_id: str) -> tuple:
        """Check if prediction can be made."""
        try:
            match = self.storage.get_match(match_id)
            
            if not match:
                return False, "Match not found"
            
            # Check status
            if match.get('status', '').lower() != 'scheduled':
                return False, "Match not scheduled"
            
            # Get match time
            try:
                match_date = match.get('match_date', '')
                kickoff_time = match.get('kickoff_time', '')
                
                if not match_date or not kickoff_time:
                    return True, ""  # Allow if no time
                
                # Parse ET time
                dt_str = f"{match_date} {kickoff_time}"
                match_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                
                # Convert to IST
                try:
                    from src.worldcup_polls.timezone_utils import TimezoneConverter
                    ist_dt = TimezoneConverter.et_to_ist(match_dt)
                except:
                    ist_dt = match_dt + timedelta(hours=9, minutes=30)
                
                # Check if past
                now = datetime.now()
                if now >= ist_dt:
                    return False, "Match has started"
                
                return True, ""
            
            except Exception as e:
                logger.warning(f"Time parsing error: {e}")
                return True, ""
        
        except Exception as e:
            logger.error(f"Error in can_predict: {e}")
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
            success = self.storage.create_prediction(
                pred_id, user_id, match_id, predicted_winner
            )
            
            if success:
                return True, f"✅ Predicted {predicted_winner}!", pred_id
            else:
                return False, "Failed to save", None
        
        except Exception as e:
            logger.error(f"Error in make_prediction: {e}")
            return False, f"Error: {str(e)}", None
    
    def get_user_predictions(self, user_id: str):
        """Get user predictions."""
        try:
            return self.storage.get_user_predictions(user_id)
        except Exception as e:
            logger.error(f"Error getting predictions: {e}")
            return []
    
    def get_match_predictions(self, match_id: str):
        """Get match predictions."""
        try:
            return self.storage.get_match_predictions(match_id)
        except Exception as e:
            logger.error(f"Error getting predictions: {e}")
            return []
