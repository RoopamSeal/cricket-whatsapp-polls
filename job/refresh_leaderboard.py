"""
Job to refresh leaderboard
Run periodically or manually
"""
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.storage import Storage
from src.leaderboard import LeaderboardManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Refresh leaderboard."""
    logger.info("Starting leaderboard refresh job")
    
    config = Config()
    storage = Storage(config)
    storage.initialize_data_layer()
    
    leaderboard_mgr = LeaderboardManager(config, storage)
    
    # Refresh all gold tables
    leaderboard_mgr.refresh_all_gold_tables()
    logger.info("Leaderboard refresh completed")


if __name__ == "__main__":
    main()
