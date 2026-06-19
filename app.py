"""
FIFA World Cup 2026 Prediction Platform - Main Application
"""
import os
import logging
import streamlit as st
from pathlib import Path
from src.config import Config
from src.storage import Storage
from src.scheduler import start_background_tasks

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

# Initialize config and storage
config = Config()
storage = Storage(config)
storage.initialize_data_layer()

# Start background scheduler (runs once per session)
if 'scheduler_started' not in st.session_state:
    start_background_tasks()
    st.session_state.scheduler_started = True

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# FIFA World Cup 2026 Custom CSS - Enhanced Design & Banner Fixes
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
        /* Add your copied image URL below inside the url('') */
        background: linear-gradient(rgba(26, 71, 42, 0.85), rgba(26, 71, 42, 0.95)), 
                    url('INSERT_YOUR_IMAGE_URL_HERE') center/cover no-repeat;
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
        background-color: #ffffff;
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
    
    /* Custom team colors */
    .team-badge {
        background: linear-gradient(135deg, #e53238 0%, #ffb81c 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 600;
        display: inline-block;
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar - Authentication with Enhanced Design
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
    
    # User stats in sidebar
    user_predictions = storage.get_user_prediction_count(st.session_state.user_id)
    user_correct = storage.get_user_correct_predictions(st.session_state.user_id)
    user_points = storage.get_user_total_points(st.session_state.user_id)
    
    st.sidebar.markdown("### 📊 Your Stats")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("🎯 Predictions", user_predictions)
        st.metric("⭐ Points", user_points)
    with col2:
        accuracy = (user_correct / user_predictions * 100) if user_predictions > 0 else 0
        st.metric("✅ Correct", user_correct)
        st.metric("📈 Accuracy", f"{accuracy:.1f}%")
    
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

# Main page routing
if st.session_state.user_id is None:
    
    # NEW FULL-WIDTH HERO BANNER
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
        <div style="background: white; padding: 1.5rem; border-radius: 0.8rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 4px solid #e53238;">
            <ul style="list-style-type: none; padding-left: 0; margin: 0; font-size: 1.1rem; line-height: 1.8;">
                <li>🌍 <strong>Event:</strong> FIFA World Cup 2026</li>
                <li>🏟️ <strong>Hosts:</strong> 🇺🇸 USA, 🇨🇦 Canada, 🇲🇽 Mexico</li>
                <li>👥 <strong>Teams:</strong> 48 Nations</li>
                <li>⚽ <strong>Matches:</strong> 104 Games</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
else:
    # Pages are automatically loaded from the pages/ directory
    pass
