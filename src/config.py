"""
Configuration management for World Cup Predictor
"""
from pathlib import Path
from typing import Optional
import os
from datetime import datetime, timezone


class Config:
    """
    Central configuration for the application.
    Manages paths, constants, and environment variables.
    """
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    SILVER_DIR = BASE_DIR / "silver"
    GOLD_DIR = BASE_DIR / "gold"
    DATA_DIR = BASE_DIR / "data"
    JOBS_DIR = BASE_DIR / "jobs"
    
    # Data files
    USER_MASTER_PATH = SILVER_DIR / "user_master.csv"
    MATCH_MASTER_PATH = SILVER_DIR / "match_master.csv"
    PREDICTION_FACT_PATH = SILVER_DIR / "prediction_fact.csv"
    MATCH_RESULT_PATH = SILVER_DIR / "match_result.csv"
    POINTS_FACT_PATH = SILVER_DIR / "points_fact.csv"

    # Database
    DB_HOST = st.secrets["database"]["host"]
    DB_PORT = st.secrets["database"]["port"]
    DB_NAME = st.secrets["database"]["database"]
    DB_USER = st.secrets["database"]["user"]
    DB_PASSWORD = st.secrets["database"]["password"]
    
    # Gold files
    LEADERBOARD_PATH = GOLD_DIR / "leaderboard.csv"
    USER_ACCURACY_PATH = GOLD_DIR / "user_accuracy.csv"
    TOURNAMENT_STATS_PATH = GOLD_DIR / "tournament_stats.csv"
    
    # Fixtures
    FIXTURES_PATH = DATA_DIR / "FIFA2026_schedule_fixtures.csv"
    
    # Application constants
    TOURNAMENT_START_DATE = datetime(2026, 6, 12, tzinfo=timezone.utc)
    TOURNAMENT_END_DATE = datetime(2026, 7, 20, tzinfo=timezone.utc)
    TOURNAMENT_NAME = "FIFA World Cup 2026"
    HOST_COUNTRIES = ["USA", "Canada", "Mexico"]
    
    # Scoring system
    POINTS_CORRECT_WINNER = 3
    POINTS_CORRECT_DRAW = 2
    POINTS_INCORRECT = 0
    
    # Scheduler settings
    LEADERBOARD_REFRESH_INTERVAL_SECONDS = 3600  # 1 hour
    RESULT_REFRESH_INTERVAL_SECONDS = 300  # 5 minutes
    
    # Application settings
    TIMEZONE = "UTC"
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    TIME_FORMAT = "%H:%M:%S"
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Match stages
    STAGES = ["Group", "Round of 16", "Quarterfinals", "Semifinals", "Final"]
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [cls.SILVER_DIR, cls.GOLD_DIR, cls.DATA_DIR, cls.JOBS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_env(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional default."""
        return os.getenv(key, default)
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.get_env("ENVIRONMENT", "development") == "production"
