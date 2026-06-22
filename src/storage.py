"""
Storage layer - PostgreSQL (Neon) backend
"""
import uuid
import logging
import datetime
import streamlit as st
from typing import Dict, List, Optional
from src.db import Database
from src.config import Config
from src.schema import DatabaseSchema

logger = logging.getLogger(__name__)


@st.cache_resource
def get_storage(_version: int = 6) -> "Storage":
    """Single cached Storage instance shared across all pages and reruns.
    Bump _version to invalidate the Streamlit cache after code changes.
    """
    config = Config()
    s = Storage(config)
    s.initialize_data_layer()
    return s


class Storage:
    def __init__(self, config: Config):
        self.config = config
        self.db = Database()

    def initialize_data_layer(self) -> None:
        try:
            schema = DatabaseSchema()
            schema.init_database()
        except Exception as e:
            logger.error(f"Schema init error: {e}")

    # ── Users ──────────────────────────────────────────────────────────────

    def get_or_create_user_by_email(self, email: str, user_name: str = "", country: str = "") -> Optional[Dict]:
        user = self.db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if user:
            return user

        base = user_name.strip() if user_name.strip() else email.split('@')[0]
        name = base
        counter = 1
        while self.db.fetch_one("SELECT 1 AS x FROM users WHERE user_name = %s", (name,)):
            name = f"{base}{counter}"
            counter += 1

        user_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO users (user_id, user_name, email, registration_date) VALUES (%s, %s, %s, %s)",
            (user_id, name, email, str(datetime.datetime.now()))
        )
        self.db.execute(
            """INSERT INTO user_stats (stat_id, user_id, total_points, total_predictions,
               correct_predictions, accuracy_percentage) VALUES (%s, %s, 0, 0, 0, 0.0)""",
            (str(uuid.uuid4()), user_id)
        )
        return self.db.fetch_one("SELECT * FROM users WHERE user_id = %s", (user_id,))

    def get_user(self, user_id: str) -> Optional[Dict]:
        return self.db.fetch_one("SELECT * FROM users WHERE user_id = %s", (user_id,))

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        return self.db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))

    # ── Matches ────────────────────────────────────────────────────────────

    def get_all_matches(self) -> List[Dict]:
        return self.db.fetch_all("""
            SELECT *,
                to_char(
                    (match_date::date + kickoff_time::time) + interval '9 hours 30 minutes',
                    'YYYY-MM-DD'
                ) AS match_date_ist
            FROM matches
            ORDER BY match_date_ist, kickoff_time_ist
        """)

    def get_match(self, match_id: str) -> Optional[Dict]:
        return self.db.fetch_one("SELECT * FROM matches WHERE match_id = %s", (match_id,))

    def load_fixtures(self, df) -> None:
        for _, row in df.iterrows():
            match_id = str(row.get('match_id') or uuid.uuid4())
            match_datetime = f"{row['match_date']} {row['kickoff_time']}"
            self.db.execute(
                """INSERT INTO matches
                   (match_id, team_1, team_2, stage, match_date, kickoff_time, match_datetime, venue, status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'scheduled') ON CONFLICT DO NOTHING""",
                (match_id, str(row['team_1']), str(row['team_2']), str(row['stage']),
                 str(row['match_date']), str(row['kickoff_time']), match_datetime,
                 str(row.get('venue', '')))
            )

    # ── Predictions ────────────────────────────────────────────────────────

    def get_prediction(self, match_id: str, user_id: str) -> Optional[Dict]:
        return self.db.fetch_one(
            "SELECT * FROM predictions WHERE match_id = %s AND user_id = %s",
            (match_id, user_id)
        )

    def create_prediction(self, prediction_id: str, user_id: str, match_id: str,
                          predicted_winner: str, timestamp: str = None) -> bool:
        if timestamp is None:
            timestamp = str(datetime.datetime.now())
        return self.db.execute(
            """INSERT INTO predictions
               (prediction_id, user_id, match_id, predicted_winner, prediction_timestamp)
               VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            (prediction_id, user_id, match_id, predicted_winner, timestamp)
        )

    def get_user_predictions(self, user_id: str) -> List[Dict]:
        return self.db.fetch_all(
            "SELECT * FROM predictions WHERE user_id = %s ORDER BY prediction_timestamp DESC",
            (user_id,)
        )

    # ── Results ────────────────────────────────────────────────────────────

    def get_result(self, match_id: str) -> Optional[Dict]:
        """Get match result (also aliased as get_match_result for compatibility)."""
        return self.db.fetch_one(
            "SELECT * FROM match_results WHERE match_id = %s", (match_id,)
        )

    def get_match_result(self, match_id: str) -> Optional[Dict]:
        return self.get_result(match_id)

    def save_result(self, match_id: str, actual_winner: str) -> bool:
        result_id = str(uuid.uuid4())
        timestamp = str(datetime.datetime.now())
        ok = self.db.execute(
            """INSERT INTO match_results (result_id, match_id, actual_winner, result_timestamp)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (match_id) DO UPDATE SET actual_winner = EXCLUDED.actual_winner,
                                                    result_timestamp = EXCLUDED.result_timestamp""",
            (result_id, match_id, actual_winner, timestamp)
        )
        if ok:
            self.db.execute(
                "UPDATE matches SET status = 'completed' WHERE match_id = %s", (match_id,)
            )
        return ok

    # ── User Stats ─────────────────────────────────────────────────────────

    def get_user_prediction_count(self, user_id: str) -> int:
        result = self.db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM predictions WHERE user_id = %s", (user_id,)
        )
        return int(result['cnt']) if result else 0

    def get_user_correct_predictions(self, user_id: str) -> int:
        result = self.db.fetch_one(
            """SELECT COUNT(*) AS cnt FROM predictions p
               JOIN match_results mr ON p.match_id = mr.match_id
               WHERE p.user_id = %s AND p.predicted_winner = mr.actual_winner""",
            (user_id,)
        )
        return int(result['cnt']) if result else 0

    def get_user_total_points(self, user_id: str) -> int:
        result = self.db.fetch_one(
            "SELECT total_points FROM user_stats WHERE user_id = %s", (user_id,)
        )
        return int(result['total_points']) if result else 0

    def get_user_stats(self, user_id: str) -> Dict:
        total = self.get_user_prediction_count(user_id)
        correct = self.get_user_correct_predictions(user_id)
        points = self.get_user_total_points(user_id)
        accuracy = (correct / total * 100) if total > 0 else 0.0
        return {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': accuracy,
            'total_points': points
        }

    def count_table(self, table: str) -> int:
        result = self.db.fetch_one(f"SELECT COUNT(*) AS cnt FROM {table}")
        return int(result['cnt']) if result else 0

    # ── Leaderboard ────────────────────────────────────────────────────────

    def get_leaderboard(self, limit: Optional[int] = None) -> List[Dict]:
        query = """
        SELECT u.user_id, u.user_name, s.total_points,
               s.accuracy_percentage,
               s.accuracy_percentage AS accuracy,
               s.total_predictions, s.correct_predictions,
               RANK() OVER (ORDER BY s.total_points DESC) AS rank
        FROM users u
        JOIN user_stats s ON u.user_id = s.user_id
        ORDER BY s.total_points DESC
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        return self.db.fetch_all(query)

    def get_user_rank(self, user_id: str) -> Optional[Dict]:
        return self.db.fetch_one(
            """SELECT * FROM (
                SELECT u.user_id, u.user_name, s.total_points, s.accuracy_percentage,
                       s.total_predictions, s.correct_predictions,
                       RANK() OVER (ORDER BY s.total_points DESC) AS rank
                FROM users u JOIN user_stats s ON u.user_id = s.user_id
            ) ranked WHERE user_id = %s""",
            (user_id,)
        )

    def get_tournament_stats(self) -> Dict:
        return {
            'Total Users':       self.count_table('users'),
            'Total Matches':     self.count_table('matches'),
            'Scheduled Matches': int((self.db.fetch_one(
                "SELECT COUNT(*) AS cnt FROM matches WHERE status = 'scheduled' AND match_date >= CURRENT_DATE::text"
            ) or {}).get('cnt', 0)),
            'Completed Matches': int((self.db.fetch_one(
                "SELECT COUNT(*) AS cnt FROM matches WHERE status = 'completed'"
            ) or {}).get('cnt', 0)),
            'Total Predictions': self.count_table('predictions'),
        }

    # ── API Sync ───────────────────────────────────────────────────────────

    def sync_results_from_api(self, competition_code: str = "WC") -> int:
        """Fetch finished match results from football-data.org and save to DB."""
        try:
            from src.api import FootballAPI
            api = FootballAPI()
            api_matches = api.fetch_finished_matches(competition_code)
            updated = 0
            for m in api_matches:
                home = m.get('homeTeam', {}).get('name', '')
                away = m.get('awayTeam', {}).get('name', '')
                score = m.get('score', {}).get('fullTime', {})
                home_score = score.get('home')
                away_score = score.get('away')
                if home_score is None or away_score is None or not home or not away:
                    continue
                if home_score > away_score:
                    winner = home
                elif away_score > home_score:
                    winner = away
                else:
                    winner = 'draw'
                db_match = self.db.fetch_one(
                    """SELECT match_id FROM matches WHERE status = 'scheduled'
                       AND (
                           (LOWER(team_1) LIKE %s AND LOWER(team_2) LIKE %s)
                           OR (LOWER(team_1) LIKE %s AND LOWER(team_2) LIKE %s)
                       )""",
                    (f"%{home[:5].lower()}%", f"%{away[:5].lower()}%",
                     f"%{away[:5].lower()}%", f"%{home[:5].lower()}%")
                )
                if db_match:
                    self.save_result(db_match['match_id'], winner)
                    updated += 1
            return updated
        except Exception as e:
            logger.error(f"API sync error: {e}")
            raise
