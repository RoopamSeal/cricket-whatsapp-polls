import logging
from src.db import Database
from src.config import Config
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class Storage:
    def __init__(self, config: Config):
        self.config = config
        # Initialize the DB engine here
        self.db = Database() 
        logger.info("Storage initialized with Database engine")

    def initialize_data_layer(self) -> None:
        """Initializes tables via schema - Ensure schema.py is imported."""
        from src.schema import DatabaseSchema
        schema = DatabaseSchema() # Assuming you updated schema to use st.secrets
        schema.init_database()
        logger.info("Data layer initialized successfully")

    # ============ User Management ============
    def get_or_create_user(self, user_name: str, email: str = "", country: str = "") -> Dict[str, Any]:
        user = self.db.fetch_one("SELECT * FROM users WHERE user_name = %s", (user_name,))
        if user:
            return user
        
        user_id = str(import uuid; uuid.uuid4())
        new_user = {
            'user_id': user_id,
            'user_name': user_name,
            'email': email or f"{user_name}@example.com",
            'registration_date': str(import datetime; datetime.datetime.now())
        }
        self.db.insert("users", new_user)
        self.db.insert("user_stats", {"user_id": user_id, "total_points": 0})
        logger.info(f"Created user: {user_name}")
        return new_user

    # ============ Match Management ============
    def get_all_matches(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM matches ORDER BY match_datetime ASC")

    def get_matches_by_status(self, status: str) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM matches WHERE status = %s", (status,))

    def update_match_status(self, match_id: str, status: str) -> None:
        self.db.update("matches", {"status": status}, "match_id = %s", (match_id,))

    # ============ Prediction Management ============
    def save_prediction(self, user_id: str, match_id: str, predicted_winner: str) -> str:
        pred_id = str(import uuid; uuid.uuid4())
        self.db.insert("predictions", {
            "prediction_id": pred_id,
            "user_id": user_id,
            "match_id": match_id,
            "predicted_winner": predicted_winner,
            "prediction_timestamp": str(import datetime; datetime.datetime.now())
        })
        return pred_id

    def get_user_predictions(self, user_id: str) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM predictions WHERE user_id = %s", (user_id,))

    # ============ Leaderboard Management ============
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        query = """
        SELECT u.user_name, s.total_points, s.accuracy_percentage, s.total_predictions, s.correct_predictions
        FROM users u 
        JOIN user_stats s ON u.user_id = s.user_id 
        ORDER BY s.total_points DESC
        """
        return self.db.fetch_all(query)

    def get_user_rank(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = """
        SELECT *, RANK() OVER (ORDER BY total_points DESC) as rank 
        FROM user_stats WHERE user_id = %s
        """
        return self.db.fetch_one(query, (user_id,))

    # ============ Stats ============
    def get_tournament_stats(self) -> Dict[str, Any]:
        return {
            "Total Users": self.db.count("users"),
            "Total Matches": self.db.count("matches"),
            "Total Predictions": self.db.count("predictions")
        }

    def get_database_size(self) -> Dict[str, int]:
        return {table: self.db.count(table) for table in ["users", "matches", "predictions"]}
