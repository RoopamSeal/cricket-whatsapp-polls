"""
Predict page - Make predictions on matches with FIFA 2026 design
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from src.config import Config
from src.storage import Storage
from src.predictions import PredictionManager
from src.fixtures import FixtureLoader

# Initialize
config = Config()
storage = Storage(config)
storage.initialize_data_layer()
fixture_loader = FixtureLoader(config)
fixture_loader.ensure_fixtures_loaded(storage)
pred_manager = PredictionManager(config, storage)

st.set_page_config(page_title="Predict - World Cup 2026", layout="wide")

st.markdown("""
<h1 style="text-align: center;">🎯 MAKE YOUR PREDICTIONS</h1>
<p style="text-align: center; color: #e53238; font-size: 1rem;">
    Choose the winner before the match starts and earn points!
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Check authentication
if st.session_state.user_id is None:
    st.info("👈 Please log in from the Home page to make predictions")
    st.stop()

# Get active matches
try:
    all_matches = storage.get_all_matches()
    matches_df = pd.DataFrame(all_matches) if all_matches else pd.DataFrame()
    
    if matches_df.empty:
        st.warning("No matches available for prediction")
        st.stop()
    
    # Filter for active (scheduled) matches
    active_matches = matches_df[matches_df['status'] == 'scheduled'].copy()
    
    if active_matches.empty:
        st.info("⏰ No active matches available for prediction at this time")
        st.stop()
    
    # Sort by date and time
    active_matches['match_datetime'] = pd.to_datetime(
        active_matches['match_date'] + ' ' + active_matches['kickoff_time']
    )
    active_matches = active_matches.sort_values('match_datetime')
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%); 
                padding: 1rem; border-radius: 0.8rem; margin-bottom: 2rem;
                color: #ffb81c; text-align: center;">
        <h3 style="color: #ffb81c; border: none; margin: 0;">
            📋 {len(active_matches)} MATCHES AVAILABLE FOR PREDICTION
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Display matches with prediction options
    for idx, (_, match) in enumerate(active_matches.iterrows()):
        match_datetime = pd.to_datetime(f"{match['match_date']} {match['kickoff_time']}")
        
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
            card_color = "#e2e8f0"
            border_color = "#ffb81c"
            status_badge = "🎯 OPEN"
            status_color = "#ffb81c"
        
        st.markdown(f"""
        <div style="background: {card_color}; padding: 1.5rem; border-radius: 0.8rem;
                    border-left: 5px solid {border_color}; margin-bottom: 1rem;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <div style="display: grid; grid-template-columns: 2fr 1fr 2fr 1fr 1fr; gap: 1rem; align-items: center;">
                <div>
                    <h4 style="color: #1a472a; margin: 0; font-size: 1.2rem; font-weight: 700;">
                        {match['team_1']}
                    </h4>
                </div>
                <div style="text-align: center;">
                    <span style="background: #ffb81c; color: #1a472a; padding: 0.4rem 0.8rem; 
                               border-radius: 0.4rem; font-weight: 600; font-size: 0.85rem;">
                        vs
                    </span>
                </div>
                <div>
                    <h4 style="color: #1a472a; margin: 0; font-size: 1.2rem; font-weight: 700;">
                        {match['team_2']}
                    </h4>
                </div>
                <div style="text-align: center;">
                    <p style="color: #666; margin: 0; font-size: 0.85rem;">
                        📅 {match_datetime.strftime('%b %d')}<br>
                        🕐 {match_datetime.strftime('%H:%M')}<br>
                        📍 {match['venue']}<br>
                        <span style="background: #e53238; color: white; padding: 0.2rem 0.5rem; 
                                   border-radius: 0.3rem; font-size: 0.75rem; font-weight: 600;">
                            {match['stage']}
                        </span>
                    </p>
                </div>
                <div style="text-align: center;">
                    <span style="background: {status_color}; color: white; padding: 0.5rem 0.8rem; 
                               border-radius: 0.4rem; font-weight: 600; font-size: 0.85rem; display: block;">
                        {status_badge}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Prediction buttons
        if user_prediction:
            st.markdown(f"""
            <div style="background: #e8f5e9; padding: 1rem; border-radius: 0.6rem;
                        border-left: 4px solid #4caf50; margin-bottom: 1.5rem;
                        text-align: center;">
                <p style="color: #1a472a; margin: 0; font-weight: 600;">
                    ✅ Your Prediction: <span style="color: #4caf50; font-weight: 700; font-size: 1.1rem;">
                    {user_prediction['predicted_winner']}
                    </span>
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            col_pred1, col_pred2, col_pred3 = st.columns(3)
            
            with col_pred1:
                if st.button(
                    f"🎯 {match['team_1']}",
                    key=f"pred_{match['match_id']}_team1",
                    disabled=not can_predict,
                    use_container_width=True
                ):
                    success, msg, pred_id = pred_manager.make_prediction(
                        st.session_state.user_id,
                        match['match_id'],
                        match['team_1']
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            with col_pred2:
                if st.button(
                    f"🤝 DRAW",
                    key=f"pred_{match['match_id']}_draw",
                    disabled=not can_predict,
                    use_container_width=True
                ):
                    success, msg, pred_id = pred_manager.make_prediction(
                        st.session_state.user_id,
                        match['match_id'],
                        'draw'
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            
            with col_pred3:
                if st.button(
                    f"🎯 {match['team_2']}",
                    key=f"pred_{match['match_id']}_team2",
                    disabled=not can_predict,
                    use_container_width=True
                ):
                    success, msg, pred_id = pred_manager.make_prediction(
                        st.session_state.user_id,
                        match['match_id'],
                        match['team_2']
                    )
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
st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>💡 Tips for Success</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="prediction-card">
        <h3 style="color: #e53238; border: none; margin-top: 0;">⏰ Timing is Key</h3>
        <p style="color: #666; margin: 0;">Predictions close at kickoff. Don't miss your window!</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="prediction-card">
        <h3 style="color: #e53238; border: none; margin-top: 0;">📊 Do Your Research</h3>
        <p style="color: #666; margin: 0;">Consider team form, injuries, and historical matchups.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="prediction-card">
        <h3 style="color: #e53238; border: none; margin-top: 0;">⭐ Maximize Points</h3>
        <p style="color: #666; margin: 0;">Winner = 3 pts, Draw = 2 pts, Wrong = 0 pts.</p>
    </div>
    """, unsafe_allow_html=True)
