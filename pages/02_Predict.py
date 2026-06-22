"""
Predict page - Make predictions on matches.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Predict", layout="wide")

# Session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# Header
st.markdown("""
<h1 style="text-align: center;">🎯 MAKE YOUR PREDICTIONS</h1>
<p style="text-align: center; color: #e53238; font-size: 1rem;">
    Choose the winner before the match starts and earn points!
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Auth check
if st.session_state.user_id is None:
    st.warning("⚠️ You are not logged in.")
    st.info("👈 Please go to **Home** to log in.")
    st.stop()

# Info
st.info("⏰ **All times in IST (Indian Standard Time)**")

# Import
try:
    from src.storage import get_storage
    from src.predictions import PredictionManager
    from src.config import Config
    
    config = Config()
    storage = get_storage()
    pred_manager = PredictionManager(config, storage)
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

try:
    from datetime import timezone, timedelta

    # Current time in EST (UTC-5) and IST offset
    EST = timezone(timedelta(hours=-5))
    IST_OFFSET = timedelta(hours=9, minutes=30)
    now_est = datetime.now(EST)
    today_est_str = now_est.strftime('%Y-%m-%d')
    now_est_time = now_est.strftime('%H:%M:%S')

    # Get matches
    matches = storage.get_all_matches()

    if not matches:
        st.warning("📭 No matches in database")
        st.stop()

    # Filter: scheduled AND kickoff has not yet passed in EST
    def is_upcoming(m):
        d = m.get('match_date', '')
        t = str(m.get('kickoff_time', '00:00')).strip()
        if len(t) == 5:   # HH:MM → HH:MM:SS
            t += ':00'
        if m.get('status', '').lower() != 'scheduled':
            return False
        if d > today_est_str:
            return True
        if d == today_est_str and t >= now_est_time:
            return True
        return False

    active = [m for m in matches if is_upcoming(m)]

    if not active:
        st.info("⏰ No upcoming matches available for prediction")
        st.stop()

    # Get dates
    dates = sorted(set(m['match_date'] for m in active))

    # Date selector
    selected_date = st.selectbox(
        "Select Date (EST)",
        dates,
        format_func=lambda d: pd.to_datetime(d).strftime('%B %d, %Y')
    )

    # Get matches for date
    day_matches = [m for m in active if m['match_date'] == selected_date]

    if not day_matches:
        st.info("No matches on this date")
        st.stop()

    # Display count
    st.subheader(f"📋 {len(day_matches)} Matches on {pd.to_datetime(selected_date).strftime('%B %d, %Y')}")
    st.markdown("")

    # Display matches
    for match in day_matches:
        # kickoff_ist is pre-computed by the DB query in storage.get_all_matches()
        kickoff_display = str(match.get('kickoff_ist', match['kickoff_time'])) + ' IST'

        # Check prediction
        pred = storage.get_prediction(match['match_id'], st.session_state.user_id)

        # Colors
        if pred:
            bg = "#e8f5e9"
            status = "✅ PREDICTED"
            status_color = "#4caf50"
        else:
            bg = "#e2e8f0"
            status = "🎯 OPEN"
            status_color = "#ffb81c"

        # Card
        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            st.write(f"**{match['team_1']}**")

        with col2:
            st.write("**vs**")

        with col3:
            st.write(f"**{match['team_2']}**")

        st.caption(f"📅 {pd.to_datetime(selected_date).strftime('%B %d, %Y')} | 🕐 {kickoff_display} | {match['stage']}")
        
        # Prediction
        if pred:
            st.success(f"✅ Your prediction: **{pred['predicted_winner']}**")
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(
                    f"🎯 {match['team_1']}",
                    key=f"p_{match['match_id']}_1",
                    use_container_width=True
                ):
                    success, msg, _ = pred_manager.make_prediction(
                        st.session_state.user_id,
                        match['match_id'],
                        match['team_1']
                    )
                    
                    if success:
                        st.success("✅ Prediction saved!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
            
            with col2:
                if st.button(
                    "🤝 DRAW",
                    key=f"p_{match['match_id']}_draw",
                    use_container_width=True
                ):
                    success, msg, _ = pred_manager.make_prediction(
                        st.session_state.user_id,
                        match['match_id'],
                        'draw'
                    )
                    
                    if success:
                        st.success("✅ Prediction saved!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
            
            with col3:
                if st.button(
                    f"🎯 {match['team_2']}",
                    key=f"p_{match['match_id']}_2",
                    use_container_width=True
                ):
                    success, msg, _ = pred_manager.make_prediction(
                        st.session_state.user_id,
                        match['match_id'],
                        match['team_2']
                    )
                    
                    if success:
                        st.success("✅ Prediction saved!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
        
        st.markdown("---")

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    st.error(f"Error: {str(e)}")
