"""
FIFA World Cup 2026 Prediction Platform - Main Application & Home Dashboard
"""
import os
import logging
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.config import Config
from src.storage import Storage
from src.scheduler import start_background_tasks
from src.fixtures import FixtureLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="World Cup 2026 Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize config, storage, and fixtures
config = Config()
storage = Storage(config)
storage.initialize_data_layer()

fixture_loader = FixtureLoader(config)
fixture_loader.ensure_fixtures_loaded(storage)

# Start background scheduler (runs once per session)
if 'scheduler_started' not in st.session_state:
    start_background_tasks()
    st.session_state.scheduler_started = True

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# FIFA World Cup 2026 Custom CSS
st.markdown("""
<style>
    /* Main color scheme - FIFA 2026
