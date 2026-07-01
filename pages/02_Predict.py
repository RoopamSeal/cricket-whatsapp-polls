"""
Predict page - Make predictions on matches.
Predictions are only open for TODAY's matches (EST date).
Future-date matches are locked — predict on the day they are played.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import logging

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

if 'ab_group' not in st.session_state:
    st.session_state.ab_group = 'control'
# ==========================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Predict", layout="wide")

st.markdown("""
<h1 style="text-align: center;">🎯 MAKE YOUR PREDICTIONS</h1>
<p style="text-align: center; color: #e53238; font-size: 1rem;">
    Predict the EXACT score for today's matches before kickoff to earn +5 points!
</p>
""", unsafe_allow_html=True)

st.markdown("---")

if st.session_state.user_id is None:
    st.warning("⚠️ You are not logged in.")
    st.info("👈 Please go to **Home** to log in.")
    st.stop()

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
    # "Today" is determined by EST (UTC-5) — the timezone of the host nations
    EST = timezone(timedelta(hours=-5))
    now_est      = datetime.now(EST)
    today_est    = now_est.strftime('%Y-%m-%d')   # e.g. '2026-06-22'
    now_est_time = now_est.strftime('%H:%M:%S')   # e.g. '14:30:00'

    st.info(f"⏰ Predictions open for **{now_est.strftime('%B %d, %Y')}** matches only (EST). Times shown in IST.")

    matches = storage.get_all_matches()

    if not matches:
        st.warning("📭 No matches in database")
        st.stop()

    # Only today's scheduled matches that haven't kicked off yet (EST)
    def is_today_and_upcoming(m):
        if m.get('status', '').lower() != 'scheduled':
            return False
        d = str(m.get('match_date', ''))
        t = str(m.get('kickoff_time', '00:00')).strip()
        if len(t) == 5:       # HH:MM → HH:MM:SS
            t += ':00'
        return d == today_est and t >= now_est_time

    today_matches = [m for m in matches if is_today_and_upcoming(m)]

    if not today_matches:
        st.info(
            f"⏰ No more matches left to predict for today ({now_est.strftime('%B %d, %Y')} EST). "
            f"Come back tomorrow!"
        )
        st.stop()

    st.subheader(f"📋 {len(today_matches)} match(es) available today")
    st.markdown("")

    for match in today_matches:
        # kickoff_time_ist stored in DB (HH:MM 24-hour IST) — no Python computation
        kickoff_display = str(match.get('kickoff_time_ist', match['kickoff_time'])) + ' IST'

        pred = storage.get_prediction(match['match_id'], st.session_state.user_id)

        st.markdown(
            f"<div style='text-align:center; color:#666; margin-bottom:1rem;'>"
            f"🕐 {kickoff_display} &nbsp;|&nbsp; {match['stage']}</div>", 
            unsafe_allow_html=True
        )

        if pred:
            s1 = pred.get('predicted_score_1')
            s2 = pred.get('predicted_score_2')
            score_display = f"({s1} - {s2})" if s1 is not None and s2 is not None else ""
            
            st.success(f"✅ Your prediction: **{pred['predicted_winner']}** {score_display}")
            st.markdown("---")
            continue

        # Score Input UI
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 2, 3])
        
        with col1:
            st.markdown(f"<h4 style='text-align:right; color:#1a472a; margin-top:2rem;'>{match['team_1']}</h4>", unsafe_allow_html=True)
            
        with col2:
            score_1 = st.number_input("Score", min_value=0, max_value=20, value=0, key=f"s1_{match['match_id']}", label_visibility="collapsed")
            
        with col3:
            st.markdown("<h4 style='text-align:center; color:#ffb81c; margin-top:0.5rem;'>vs</h4>", unsafe_allow_html=True)
            
        with col4:
            score_2 = st.number_input("Score", min_value=0, max_value=20, value=0, key=f"s2_{match['match_id']}", label_visibility="collapsed")
            
        with col5:
            st.markdown(f"<h4 style='text-align:left; color:#1a472a; margin-top:2rem;'>{match['team_2']}</h4>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Single Lock-in Button
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            if st.button("🔒 Lock In Prediction", key=f"btn_{match['match_id']}", width="stretch", type="primary"):
                
                # Automatically calculate the winner based on the inputted scores
                if score_1 > score_2:
                    winner = match['team_1']
                elif score_1 < score_2:
                    winner = match['team_2']
                else:
                    winner = 'draw'

                # Pass the scores to the backend
                ok, msg, _ = pred_manager.make_prediction(
                    st.session_state.user_id, 
                    match['match_id'], 
                    winner, 
                    score_1, 
                    score_2
                )
                
                if ok:
                    st.success(f"✅ Prediction locked! {winner} ({score_1} - {score_2})")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Error: {msg}")

        st.markdown("---")

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    st.error(f"Error: {str(e)}")
