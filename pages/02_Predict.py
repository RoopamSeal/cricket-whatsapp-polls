"""
Predict page - Make predictions on matches
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from src.config import Config
from src.storage import Storage
from src.predictions import PredictionManager
from src.fixtures import FixtureLoader
from src.ui import inject_global_css, match_card

# Initialize
config = Config()
storage = Storage(config)
storage.initialize_data_layer()
fixture_loader = FixtureLoader(config)
fixture_loader.ensure_fixtures_loaded(storage)
pred_manager = PredictionManager(config, storage)

inject_global_css()
st.set_page_config(page_title="Predict - World Cup 2026", layout="wide")

# Check authentication
if st.session_state.user_id is None:
    st.info("Please log in from the main page")
    st.stop()

st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <div style="
        font-family: 'Montserrat', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #0057B8 0%, #00C896 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    ">🎯 Make Your Predictions</div>
    <div style="
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.7);
    ">Choose wisely. Lock in before kickoff.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

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
        st.info("No active matches available at this time. All predictions are locked.")
        st.stop()
    
    # Sort by date and time
    active_matches['match_datetime'] = pd.to_datetime(
        active_matches['match_date'] + ' ' + active_matches['kickoff_time']
    )
    active_matches = active_matches.sort_values('match_datetime')
    
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, rgba(0, 88, 184, 0.1) 0%, rgba(0, 200, 150, 0.05) 100%);
        border-radius: 12px;
        margin-bottom: 2rem;
    ">
        <strong>⚽ {len(active_matches)} Matches Available</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # Display matches
    for idx, (_, match) in enumerate(active_matches.iterrows()):
        st.markdown("")
        
        match_datetime = pd.to_datetime(f"{match['match_date']} {match['kickoff_time']}")
        now = datetime.now(timezone.utc)
        
        user_prediction = storage.get_prediction(match['match_id'], st.session_state.user_id)
        can_predict, reason = pred_manager.can_predict(match['match_id'])
        
        st.markdown(f"""
        <div class="match-card">
            <div style="
                font-size: 0.75rem;
                color: #00C896;
                font-family: 'Montserrat', sans-serif;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 1rem;
            ">{match['stage']}</div>
            
            <div style="text-align: center; margin: 2rem 0;">
                <div class="team-name">{match['team_1']}</div>
                <div class="vs-divider">vs</div>
                <div class="team-name">{match['team_2']}</div>
            </div>
            
            <div style="
                text-align: center;
                font-size: 0.9rem;
                color: rgba(255, 255, 255, 0.6);
                margin-bottom: 1.5rem;
            ">{match_datetime.strftime('%B %d, %Y at %H:%M UTC')} • {match['venue']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if can_predict:
            # Calculate time remaining
            time_diff = match_datetime - now
            hours = time_diff.total_seconds() // 3600
            minutes = (time_diff.total_seconds() % 3600) // 60
            
            st.markdown(f"""
            <div style="
                text-align: center;
                color: #00C896;
                font-weight: 600;
                margin-bottom: 1rem;
                font-size: 0.9rem;
            ">⏱️ {int(hours)}h {int(minutes)}m remaining</div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"🎯 {match['team_1']}", key=f"t1_{match['match_id']}", 
                           disabled=user_prediction is not None, use_container_width=True):
                    if user_prediction is None:
                        success, msg, _ = pred_manager.make_prediction(
                            st.session_state.user_id, match['match_id'], match['team_1']
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            
            with col2:
                if st.button("🤝 Draw", key=f"draw_{match['match_id']}", 
                           disabled=user_prediction is not None, use_container_width=True):
                    if user_prediction is None:
                        success, msg, _ = pred_manager.make_prediction(
                            st.session_state.user_id, match['match_id'], 'draw'
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            
            with col3:
                if st.button(f"🎯 {match['team_2']}", key=f"t2_{match['match_id']}", 
                           disabled=user_prediction is not None, use_container_width=True):
                    if user_prediction is None:
                        success, msg, _ = pred_manager.make_prediction(
                            st.session_state.user_id, match['match_id'], match['team_2']
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            
            if user_prediction:
                st.markdown(f"""
                <div style="
                    text-align: center;
                    margin-top: 1rem;
                    padding: 0.75rem;
                    background: rgba(0, 200, 150, 0.15);
                    border: 1px solid rgba(0, 200, 150, 0.4);
                    border-radius: 8px;
                    color: #00C896;
                    font-weight: 600;
                    font-family: 'Montserrat', sans-serif;
                ">✓ Your prediction: <strong>{user_prediction['predicted_winner']}</strong></div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 1rem;
                background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, rgba(255, 107, 107, 0.08) 100%);
                border: 1px solid rgba(255, 107, 107, 0.4);
                border-radius: 8px;
                color: #FF6B6B;
                font-weight: 600;
                animation: pulse 2s infinite;
            ">⏱️ {reason}</div>
            """, unsafe_allow_html=True)
        
        st.markdown("")

except Exception as e:
    st.error(f"Error loading matches: {e}")
