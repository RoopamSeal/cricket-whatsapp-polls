"""
Predict page - Make predictions on matches with FIFA 2026 design and IST timezone support.

This page displays scheduled matches and allows users to make predictions.
All times are converted to and displayed in Indian Standard Time (IST).
"""

import streamlit as st
import pandas as pd
import logging
from datetime import date, datetime, timezone, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing from new architecture, fallback to old if needed
try:
    from src.worldcup_polls.config import get_config
    from src.worldcup_polls.db import get_session
    from src.worldcup_polls.models import Poll, Option, Vote
    from src.worldcup_polls.timezone_utils import TimezoneConverter
    from src.worldcup_polls.voting import cast_vote, has_voted, get_voter_id
    from src.worldcup_polls.components import render_timezone_info
    USE_NEW_ARCH = True
except ImportError:
    try:
        from src.config import Config
        from src.storage import get_storage
        from src.predictions import PredictionManager
        USE_NEW_ARCH = False
    except ImportError:
        st.error("❌ Configuration modules not found. Please check installation.")
        st.stop()

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'predict_match_date' not in st.session_state:
    st.session_state.predict_match_date = None

# Page configuration
st.set_page_config(page_title="Predict", layout="wide")

# Display header
st.markdown("""
<h1 style="text-align: center;">🎯 MAKE YOUR PREDICTIONS</h1>
<p style="text-align: center; color: #e53238; font-size: 1rem;">
    Choose the winner before the match starts and earn points!
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Check authentication
if st.session_state.user_id is None:
    st.warning("⚠️ You are not logged in.")
    st.info("👈 Please go to the **Home** page to log in or register before making predictions.")
    st.stop()

# Display timezone information
try:
    if USE_NEW_ARCH:
        render_timezone_info()
    else:
        st.info("⏰ **All times displayed in IST (Indian Standard Time)**")
except Exception as e:
    st.info("⏰ **All times displayed in IST (Indian Standard Time)**")


def convert_et_to_ist_display(et_date_str: str, et_time_str: str) -> str:
    """
    Convert ET date/time to IST display string.
    
    Args:
        et_date_str: Date string in YYYY-MM-DD format (ET)
        et_time_str: Time string in HH:MM format (ET)
    
    Returns:
        Formatted IST time string
    """
    try:
        # Parse ET datetime
        et_datetime = datetime.strptime(f"{et_date_str} {et_time_str}", "%Y-%m-%d %H:%M")
        
        # Convert to IST
        ist_datetime = TimezoneConverter.et_to_ist(et_datetime)
        
        # Return formatted string
        return ist_datetime.strftime("%I:%M %p")
    except Exception as e:
        logger.warning(f"Error converting time: {e}. Using ET time.")
        return et_time_str


def get_ist_date_from_et(et_date_str: str, et_time_str: str) -> str:
    """
    Get IST date from ET date and time (handles date changes when converting timezones).
    
    Args:
        et_date_str: Date string in YYYY-MM-DD format (ET)
        et_time_str: Time string in HH:MM format (ET)
    
    Returns:
        IST date in YYYY-MM-DD format
    """
    try:
        et_datetime = datetime.strptime(f"{et_date_str} {et_time_str}", "%Y-%m-%d %H:%M")
        ist_datetime = TimezoneConverter.et_to_ist(et_datetime)
        return ist_datetime.strftime("%Y-%m-%d")
    except Exception as e:
        logger.warning(f"Error converting date: {e}. Using ET date.")
        return et_date_str


try:
    if USE_NEW_ARCH:
        # ============ NEW ARCHITECTURE ============
        config = get_config()
        session = get_session()
        
        # Get active polls (matches)
        from sqlalchemy import and_
        polls = session.query(Poll).all()
        
        if not polls:
            st.warning("📭 No matches available in the database.")
            st.stop()
        
        # Filter for active polls (not ended)
        active_polls = [
            p for p in polls
            if p.end_at is None or p.end_at > datetime.now()
        ]
        
        if not active_polls:
            st.info("⏰ No upcoming matches to predict on right now.")
            st.stop()
        
        # Sort by end time (match time)
        active_polls.sort(
            key=lambda p: p.end_at if p.end_at else datetime.max
        )
        
        # Get unique dates
        poll_dates = sorted(set(
            p.end_at.date() if p.end_at else date.today()
            for p in active_polls
        ))
        
        # Default to today or nearest future date
        today = date.today()
        default_date = next((d for d in poll_dates if d >= today), poll_dates[0])
        
        if st.session_state.predict_match_date is None:
            st.session_state.predict_match_date = default_date
        
        # Date navigation
        col_prev, col_date, col_next = st.columns([1, 4, 1])
        
        if st.session_state.predict_match_date in poll_dates:
            current_idx = poll_dates.index(st.session_state.predict_match_date)
        else:
            current_idx = 0
            st.session_state.predict_match_date = poll_dates[0]
        
        with col_prev:
            if st.button(
                "◀ Prev",
                use_container_width=True,
                disabled=(current_idx == 0),
                key="pred_prev_btn"
            ):
                st.session_state.predict_match_date = poll_dates[current_idx - 1]
                st.rerun()
        
        with col_date:
            chosen = st.date_input(
                "Match Date",
                value=st.session_state.predict_match_date,
                min_value=poll_dates[0],
                max_value=poll_dates[-1],
                key="predict_date_picker",
                label_visibility="collapsed",
            )
            if chosen != st.session_state.predict_match_date:
                nearest = min(poll_dates, key=lambda d: abs((d - chosen).days))
                st.session_state.predict_match_date = nearest
                st.rerun()
        
        with col_next:
            if st.button(
                "Next ▶",
                use_container_width=True,
                disabled=(current_idx >= len(poll_dates) - 1),
                key="pred_next_btn"
            ):
                st.session_state.predict_match_date = poll_dates[current_idx + 1]
                st.rerun()
        
        # Get matches for selected date
        selected_date = st.session_state.predict_match_date
        day_matches = [
            p for p in active_polls
            if (p.end_at.date() if p.end_at else date.today()) == selected_date
        ]
        
        if not day_matches:
            st.info(f"📭 No matches on {selected_date.strftime('%B %d, %Y')}. Use the arrows to navigate.")
            st.stop()
        
        # Display date header
        st.html(f"""
        <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
                    padding: 1rem; border-radius: 0.8rem; margin-bottom: 2rem;
                    color: #ffb81c; text-align: center;">
            <h3 style="color: #ffb81c; border: none; margin: 0;">
                📋 {len(day_matches)} MATCH{'ES' if len(day_matches) != 1 else ''} — {selected_date.strftime('%B %d, %Y').upper()}
            </h3>
        </div>
        """)
        
        # Display matches
        voter_id = get_voter_id()
        
        for poll in day_matches:
            # Check if user has voted
            user_vote = session.query(Vote).filter(
                Vote.poll_id == poll.id,
                Vote.voter_id == voter_id
            ).first()
            
            # Check if poll is still active
            poll_active = poll.end_at is None or poll.end_at > datetime.now()
            
            # Determine card colors based on status
            if user_vote:
                card_color = "#e8f5e9"
                border_color = "#4caf50"
                status_badge = "✅ PREDICTED"
                status_color = "#4caf50"
            elif not poll_active:
                card_color = "#ffebee"
                border_color = "#e53238"
                status_badge = "⏱️ MATCH STARTED"
                status_color = "#e53238"
            else:
                card_color = "#e2e8f0"
                border_color = "#ffb81c"
                status_badge = "🎯 OPEN"
                status_color = "#ffb81c"
            
            # Extract match info from poll
            # Format: "Team A vs Team B"
            title_parts = poll.title.split(" vs ")
            team_1 = title_parts[0] if len(title_parts) > 0 else "Team A"
            team_2 = title_parts[1] if len(title_parts) > 1 else "Team B"
            
            # Get time info from poll
            end_time_str = ""
            venue_str = ""
            stage_str = ""
            
            if poll.description:
                # Try to extract info from description
                lines = poll.description.split("\n")
                for line in lines:
                    if "Time (IST):" in line:
                        end_time_str = line.replace("Time (IST):", "").strip()
                    elif "Venue:" in line:
                        venue_str = line.replace("Venue:", "").strip()
                    elif "Stage:" in line:
                        stage_str = line.replace("Stage:", "").strip()
            
            if not end_time_str and poll.end_at:
                end_time_str = TimezoneConverter.format_ist(
                    poll.end_at,
                    "%Y-%m-%d %I:%M %p IST"
                )
            
            # Display match card
            st.html(f"""
            <div style="background: {card_color}; padding: 1.5rem; border-radius: 0.8rem;
                        border-left: 5px solid {border_color}; margin-bottom: 1rem;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <div style="display: grid; grid-template-columns: 2fr 1fr 2fr 1fr 1fr; gap: 1rem; align-items: center;">
                    <div>
                        <h4 style="color: #1a472a; margin: 0; font-size: 1.2rem; font-weight: 700;">{team_1}</h4>
                    </div>
                    <div style="text-align: center;">
                        <span style="background: #ffb81c; color: #1a472a; padding: 0.4rem 0.8rem; border-radius: 0.4rem; font-weight: 600; font-size: 0.85rem;">vs</span>
                    </div>
                    <div>
                        <h4 style="color: #1a472a; margin: 0; font-size: 1.2rem; font-weight: 700;">{team_2}</h4>
                    </div>
                    <div style="text-align: center;">
                        <p style="color: #666; margin: 0; font-size: 0.85rem;">
                            📅 {end_time_str.split()[0] if end_time_str else 'TBA'}<br>
                            🕐 {' '.join(end_time_str.split()[1:]) if end_time_str else 'TBA'}<br>
                            📍 {venue_str if venue_str else 'TBA'}<br>
                            <span style="background: #e53238; color: white; padding: 0.2rem 0.5rem; border-radius: 0.3rem; font-size: 0.75rem; font-weight: 600;">{stage_str if stage_str else 'GROUP'}</span>
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
            
            # Show prediction or voting options
            if user_vote:
                st.html(f"""
                <div style="background: #e8f5e9; padding: 1rem; border-radius: 0.6rem; border-left: 4px solid #4caf50; margin-bottom: 1.5rem; text-align: center;">
                    <p style="color: #1a472a; margin: 0; font-weight: 600;">
                        ✅ Your Prediction: <span style="color: #4caf50; font-weight: 700; font-size: 1.1rem;">{user_vote.option.label}</span>
                    </p>
                </div>
                """)
            else:
                if poll_active:
                    col_opt1, col_opt2, col_opt3 = st.columns(3)
                    
                    with col_opt1:
                        if st.button(
                            f"🎯 {team_1}",
                            key=f"vote_{poll.id}_team1",
                            use_container_width=True
                        ):
                            try:
                                vote = cast_vote(poll.id, poll.options[0].id, voter_id, session)
                                if vote:
                                    st.success(f"✅ Voted for {team_1}")
                                    st.balloons()
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error voting: {str(e)}")
                    
                    with col_opt2:
                        if st.button(
                            "🤝 DRAW",
                            key=f"vote_{poll.id}_draw",
                            use_container_width=True
                        ):
                            try:
                                vote = cast_vote(poll.id, poll.options[1].id, voter_id, session)
                                if vote:
                                    st.success("✅ Voted for Draw")
                                    st.balloons()
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error voting: {str(e)}")
                    
                    with col_opt3:
                        if st.button(
                            f"🎯 {team_2}",
                            key=f"vote_{poll.id}_team2",
                            use_container_width=True
                        ):
                            try:
                                vote = cast_vote(poll.id, poll.options[2].id, voter_id, session)
                                if vote:
                                    st.success(f"✅ Voted for {team_2}")
                                    st.balloons()
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error voting: {str(e)}")
                    
                    st.markdown("")  # Spacing
                else:
                    st.html("""
                    <div style="background: #ffebee; padding: 1rem; border-radius: 0.6rem; border-left: 4px solid #e53238; margin-bottom: 1.5rem; text-align: center;">
                        <p style="color: #c41e3a; margin: 0; font-weight: 600;">
                            ⏰ Prediction window closed. Match has started.
                        </p>
                    </div>
                    """)
    
    else:
        # ============ OLD ARCHITECTURE ============
        config = Config()
        storage = get_storage()
        pred_manager = PredictionManager(config, storage)
        
        # Get all matches
        try:
            matches_data = storage.get_all_matches()
            
            # Handle both DataFrame and list responses
            if isinstance(matches_data, pd.DataFrame):
                matches_df = matches_data.copy()
            elif isinstance(matches_data, list):
                matches_df = pd.DataFrame(matches_data)
            else:
                st.error("❌ Unexpected data format from database")
                st.stop()
            
            if matches_df.empty:
                st.warning("📭 No matches available in the database.")
                st.stop()
            
            # Ensure required columns exist
            required_cols = ['match_id', 'team_1', 'team_2', 'match_date', 'kickoff_time', 'stage', 'venue', 'status']
            missing_cols = [col for col in required_cols if col not in matches_df.columns]
            
            if missing_cols:
                st.error(f"❌ Missing columns in database: {', '.join(missing_cols)}")
                st.stop()
            
            # Convert to datetime properly
            matches_df['match_date'] = pd.to_datetime(matches_df['match_date']).dt.date
            
            # Add IST time conversion
            matches_df['match_datetime_str'] = (
                matches_df['match_date'].astype(str) + ' ' + matches_df['kickoff_time'].astype(str)
            )
            
            matches_df['kickoff_time_ist'] = matches_df.apply(
                lambda row: convert_et_to_ist_display(
                    str(row['match_date']),
                    str(row['kickoff_time'])
                ),
                axis=1
            )
            
            # Filter for active (scheduled) matches
            active_matches = matches_df[
                matches_df['status'].str.lower() == 'scheduled'
            ].copy()
            
            if active_matches.empty:
                st.info("⏰ No upcoming matches to predict on right now.")
                st.stop()
            
            # Get match dates
            match_dates = sorted(active_matches['match_date'].unique())
            
            # Default to today or nearest future date
            today = date.today()
            default_date = next((d for d in match_dates if d >= today), match_dates[0])
            
            if st.session_state.predict_match_date is None:
                st.session_state.predict_match_date = default_date
            
            # Date navigation
            col_prev, col_date, col_next = st.columns([1, 4, 1])
            
            if st.session_state.predict_match_date in match_dates:
                current_idx = list(match_dates).index(st.session_state.predict_match_date)
            else:
                current_idx = 0
                st.session_state.predict_match_date = match_dates[0]
            
            with col_prev:
                if st.button(
                    "◀ Prev",
                    use_container_width=True,
                    disabled=(current_idx == 0),
                    key="pred_prev_btn"
                ):
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
                if st.button(
                    "Next ▶",
                    use_container_width=True,
                    disabled=(current_idx >= len(match_dates) - 1),
                    key="pred_next_btn"
                ):
                    st.session_state.predict_match_date = match_dates[current_idx + 1]
                    st.rerun()
            
            # Get matches for selected date
            selected_date = st.session_state.predict_match_date
            day_matches = active_matches[active_matches['match_date'] == selected_date].copy()
            
            if day_matches.empty:
                st.info(f"📭 No matches on {selected_date.strftime('%B %d, %Y')}. Use the arrows to navigate.")
                st.stop()
            
            # Display date header
            st.html(f"""
            <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
                        padding: 1rem; border-radius: 0.8rem; margin-bottom: 2rem;
                        color: #ffb81c; text-align: center;">
                <h3 style="color: #ffb81c; border: none; margin: 0;">
                    📋 {len(day_matches)} MATCH{'ES' if len(day_matches) != 1 else ''} — {selected_date.strftime('%B %d, %Y').upper()}
                </h3>
            </div>
            """)
            
            # Display matches
            for idx, match in day_matches.iterrows():
                # Check user prediction
                user_prediction = storage.get_prediction(
                    match['match_id'],
                    st.session_state.user_id
                )
                
                # Check if can predict
                can_predict, reason = pred_manager.can_predict(match['match_id'])
                
                # Determine colors
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
                
                # Display match card
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
                                📅 {match['match_date']}<br>
                                🕐 {match['kickoff_time_ist']} IST<br>
                                📍 {match['venue'][:30]}...<br>
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
                
                # Show prediction or voting options
                if user_prediction:
                    st.html(f"""
                    <div style="background: #e8f5e9; padding: 1rem; border-radius: 0.6rem; border-left: 4px solid #4caf50; margin-bottom: 1.5rem; text-align: center;">
                        <p style="color: #1a472a; margin: 0; font-weight: 600;">
                            ✅ Your Prediction: <span style="color: #4caf50; font-weight: 700; font-size: 1.1rem;">{user_prediction['predicted_winner']}</span>
                        </p>
                    </div>
                    """)
                else:
                    if can_predict:
                        col_pred1, col_pred2, col_pred3 = st.columns(3)
                        
                        with col_pred1:
                            if st.button(
                                f"🎯 {match['team_1']}",
                                key=f"pred_{match['match_id']}_team1",
                                use_container_width=True
                            ):
                                success, msg, _ = pred_manager.make_prediction(
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
                                "🤝 DRAW",
                                key=f"pred_{match['match_id']}_draw",
                                use_container_width=True
                            ):
                                success, msg, _ = pred_manager.make_prediction(
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
                                use_container_width=True
                            ):
                                success, msg, _ = pred_manager.make_prediction(
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
                    else:
                        st.html(f"""
                        <div style="background: #ffebee; padding: 1rem; border-radius: 0.6rem; border-left: 4px solid #e53238; margin-bottom: 1.5rem; text-align: center;">
                            <p style="color: #c41e3a; margin: 0; font-weight: 600;">
                                ⏰ {reason}
                            </p>
                        </div>
                        """)
        
        except Exception as e:
            logger.error(f"Error loading matches: {e}", exc_info=True)
            st.error(f"❌ Error loading matches: {str(e)}")

except Exception as e:
    logger.error(f"Unexpected error in predict page: {e}", exc_info=True)
    st.error(f"❌ An unexpected error occurred: {str(e)}")
    st.info("Please try refreshing the page or contact support.")

# Tips section
st.markdown("---")

st.html("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>💡 Tips for Success</h2>")

col1, col2, col3 = st.columns(3)

card_style = "background: linear-gradient(135deg, #e2e8f0 0%, #edf2f7 100%); padding: 1.2rem; border-radius: 0.8rem; border-left: 5px solid #e53238; border-right: 2px solid #ffb81c; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"

with col1:
    st.html(f"""
    <div style="{card_style}">
        <h3 style="color: #e53238; border: none; margin-top: 0;">⏰ Timing is Key</h3>
        <p style="color: #666; margin: 0;">Predictions close at kickoff (IST). Don't miss your window!</p>
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
