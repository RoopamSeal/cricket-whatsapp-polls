"""
Predict page - Make predictions on matches with FIFA 2026 design
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime, timezone, timedelta
from src.config import Config
from src.storage import Storage
from src.predictions import PredictionManager

# ==========================================
# 1. CRITICAL: Initialize Session State
# ==========================================
# This prevents crashes if the user refreshes the page directly
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# Initialize backend (Removed the broken FixtureLoader)
config = Config()
storage = Storage(config)
storage.initialize_data_layer()
pred_manager = PredictionManager(config, storage)

st.markdown("""
<h1 style="text-align: center;">🎯 MAKE YOUR PREDICTIONS</h1>
<p style="text-align: center; color: #e53238; font-size: 1rem;">
    Choose the winner before the match starts and earn points!
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Check authentication safely
if st.session_state.user_id is None:
    st.warning("⚠️ You are not logged in.")
    st.info("👈 Please go to the **Home** page to log in or register before making predictions.")
    st.stop()

# Get active matches
try:
    all_matches = storage.get_all_matches()
    matches_df = pd.DataFrame(all_matches) if all_matches else pd.DataFrame()
    
    if matches_df.empty:
        st.warning("No matches available in the database.")
        st.stop()
    
    # Filter for active (scheduled) matches
    active_matches = matches_df[matches_df['status'] == 'scheduled'].copy()

    if active_matches.empty:
        st.info("⏰ No upcoming matches to predict on right now.")
        st.stop()

    # Sort and build date list
    active_matches['match_datetime'] = pd.to_datetime(
        active_matches['match_date'] + ' ' + active_matches['kickoff_time']
    )
    active_matches = active_matches.sort_values('match_datetime')
    match_dates = sorted(pd.to_datetime(active_matches['match_date']).dt.date.unique())

    # Default to today or nearest future match date
    today = date.today()
    default_date = next((d for d in match_dates if d >= today), match_dates[0])

    if ('predict_match_date' not in st.session_state
            or st.session_state.predict_match_date not in match_dates):
        st.session_state.predict_match_date = default_date

    # Date navigation bar
    col_prev, col_date, col_next = st.columns([1, 4, 1])
    current_idx = match_dates.index(st.session_state.predict_match_date)

    with col_prev:
        if st.button("◀ Prev", use_container_width=True,
                     disabled=(current_idx == 0), key="pred_prev_btn"):
            st.session_state.predict_match_date = match_dates[current_idx - 1]
            st.rerun()
    with col_date:
        chosen = st.date_input(
            "Match Date",
            value=st.session_state.predict_match_date,
            min_value=match_dates[0],
            max_value=match_dates[-1],
            key="predict_date_picker",
            label_visibility="collapsed",
        )
        if chosen != st.session_state.predict_match_date:
            nearest = min(match_dates, key=lambda d: abs((d - chosen).days))
            st.session_state.predict_match_date = nearest
            st.rerun()
    with col_next:
        if st.button("Next ▶", use_container_width=True,
                     disabled=(current_idx >= len(match_dates) - 1), key="pred_next_btn"):
            st.session_state.predict_match_date = match_dates[current_idx + 1]
            st.rerun()

    selected_date = st.session_state.predict_match_date
    day_matches = active_matches[
        pd.to_datetime(active_matches['match_date']).dt.date == selected_date
    ]

    if day_matches.empty:
        st.info(f"No matches on {selected_date.strftime('%B %d, %Y')}. Use the arrows to navigate.")
        st.stop()

    st.html(f"""
    <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
                padding: 1rem; border-radius: 0.8rem; margin-bottom: 2rem;
                color: #ffb81c; text-align: center;">
        <h3 style="color: #ffb81c; border: none; margin: 0;">
            📋 {len(day_matches)} MATCH{'ES' if len(day_matches) != 1 else ''} — {selected_date.strftime('%B %d, %Y').upper()}
        </h3>
    </div>
    """)

    # Display matches with prediction options
    for idx, (_, match) in enumerate(day_matches.iterrows()):
        
        # --- IST TIMING CONVERSION ---
        match_datetime_us = pd.to_datetime(f"{match['match_date']} {match['kickoff_time']}")
        match_datetime_ist = match_datetime_us + pd.Timedelta(hours=9, minutes=30)
        # -----------------------------
        
        # Check if user already predicted
        user_prediction = storage.get_prediction(match['match_id'], st.session_state.user_id)
        can_predict, reason = pred_manager.can_predict(match['match_id'])
        
        # Determine color based on prediction status
        if user_prediction:
            card_color = "#e8f5e9"
            border_color = "#4caf50"
            status_badge = "✅ PREDICTED"
            status_color = "#4caf50"
        elif not can_predict:
            card_color = "#ffebee"
            border_color = "#e53238"
            status_badge = f"⏱️ {reason}"
            status_color = "#e53238"
        else:
            card_color = "#e2e8f0"  # Cooler gray-blue
            border_color = "#ffb81c"
            status_badge = "🎯 OPEN"
            status_color = "#ffb81c"
        
        # Using st.html() to prevent Markdown parsing bugs
        st.html(f"""
        <div style="background: {card_color}; padding: 1.5rem; border-radius: 0.8rem;
                    border-left: 5px solid {border_color}; margin-bottom: 1rem;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <div style="display: grid; grid-template-columns: 2fr 1fr 2fr 1fr 1fr; gap: 1rem; align-items: center;">
                <div>
                    <h4 style="color: #1a472a; margin: 0; font-size: 1.2rem; font-weight: 700;">{match['team_1']}</h4>
                </div>
                <div style="text-align: center;">
                    <span style="background: #ffb81c; color: #1a472a; padding: 0.4rem 0.8rem; border-radius: 0.4rem; font-weight: 600; font-size: 0.85rem;">vs</span>
                </div>
                <div>
                    <h4 style="color: #1a472a; margin: 0; font-size: 1.2rem; font-weight: 700;">{match['team_2']}</h4>
                </div>
                <div style="text-align: center;">
                    <p style="color: #666; margin: 0; font-size: 0.85rem;">
                        📅 {match_datetime_ist.strftime('%b %d')}<br>
                        🕐 {match_datetime_ist.strftime('%H:%M')} IST<br>
                        📍 {match['venue']}<br>
                        <span style="background: #e53238; color: white; padding: 0.2rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem; font-weight: 600;">{match['stage']}</span>
                    </p>
                </div>
                <div style="text-align: center;">
                    <span style="background: {status_color}; color: white; padding: 0.5rem 0.8rem; border-radius: 0.4rem; font-weight: 600; font-size: 0.85rem; display: block;">
                        {status_badge}
                    </span>
                </div>
            </div>
        </div>
        """)
        
        # Prediction buttons
        if user_prediction:
            st.html(f"""
            <div style="background: #e8f5e9; padding: 1rem; border-radius: 0.6rem; border-left: 4px solid #4caf50; margin-bottom: 1.5rem; text-align: center;">
                <p style="color: #1a472a; margin: 0; font-weight: 600;">
                    ✅ Your Prediction: <span style="color: #4caf50; font-weight: 700; font-size: 1.1rem;">{user_prediction['predicted_winner']}</span>
                </p>
            </div>
            """)
        else:
            col_pred1, col_pred2, col_pred3 = st.columns(3)
            
            with col_pred1:
                if st.button(f"🎯 {match['team_1']}", key=f"pred_{match['match_id']}_team1", disabled=not can_predict, use_container_width=True):
                    success, msg, _ = pred_manager.make_prediction(st.session_state.user_id, match['match_id'], match['team_1'])
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            with col_pred2:
                if st.button(f"🤝 DRAW", key=f"pred_{match['match_id']}_draw", disabled=not can_predict, use_container_width=True):
                    success, msg, _ = pred_manager.make_prediction(st.session_state.user_id, match['match_id'], 'draw')
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            with col_pred3:
                if st.button(f"🎯 {match['team_2']}", key=f"pred_{match['match_id']}_team2", disabled=not can_predict, use_container_width=True):
                    success, msg, _ = pred_manager.make_prediction(st.session_state.user_id, match['match_id'], match['team_2'])
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            st.markdown("")  # Spacing
    
except Exception as e:
    st.error(f"Error loading matches: {e}")

st.markdown("---")

# Tips Section
st.html("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>💡 Tips for Success</h2>")

col1, col2, col3 = st.columns(3)

card_style = "background: linear-gradient(135deg, #e2e8f0 0%, #edf2f7 100%); padding: 1.2rem; border-radius: 0.8rem; border-left: 5px solid #e53238; border-right: 2px solid #ffb81c; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"

with col1:
    st.html(f"""
    <div style="{card_style}">
        <h3 style="color: #e53238; border: none; margin-top: 0;">⏰ Timing is Key</h3>
        <p style="color: #666; margin: 0;">Predictions close at kickoff. Don't miss your window!</p>
    </div>
    """)

with col2:
    st.html(f"""
    <div style="{card_style}">
        <h3 style="color: #e53238; border: none; margin-top: 0;">📊 Do Your Research</h3>
        <p style="color: #666; margin: 0;">Consider team form, injuries, and historical matchups.</p>
    </div>
    """)

with col3:
    st.html(f"""
    <div style="{card_style}">
        <h3 style="color: #e53238; border: none; margin-top: 0;">⭐ Maximize Points</h3>
        <p style="color: #666; margin: 0;">Winner = 3 pts, Draw = 2 pts, Wrong = 0 pts.</p>
    </div>
    """)
