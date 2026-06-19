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
    /* Main color scheme - FIFA 2026 inspired */
    :root {
        --primary-color: #1a472a;  /* Dark green */
        --secondary-color: #ffb81c; /* Gold */
        --accent-color: #e53238;   /* Red */
        --light-bg: #f5f5f5;
        --card-bg: #ffffff;
    }
    
    /* Main container */
    .main {
        padding: 1rem 2rem;
        background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a472a 0%, #2d5a3d 100%);
    }

    [data-testid="stSidebarNav"] span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Make the links turn gold when you hover over them */
    [data-testid="stSidebarNav"] a:hover span {
        color: #ffb81c !important; 
    }

    /* Keep the SVG icons white as well */
    [data-testid="stSidebarNav"] svg {
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffb81c !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    /* Header styling */
    h1, h2 {
        color: #1a472a;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.1);
        border-bottom: 3px solid #ffb81c;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: #1a472a;
        border-left: 4px solid #e53238;
        padding-left: 0.8rem;
    }

    /* ----------------------------------------------------
       HERO BANNER CSS
       ---------------------------------------------------- */
    .banner-header {
        background: linear-gradient(rgba(26, 71, 42, 0.5), rgba(26, 71, 42, 0.6)), 
                    url('https://s.yimg.com/ny/api/res/1.2/2DOPtSxLvgCKhWuhEIUNTQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTU0MDtjZj13ZWJw/https://media.zenfs.com/en/wdaf_articles_412/6e591ad86accfc2fa04d6bff48ecf693') center/cover no-repeat;
        padding: 4rem 2rem;
        border-radius: 1rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .banner-header h1 {
        color: #ffffff !important;
        border-bottom: none !important;
        font-size: 3.5rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        margin: 0 0 0.5rem 0;
        padding: 0;
    }
    
    .banner-header h2 {
        color: #ffb81c !important;
        border-bottom: none !important;
        font-size: 1.5rem !important;
        margin: 0;
        letter-spacing: 2px;
    }

    .banner-header p {
        color: #f5f5f5;
        font-size: 1.2rem;
        max-width: 600px;
        margin: 1.5rem auto 0 auto;
        opacity: 0.9;
    }
    /* ---------------------------------------------------- */
    
    /* Leaderboard header */
    .leaderboard-header {
        background: linear-gradient(135deg, #1a472a 0%, #e53238 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1.5rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .leaderboard-header h2 {
        color: #ffb81c;
        border: none;
        margin: 0;
        font-size: 1.8rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #ffb81c 0%, #ffa500 100%);
        color: #1a472a !important;
        border: none;
        border-radius: 0.6rem;
        padding: 0.7rem 1.5rem;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        color: #1a472a !important;
    }

    /* Metric Fixes */
    [data-testid="stMetric"] {
        background-color: #e2e8f0;
        padding: 1.2rem;
        border-radius: 0.8rem;
        border: 2px solid #ffb81c;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stMetricLabel"] * {
        color: #1a472a !important; 
        font-weight: 700 !important;
        font-size: 1rem !important;
    }
    
    [data-testid="stMetricValue"] * {
        color: #e53238 !important; 
        font-weight: 800 !important;
        font-size: 2rem !important;
    }

    /* Match and Dashboard Cards */
    .match-card {
        background: linear-gradient(to right, #e2e8f0 0%, #edf2f7 100%);
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border: 2px solid #e0e0e0;
        border-left: 4px solid #ffb81c;
        box-shadow: 0 3px 12px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .match-card:hover {
        border-color: #ffb81c;
        box-shadow: 0 6px 20px rgba(255, 184, 28, 0.15);
        transform: translateX(4px);
    }
    
    .prediction-card {
        background: linear-gradient(135deg, #e2e8f0 0%, #edf2f7 100%);
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border-left: 5px solid #e53238;
        border-right: 2px solid #ffb81c;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .prediction-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 0.8rem;
        border-left: 4px solid #ffb81c;
    }
    
    /* Divider */
    hr {
        border: 1px solid rgba(255, 184, 28, 0.3);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar - Authentication & User Stats
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0;">
        <h1 style="font-size: 3rem; margin: 0;">⚽</h1>
        <h2 style="color: #ffb81c; font-size: 1.8rem; margin: 0.5rem 0; border: none;">WORLD CUP</h2>
        <h3 style="color: #e53238; font-size: 1.5rem; margin: 0; border: none;">2026</h3>
        <p style="color: #ffffff; font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">PREDICTION PLATFORM</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

# LOGIN LOGIC IN SIDEBAR
if st.session_state.user_id is None:
    st.sidebar.subheader("🎬 Enter Tournament")
    username = st.sidebar.text_input(
        "Username", 
        key="login_username", 
        placeholder="Enter your username",
        help="Create your profile to start predicting"
    )
    
    if st.sidebar.button("⚡ Join Now", use_container_width=True, type="primary"):
        if username.strip():
            user = storage.get_or_create_user(username)
            st.session_state.user_id = user['user_id']
            st.session_state.user_name = user['user_name']
            st.success(f"🎉 Welcome to the tournament, {username}!")
            st.rerun()
        else:
            st.sidebar.error("Please enter a username")
else:
    # LOGGED IN SIDEBAR VIEW
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffb81c 0%, #e53238 100%); 
                padding: 1rem; border-radius: 0.8rem; text-align: center; 
                margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
        <p style="color: white; font-size: 0.9rem; margin: 0; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">
            ✅ Logged In As
        </p>
        <p style="color: white; font-size: 1.4rem; margin: 0.5rem 0 0 0; font-weight: 800; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
            {st.session_state.user_name}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    user_predictions = storage.get_user_prediction_count(st.session_state.user_id)
    user_correct = storage.get_user_correct_predictions(st.session_state.user_id)
    user_points = storage.get_user_total_points(st.session_state.user_id)
    
    st.sidebar.markdown("### 📊 Your Stats")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("🎯 Preds", user_predictions)
        st.metric("⭐ Points", user_points)
    with col2:
        accuracy = (user_correct / user_predictions * 100) if user_predictions > 0 else 0
        st.metric("✅ Correct", user_correct)
        st.metric("📈 Acc %", f"{accuracy:.1f}%")
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.rerun()

st.sidebar.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.6); font-size: 0.75rem; margin-top: 2rem;">
    ⚽ FIFA World Cup 2026<br>
    v1.0 | Powered by Data
</div>
""", unsafe_allow_html=True)

# ==========================================
# MAIN PAGE ROUTING
# ==========================================

if st.session_state.user_id is None:
    # ---------------------------------------------------------
    # STATE 1: NOT LOGGED IN (LANDING PAGE)
    # ---------------------------------------------------------
    st.markdown("""
    <div class="banner-header">
        <h1>⚽ WORLD CUP 2026</h1>
        <h2>PREDICTION PLATFORM</h2>
        <p>Join millions of football fans worldwide. Predict match outcomes, climb the global leaderboard, and prove your football knowledge!</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%); 
                    padding: 2rem 1.5rem; border-radius: 1rem; text-align: center;
                    border: 2px solid #ffb81c; color: white; height: 100%;">
            <h3 style="color: #ffb81c; border: none; margin-top: 0; font-size: 1.5rem;">🎯 PREDICT</h3>
            <p style="font-size: 1.1rem; opacity: 0.9;">Make predictions on all 64 matches of the tournament</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e53238 0%, #c41e3a 100%); 
                    padding: 2rem 1.5rem; border-radius: 1rem; text-align: center;
                    border: 2px solid #ffb81c; color: white; height: 100%;">
            <h3 style="color: #ffb81c; border: none; margin-top: 0; font-size: 1.5rem;">🏆 COMPETE</h3>
            <p style="font-size: 1.1rem; opacity: 0.9;">Compete on the global leaderboard with other fans</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ffb81c 0%, #ffa500 100%); 
                    padding: 2rem 1.5rem; border-radius: 1rem; text-align: center;
                    border: 2px solid #1a472a; color: #1a472a; height: 100%;">
            <h3 style="color: #1a472a; border: none; margin-top: 0; font-size: 1.5rem;">⭐ WIN</h3>
            <p style="font-size: 1.1rem; font-weight: 500;">Earn points and climb the rankings to the top</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Scoring Rules")
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 0.8rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 4px solid #1a472a;">
            <ul style="list-style-type: none; padding-left: 0; margin: 0; font-size: 1.1rem; line-height: 1.8;">
                <li>🟢 <strong>Correct Winner:</strong> <span style="color:#1a472a; font-weight:bold;">+3 points</span></li>
                <li>🟡 <strong>Correct Draw:</strong> <span style="color:#ffb81c; font-weight:bold;">+2 points</span></li>
                <li>🔴 <strong>Wrong Prediction:</strong> <span style="color:#e53238; font-weight:bold;">0 points</span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📅 Tournament Info")
        st.markdown("""
        <div style="background: #e2e8f0; padding: 1.5rem; border-radius: 0.8rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 4px solid #e53238;">
            <ul style="list-style-type: none; padding-left: 0; margin: 0; font-size: 1.1rem; line-height: 1.8;">
                <li>🌍 <strong>Event:</strong> FIFA World Cup 2026</li>
                <li>🏟️ <strong>Hosts:</strong> 🇺🇸 USA, 🇨🇦 Canada, 🇲🇽 Mexico</li>
                <li>👥 <strong>Teams:</strong> 48 Nations</li>
                <li>⚽ <strong>Matches:</strong> 104 Games</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

else:
    # ---------------------------------------------------------
    # STATE 2: LOGGED IN (DASHBOARD)
    # ---------------------------------------------------------
    st.markdown("""
    <h1 style="text-align: center; font-size: 2.5rem; margin-bottom: 0;">
        ⚽ WORLD CUP 2026 DASHBOARD
    </h1>
    <p style="text-align: center; color: #e53238; font-size: 1.1rem; margin-bottom: 2rem;">
        🇺🇸 USA | 🇨🇦 CANADA | 🇲🇽 MEXICO
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Tournament Info Section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%); 
                padding: 2rem; border-radius: 0.8rem; margin-bottom: 2rem;
                box-shadow: 0 6px 20px rgba(0,0,0,0.15);">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; color: white; text-align: center;">
            <div>
                <p style="font-size: 0.9rem; color: #ffb81c; margin: 0;">TOURNAMENT</p>
                <h3 style="color: #ffffff; border: none; margin: 0.5rem 0; font-size: 1.4rem;">FIFA 2026</h3>
            </div>
            <div>
                <p style="font-size: 0.9rem; color: #ffb81c; margin: 0;">HOST NATIONS</p>
                <h3 style="color: #ffffff; border: none; margin: 0.5rem 0; font-size: 1.4rem;">3 Countries</h3>
            </div>
            <div>
                <p style="font-size: 0.9rem; color: #ffb81c; margin: 0;">TEAMS</p>
                <h3 style="color: #ffffff; border: none; margin: 0.5rem 0; font-size: 1.4rem;">48 Teams</h3>
            </div>
            <div>
                <p style="font-size: 0.9rem; color: #ffb81c; margin: 0;">MATCHES</p>
                <h3 style="color: #ffffff; border: none; margin: 0.5rem 0; font-size: 1.4rem;">104 Games</h3>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tournament Stats
    st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>📊 Tournament Statistics</h2>", unsafe_allow_html=True)

    try:
        tournament_stats = storage.get_tournament_stats()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            users = int(float(tournament_stats.get('Total Users', 0)))
            st.metric("👥 Users", users)
            
        with col2:
            matches = int(float(tournament_stats.get('Total Matches', 0)))
            st.metric("🎯 Matches", matches)
            
        with col3:
            scheduled = int(float(tournament_stats.get('Scheduled Matches', 0)))
            st.metric("🔜 Upcoming", scheduled)
            
        with col4:
            completed = int(float(tournament_stats.get('Completed Matches', 0)))
            st.metric("✅ Completed", completed)
            
        with col5:
            predictions = int(float(tournament_stats.get('Total Predictions', 0)))
            st.metric("⭐ Predictions", predictions)
            
        st.markdown("---")
    except Exception as e:
        st.warning(f"Could not load tournament stats: {e}")

    # Today's/Upcoming Matches
    st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>🔜 Upcoming Matches</h2>", unsafe_allow_html=True)

    try:
        matches = storage.get_all_matches()
        matches_df = pd.DataFrame(matches)
        
        if matches_df.empty:
            st.info("No matches scheduled yet")
        else:
            # Filter active matches (scheduled or live)
            active_matches = matches_df[matches_df['status'].isin(['scheduled', 'live'])]
            
            if active_matches.empty:
                st.info("No upcoming matches")
            else:
                # Sort by date and time
                active_matches = active_matches.copy()
                active_matches['match_datetime'] = pd.to_datetime(
                    active_matches['match_date'] + ' ' + active_matches['kickoff_time']
                )
                active_matches = active_matches.sort_values('match_datetime')
                
                for idx, (_, match) in enumerate(active_matches.head(10).iterrows()):
                    # Parse US time and convert to IST (+9 hours 30 mins)
                    match_datetime_us = pd.to_datetime(f"{match['match_date']} {match['kickoff_time']}")
                    match_datetime_ist = match_datetime_us + pd.Timedelta(hours=9, minutes=30)
                    
                    st.markdown(f"""
                    <div class="match-card">
                        <div style="display: grid; grid-template-columns: 2fr 1fr 2fr 1.5fr; gap: 1rem; align-items: center;">
                            <div style="text-align: right;">
                                <h4 style="color: #1a472a; margin: 0; font-size: 1.1rem; font-weight: 700;">
                                    {match['team_1']}
                                </h4>
                            </div>
                            <div style="text-align: center;">
                                <span style="background: #ffb81c; color: #1a472a; padding: 0.5rem 0.8rem; 
                                           border-radius: 0.4rem; font-weight: 600; font-size: 0.85rem;">
                                    vs
                                </span>
                            </div>
                            <div style="text-align: left;">
                                <h4 style="color: #1a472a; margin: 0; font-size: 1.1rem; font-weight: 700;">
                                    {match['team_2']}
                                </h4>
                            </div>
                            <div style="text-align: center;">
                                <p style="color: #666; margin: 0; font-size: 0.9rem;">
                                    📅 {match_datetime_ist.strftime('%b %d')}<br>
                                    🕐 {match_datetime_ist.strftime('%H:%M')} IST<br>
                                    📍 {match['venue']}
                                </p>
                            </div>
                        </div>
                        <div style="margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid #e0e0e0;">
                            <span style="background: #e53238; color: white; padding: 0.3rem 0.6rem; 
                                       border-radius: 0.3rem; font-size: 0.8rem; font-weight: 600;">
                                {match['stage']}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading matches: {e}")

    st.markdown("---")

    # Leaderboard Preview
    st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>🏆 Top 10 Leaderboard</h2>", unsafe_allow_html=True)

    try:
        leaderboard = storage.get_leaderboard(limit=10)
        
        if leaderboard:
            lb_df = pd.DataFrame(leaderboard)
            
            # Format display
            display_df = lb_df[[
                'rank', 'user_name', 'total_points', 'accuracy_percentage'
            ]].copy()
            
            display_df.columns = [
                '🏅', 'Player', '⭐ Points', '📊 Accuracy %'
            ]
            
            # Add emoji medals
            display_df['🏅'] = display_df['🏅'].apply(lambda x: 
                '🥇' if x == 1 else '🥈' if x == 2 else '🥉' if x == 3 else f'#{x}'
            )
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Leaderboard will appear once users make predictions")
    except Exception as e:
        st.error(f"Error loading leaderboard: {e}")

    st.markdown("---")

    # User's Stats
    if st.session_state.user_id:
        st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>👤 Your Statistics</h2>", unsafe_allow_html=True)
        
        try:
            col1, col2, col3, col4 = st.columns(4)
            
            predictions = storage.get_user_prediction_count(st.session_state.user_id)
            correct = storage.get_user_correct_predictions(st.session_state.user_id)
            accuracy = (correct / predictions * 100) if predictions > 0 else 0
            points = storage.get_user_total_points(st.session_state.user_id)
            
            with col1:
                st.metric("🎯 Predictions", predictions)
            with col2:
                st.metric("✅ Correct", correct)
            with col3:
                st.metric("📊 Accuracy", f"{accuracy:.1f}%")
            with col4:
                st.metric("⭐ Total Points", points)
            
            # User rank
            user_rank = storage.get_user_rank(st.session_state.user_id)
            if user_rank:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ffb81c 0%, #ffa500 100%); 
                            padding: 1.5rem; border-radius: 0.8rem; text-align: center;
                            color: #1a472a; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-top: 1rem;">
                    <h3 style="color: #1a472a; border: none; margin: 0; font-size: 1.8rem;">
                        🎯 Rank #{user_rank['rank']}
                    </h3>
                    <p style="margin: 0.5rem 0 0 0; font-weight: 600;">You're in the top {(user_rank['rank'] / len(storage.get_leaderboard())) * 100:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error loading user stats: {e}")

    st.markdown("---")

    # Information Section
    st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>ℹ️ How to Play</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="prediction-card">
            <h3 style="color: #e53238; border: none; margin-top: 0;">🎯 Make Predictions</h3>
            <ul style="color: #666; margin: 0;">
                <li>Go to the <b>Predict</b> page</li>
                <li>Choose upcoming matches</li>
                <li>Select your predicted winner</li>
                <li>Lock in before kickoff</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="prediction-card">
            <h3 style="color: #e53238; border: none; margin-top: 0;">📊 Track Performance</h3>
            <ul style="color: #666; margin: 0;">
                <li>Visit <b>My Predictions</b></li>
                <li>View your prediction history</li>
                <li>Check accuracy metrics</li>
                <li>Earn points for correct picks</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="prediction-card">
            <h3 style="color: #e53238; border: none; margin-top: 0;">🏆 Climb Rankings</h3>
            <ul style="color: #666; margin: 0;">
                <li>Check the <b>Leaderboard</b></li>
                <li>Compete globally</li>
                <li>Earn achievement badges</li>
                <li>Have fun! ⚽</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Scoring Info
    st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>⭐ Scoring System</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); 
                    padding: 1.5rem; border-radius: 0.8rem; text-align: center;
                    color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h3 style="color: #ffffff; border: none; margin: 0;">✅ CORRECT</h3>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; font-weight: 700;">+3 POINTS</p>
            <small>Predict the winner correctly</small>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ffb81c 0%, #ffa500 100%); 
                    padding: 1.5rem; border-radius: 0.8rem; text-align: center;
                    color: #1a472a; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h3 style="color: #1a472a; border: none; margin: 0;">🤝 DRAW</h3>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; font-weight: 700;">+2 POINTS</p>
            <small>Predict a draw correctly</small>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e53238 0%, #c41e3a 100%); 
                    padding: 1.5rem; border-radius: 0.8rem; text-align: center;
                    color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h3 style="color: #ffffff; border: none; margin: 0;">❌ INCORRECT</h3>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; font-weight: 700;">0 POINTS</p>
            <small>Wrong prediction</small>
        </div>
        """, unsafe_allow_html=True)
