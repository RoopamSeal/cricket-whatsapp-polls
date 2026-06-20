"""
Storage layer bridging frontend calls to PostgreSQL database
"""
import uuid
import logging
import datetime
from typing import Dict, List, Optional, Any
from src.db import Database
from src.config import Config
from src.schema import DatabaseSchema

logger = logging.getLogger(__name__)


class Storage:
    def __init__(self, config: Config):
        self.config = config
        self.db = Database()
        logger.info("Storage initialized with Database engine")

    def initialize_data_layer(self) -> None:
        schema = DatabaseSchema()
        schema.init_database()
        logger.info("Data layer initialized successfully")

    # ============ User Management ============
    def get_or_create_user(self, user_name: str, email: str = "", country: str = "") -> Dict[str, Any]:
        user = self.db.fetch_one("SELECT * FROM users WHERE user_name = %s", (user_name,))
        if user:
            return user

        user_id = str(uuid.uuid4())
        new_user = {
            'user_id': user_id,
            'user_name': user_name,
            'email': email or f"{user_name}@example.com",
            'registration_date': str(datetime.datetime.now())
        }
        self.db.insert("users", new_user)
        # Use direct SQL to avoid column name mismatch in db.insert auto-key logic
        self.db.execute(
            """INSERT INTO user_stats (stat_id, user_id, total_points, total_predictions,
               correct_predictions, accuracy_percentage) VALUES (%s, %s, 0, 0, 0, 0.0)""",
            (str(uuid.uuid4()), user_id)
        )
        logger.info(f"Created user: {user_name}")
        return new_user

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one("SELECT * FROM users WHERE user_id = %s", (user_id,))

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Look up an existing user by email without creating one."""
        return self.db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))

    def get_or_create_user_by_email(self, email: str, display_name: str = "") -> Dict[str, Any]:
        """Find existing user by email or create new one. Email is the primary identifier."""
        user = self.db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if user:
            return user

        base_name = display_name.strip() if display_name.strip() else email.split('@')[0]
        user_name = base_name
        counter = 1
        while self.db.fetch_one("SELECT 1 AS x FROM users WHERE user_name = %s", (user_name,)):
            user_name = f"{base_name}{counter}"
            counter += 1

        user_id = str(uuid.uuid4())
        new_user = {
            'user_id': user_id,
            'user_name': user_name,
            'email': email,
            'registration_date': str(datetime.datetime.now())
        }
        self.db.insert("users", new_user)
        self.db.execute(
            """INSERT INTO user_stats (stat_id, user_id, total_points, total_predictions,
               correct_predictions, accuracy_percentage) VALUES (%s, %s, 0, 0, 0, 0.0)""",
            (str(uuid.uuid4()), user_id)
        )
        logger.info(f"Created user: {user_name} ({email})")
        return new_user

    # ============ Match Management ============
    def get_all_matches(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM matches ORDER BY match_datetime ASC")

    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one("SELECT * FROM matches WHERE match_id = %s", (match_id,))

    def get_matches_by_status(self, status: str) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM matches WHERE status = %s", (status,))

    def update_match_status(self, match_id: str, status: str) -> None:
        self.db.update("matches", {"status": status}, "match_id = %s", (match_id,))

    def save_match_result(self, match_id: str, winner: str) -> None:
        result_data = {
            "result_id": str(uuid.uuid4()),
            "match_id": match_id,
            "actual_winner": winner,
            "result_timestamp": str(datetime.datetime.now())
        }
        self.db.insert("match_results", result_data)

    def get_match_result(self, match_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one(
            "SELECT * FROM match_results WHERE match_id = %s", (match_id,)
        )

    def load_fixtures(self, df) -> None:
        for _, row in df.iterrows():
            match_date = str(row['match_date'])
            kickoff = str(row['kickoff_time'])
            match_data = {
                'match_id': str(row['match_id']),
                'team_1': str(row['team_1']),
                'team_2': str(row['team_2']),
                'match_date': match_date,
                'kickoff_time': kickoff,
                'match_datetime': f"{match_date} {kickoff}",
                'stage': str(row['stage']),
                'venue': str(row['venue']),
                'status': str(row.get('status', 'scheduled'))
            }
            self.db.insert("matches", match_data)

    # ============ Prediction Management ============
    def save_prediction(self, user_id: str, match_id: str, predicted_winner: str) -> str:
        pred_id = str(uuid.uuid4())
        self.db.insert("predictions", {
            "prediction_id": pred_id,
            "user_id": user_id,
            "match_id": match_id,
            "predicted_winner": predicted_winner,
            "prediction_timestamp": str(datetime.datetime.now())
        })
        return pred_id

    def get_user_predictions(self, user_id: str) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM predictions WHERE user_id = %s", (user_id,))

    def get_prediction(self, match_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one(
            "SELECT * FROM predictions WHERE match_id = %s AND user_id = %s",
            (match_id, user_id)
        )

    def user_has_predicted(self, user_id: str, match_id: str) -> bool:
        result = self.db.fetch_one(
            "SELECT 1 AS exists_flag FROM predictions WHERE user_id = %s AND match_id = %s",
            (user_id, match_id)
        )
        return result is not None

    # ============ Points Management ============
    def save_points(self, user_id: str, match_id: str, points: int) -> None:
        is_correct = 1 if points > 0 else 0
        logger.debug(f"Saving {points} points for user {user_id} on match {match_id}")
        self.db.execute(
            """UPDATE user_stats
               SET total_points = total_points + %s,
                   total_predictions = total_predictions + 1,
                   correct_predictions = correct_predictions + %s,
                   accuracy_percentage = CASE
                       WHEN (total_predictions + 1) > 0
                       THEN ROUND((correct_predictions + %s) * 100.0 / (total_predictions + 1), 2)
                       ELSE 0.0
                   END
               WHERE user_id = %s""",
            (points, is_correct, is_correct, user_id)
        )

    # ============ User Stats ============
    def get_user_prediction_count(self, user_id: str) -> int:
        return self.db.count("predictions", "user_id = %s", (user_id,))

    def get_user_correct_predictions(self, user_id: str) -> int:
        query = """
        SELECT COUNT(*) AS count FROM predictions p
        JOIN match_results mr ON p.match_id = mr.match_id
        WHERE p.user_id = %s AND p.predicted_winner = mr.actual_winner
        """
        result = self.db.fetch_one(query, (user_id,))
        return int(result['count']) if result else 0

    def get_user_total_points(self, user_id: str) -> int:
        result = self.db.fetch_one(
            "SELECT total_points FROM user_stats WHERE user_id = %s", (user_id,)
        )
        return int(result['total_points']) if result else 0

    def count_table(self, table: str) -> int:
        return self.db.count(table)

    # ============ Leaderboard Management ============
    def get_leaderboard(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        query = """
        SELECT u.user_name, s.total_points, s.accuracy_percentage,
               s.total_predictions, s.correct_predictions,
               RANK() OVER (ORDER BY s.total_points DESC) AS rank
        FROM users u
        JOIN user_stats s ON u.user_id = s.user_id
        ORDER BY s.total_points DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        return self.db.fetch_all(query)

    def get_user_rank(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = """
        SELECT * FROM (
            SELECT s.*, u.user_name,
                   RANK() OVER (ORDER BY s.total_points DESC) AS rank
            FROM user_stats s
            JOIN users u ON s.user_id = u.user_id
        ) ranked
        WHERE user_id = %s
        """
        return self.db.fetch_one(query, (user_id,))

    # ============ Stats ============
    def get_tournament_stats(self) -> Dict[str, Any]:
        return {
            "Total Users": self.db.count("users"),
            "Total Matches": self.db.count("matches"),
            "Total Predictions": self.db.count("predictions"),
            "Scheduled Matches": self.db.count("matches", "status = %s", ("scheduled",)),
            "Completed Matches": self.db.count("matches", "status = %s", ("completed",)),
        }

    def get_database_size(self) -> Dict[str, int]:
        return {table: self.db.count(table) for table in ["users", "matches", "predictions"]}
