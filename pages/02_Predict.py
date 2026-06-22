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

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

st.markdown("""
<h1 style="text-align: center;">🎯 MAKE YOUR PREDICTIONS</h1>
<p style="text-align: center; color: #e53238; font-size: 1rem;">
    Predict today's matches before kickoff and earn points!
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

        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown(
                f"**{match['team_1']}** vs **{match['team_2']}**  \n"
                f"🕐 {kickoff_display} &nbsp;|&nbsp; {match['stage']}"
            )
        with col_b:
            if pred:
                st.success(f"✅ {pred['predicted_winner']}")

        if not pred:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"🎯 {match['team_1']}", key=f"p_{match['match_id']}_1", use_container_width=True):
                    ok, msg, _ = pred_manager.make_prediction(
                        st.session_state.user_id, match['match_id'], match['team_1']
                    )
                    if ok:
                        st.success("✅ Prediction saved!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
            with c2:
                if st.button("🤝 DRAW", key=f"p_{match['match_id']}_draw", use_container_width=True):
                    ok, msg, _ = pred_manager.make_prediction(
                        st.session_state.user_id, match['match_id'], 'draw'
                    )
                    if ok:
                        st.success("✅ Prediction saved!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
            with c3:
                if st.button(f"🎯 {match['team_2']}", key=f"p_{match['match_id']}_2", use_container_width=True):
                    ok, msg, _ = pred_manager.make_prediction(
                        st.session_state.user_id, match['match_id'], match['team_2']
                    )
                    if ok:
                        st.success("✅ Prediction saved!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")

        st.markdown("---")

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    st.error(f"Error: {str(e)}")
