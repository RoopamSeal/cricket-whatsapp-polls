import requests
import streamlit as st
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FootballAPI:
    BASE_URL = "https://api.football-data.org/v4"
    
    def __init__(self):
        self.headers = {
            "X-Auth-Token": st.secrets["football_data"]["API_TOKEN"]
        }

    def fetch_finished_matches(self, competition_code: str = "WC"):
        """Fetches finished matches, forcing fresh data via dynamic date parameters."""
        url = f"{self.BASE_URL}/competitions/{competition_code}/matches"
        
        # Calculate a rolling 7-day window to bust the API cache
        # We add +1 day to date_to to prevent timezone cutoff issues
        date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        date_to = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        params = {
            "status": "FINISHED",
            "dateFrom": date_from,
            "dateTo": date_to
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            matches = response.json().get('matches', [])
            logger.info(f"API fetched {len(matches)} finished matches between {date_from} and {date_to}.")
            return matches
            
        except Exception as e:
            logger.error(f"API Fetch Error: {e}")
            return []
