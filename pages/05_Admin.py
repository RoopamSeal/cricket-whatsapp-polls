"""
Admin page - Premium dashboard with action cards
"""
import streamlit as st
import pandas as pd
from src.config import Config
from src.storage import Storage
from src.fixtures import FixtureLoader, create_sample_fixtures
from src.simulator import ResultSimulator
from src.leaderboard import LeaderboardManager
from src.ui import inject_global_css, admin_action_card

# Initialize
config = Config()
storage = Storage(config)
storage.initialize_data_layer()

inject_global_css()
st.set_page_config(page_title="Admin - World Cup 2026", layout="wide")

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
    ">⚙️ Admin Console</div>
    <div style="
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.7);
    ">Tournament management and control.</div>
</div>
""", unsafe_allow_html=True)

# Simple auth
admin_password = st.secrets.get("admin_password", "admin123")

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.markdown("---")
    st.warning("🔒 Admin Authentication Required")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter admin password:", type="password", label_visibility="collapsed")
        if st.button("🔓 Authenticate", use_container_width=True, type="primary"):
            if password == admin_password:
                st.session_state.admin_authenticated = True
                st.success("Authenticated!")
                st.rerun()
            else:
                st.error("Invalid password")
    st.stop()

st.markdown("""
<div style="
    padding: 1rem;
    background: linear-gradient(135deg, rgba(0, 200, 150, 0.15) 0%, rgba(0, 200, 150, 0.08) 100%);
    border: 1px solid rgba(0, 200, 150, 0.4);
    border-radius: 12px;
    color: #00C896;
    font-weight: 600;
">✅ Admin Mode Active</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Admin tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🎯 Fixtures",
    "🎮 Simulator",
    "🏆 Leaderboard",
    "🔧 Maintenance"
])

# ========== TAB 1: Dashboard ==========
with tab1:
    st.markdown('<h2>Database Overview</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    try:
        sizes = storage.get_database_size()
        
        with col1:
            st.markdown(f"""
            <div class="glass-container" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">👥</div>
                <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; font-weight: 600; margin-bottom: 0.5rem;">Users</div>
                <div style="font-size: 1.8rem; font-weight: 900; color: #00C896;">{sizes.get('users', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="glass-container" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚽</div>
                <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; font-weight: 600; margin-bottom: 0.5rem;">Matches</div>
                <div style="font-size: 1.8rem; font-weight: 900; color: #00C896;">{sizes.get('matches', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="glass-container" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; font-weight: 600; margin-bottom: 0.5rem;">Predictions</div>
                <div style="font-size: 1.8rem; font-weight: 900; color: #00C896;">{sizes.get('predictions', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="glass-container" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
                <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; font-weight: 600; margin-bottom: 0.5rem;">Results</div>
                <div style="font-size: 1.8rem; font-weight: 900; color: #00C896;">{sizes.get('results', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="glass-container" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⭐</div>
                <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; font-weight: 600; margin-bottom: 0.5rem;">Points</div>
                <div style="font-size: 1.8rem; font-weight: 900; color: #00C896;">{sizes.get('points', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
    st.markdown('<h2>Data Preview</h2>', unsafe_allow_html=True)
    
    table_choice = st.selectbox(
        "Select table to preview",
        ["users", "matches", "predictions", "results", "points"]
    )
    
    try:
        if table_choice == "users":
            df = pd.read_csv(config.USER_MASTER_PATH)
        elif table_choice == "matches":
            df = pd.read_csv(config.MATCH_MASTER_PATH)
        elif table_choice == "predictions":
            df = pd.read_csv(config.PREDICTION_FACT_PATH)
        elif table_choice == "results":
            df = pd.read_csv(config.MATCH_RESULT_PATH)
        else:
            df = pd.read_csv(config.POINTS_FACT_PATH)
        
        st.dataframe(df.head(10), use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

# ========== TAB 2: Fixtures ==========
with tab2:
    st.markdown('<h2>Fixture Management</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3>📋 Current Fixtures</h3>', unsafe_allow_html=True)
        try:
            matches = storage.get_all_matches()
            st.metric("Total Matches", len(matches))
            
            if matches:
                matches_df = pd.DataFrame(matches)
                st.write(matches_df['status'].value_counts().to_dict())
        except Exception as e:
            st.error(f"Error: {e}")
    
    with col2:
        st.markdown('<h3>📥 Load Fixtures</h3>', unsafe_allow_html=True)
        
        admin_action_card(
            "📦",
            "Sample Fixtures",
            "Load sample FIFA 2026 fixtures",
            "Load Samples",
            lambda: (
                storage.load_fixtures(create_sample_fixtures()),
                st.success(f"Loaded {len(create_sample_fixtures())} sample fixtures!")
            )
        )
    
    st.markdown("---")
    st.markdown('<h2>Upload Custom Fixtures</h2>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    
    if uploaded_file:
        try:
            fixtures_df = pd.read_csv(uploaded_file)
            st.dataframe(fixtures_df)
            
            if st.button("✅ Load Uploaded Fixtures", use_container_width=True, type="primary"):
                fixture_loader = FixtureLoader(config)
                if fixture_loader.validate_fixtures(fixtures_df):
                    storage.load_fixtures(fixtures_df)
                    st.success(f"Loaded {len(fixtures_df)} fixtures!")
                else:
                    st.error("Fixture validation failed")
        except Exception as e:
            st.error(f"Error: {e}")

# ========== TAB 3: Simulator ==========
with tab3:
    st.markdown('<h2>Match Result Simulator</h2>', unsafe_allow_html=True)
    
    simulator = ResultSimulator(config, storage)
    
    col1, col2 = st.columns(2)
    
    with col1:
        admin_action_card(
            "🎮",
            "Auto-Simulate",
            "Simulate completed matches",
            "Run Auto-Simulator",
            lambda: (
                st.success(f"Simulated {simulator.auto_simulate_completed_matches()} matches")
            )
        )
    
    with col2:
        admin_action_card(
            "💥",
            "Bulk Simulate",
            "Simulate ALL match results",
            "Bulk Simulate",
            lambda: (
                st.success(f"Simulated {simulator.bulk_simulate_all_results()} matches")
            )
        )
    
    st.markdown("---")
    st.markdown('<h2>Manual Result Entry</h2>', unsafe_allow_html=True)
    
    try:
        matches = storage.get_matches_by_status('scheduled')
        if matches:
            match_dict = {f"{m['team_1']} vs {m['team_2']}" : m for m in matches}
            
            selected_match_str = st.selectbox(
                "Select match",
                list(match_dict.keys()),
                label_visibility="collapsed"
            )
            
            selected_match = match_dict[selected_match_str]
            
            winner = st.radio(
                "Winner",
                [selected_match['team_1'], selected_match['team_2'], 'draw'],
                horizontal=True
            )
            
            if st.button("💾 Save Result", use_container_width=True, type="primary"):
                storage.save_match_result(selected_match['match_id'], winner)
                storage.update_match_status(selected_match['match_id'], 'completed')
                st.success("Result saved!")
        else:
            st.info("No scheduled matches")
    except Exception as e:
        st.error(f"Error: {e}")

# ========== TAB 4: Leaderboard ==========
with tab4:
    st.markdown('<h2>Leaderboard Management</h2>', unsafe_allow_html=True)
    
    leaderboard_mgr = LeaderboardManager(config, storage)
    
    admin_action_card(
        "🔄",
        "Refresh Leaderboard",
        "Compute leaderboard and gold tables",
        "Refresh Now",
        lambda: (
            leaderboard_mgr.refresh_all_gold_tables(),
            st.success("Leaderboard refreshed!")
        )
    )
    
    st.markdown("---")
    st.markdown('<h2>Current Rankings</h2>', unsafe_allow_html=True)
    
    try:
        leaderboard = storage.get_leaderboard()
        if leaderboard:
            lb_df = pd.DataFrame(leaderboard)
            st.dataframe(
                lb_df[[
                    'rank', 'user_name', 'total_points',
                    'total_predictions', 'accuracy_percentage'
                ]],
                use_container_width=True
            )
        else:
            st.info("Leaderboard empty")
    except Exception as e:
        st.error(f"Error: {e}")

# ========== TAB 5: Maintenance ==========
with tab5:
    st.markdown('<h2>Maintenance & Reset</h2>', unsafe_allow_html=True)
    st.warning("⚠️ Dangerous operations - use with extreme caution!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3>📈 Statistics</h3>', unsafe_allow_html=True)
        if st.button("View Statistics", use_container_width=True):
            try:
                stats = storage.get_tournament_stats()
                for key, value in stats.items():
                    st.metric(key, value)
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.markdown('<h3>🗑️ Dangerous Zone</h3>', unsafe_allow_html=True)
        
        if st.checkbox("⚠️ I understand this will delete all data"):
            if st.button("🔴 RESET ALL TABLES", use_container_width=True, type="secondary"):
                try:
                    storage.reset_all_tables()
                    st.success("All tables reset!")
                except Exception as e:
                    st.error(f"Error: {e}")
