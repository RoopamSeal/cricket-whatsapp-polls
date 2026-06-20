"""
Leaderboard page - Global rankings with FIFA 2026 design
"""
import streamlit as st
import pandas as pd
import datetime
from src.config import Config
from src.storage import Storage

# 1. Session state safety initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# Initialize
config = Config()
storage = Storage(config)
storage.initialize_data_layer()

st.markdown("""
<h1 style="text-align: center;">🏆 GLOBAL LEADERBOARD</h1>
<p style="text-align: center; color: #e53238; font-size: 1rem;">
    See how you rank against players worldwide!
</p>
""", unsafe_allow_html=True)

st.markdown("---")

try:
    # Get a baseline leaderboard just to configure the slider limits
    initial_leaderboard = storage.get_leaderboard()
    
    if not initial_leaderboard:
        st.info("📊 Leaderboard will appear once players make predictions")
        st.stop()
    
    initial_df = pd.DataFrame(initial_leaderboard)
    max_possible_preds = int(initial_df['total_predictions'].max())
    
    # ==========================================
    # STATIC WIDGETS
    # These remain outside the fragment so they don't reset every 10 seconds
    # ==========================================
    st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>🔍 Filter & Sort</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_predictions = st.slider(
            "Minimum Predictions",
            min_value=0,
            max_value=max_possible_preds if max_possible_preds > 0 else 1,
            value=0,
            help="Filter players with minimum number of predictions"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort By",
            options=['Total Points', 'Accuracy %', 'Total Predictions', 'Rank'],
            help="Choose sorting method"
        )
    
    with col3:
        st.write("")  # Placeholder
    
    st.markdown("---")
    
    # ==========================================
    # AUTO-REFRESHING FRAGMENT
    # This block executes every 10s to fetch live data
    # ==========================================
    @st.fragment(run_every="10s")
    def live_leaderboard_display(min_preds, sort_method):
        # Fetch fresh data on every background tick
        live_data = storage.get_leaderboard()
        if not live_data:
            st.info("Waiting for data...")
            return
            
        lb_df = pd.DataFrame(live_data)
        
        # Apply filters
        filtered_df = lb_df[lb_df['total_predictions'] >= min_preds].copy()
        
        # Apply sorting
        if sort_method == 'Total Points':
            filtered_df = filtered_df.sort_values('total_points', ascending=False)
        elif sort_method == 'Accuracy %':
            filtered_df = filtered_df.sort_values('accuracy_percentage', ascending=False)
        elif sort_method == 'Total Predictions':
            filtered_df = filtered_df.sort_values('total_predictions', ascending=False)
        else:
            filtered_df = filtered_df.sort_values('rank')
        
        filtered_df['rank'] = range(1, len(filtered_df) + 1)
        
        # Display leaderboard header
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%); 
                    padding: 1.5rem; border-radius: 0.8rem; margin-bottom: 1.5rem;
                    color: #ffb81c; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h2 style="color: #ffb81c; border: none; margin: 0;">
                🏅 RANKINGS ({len(filtered_df)} Players)
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Display top 3 with special styling
        if len(filtered_df) >= 1:
            st.markdown("<h3 style='color: #1a472a; border: none; margin-bottom: 1.5rem;'>🥇🥈🥉 Podium</h3>", unsafe_allow_html=True)
            
            podium_cols = st.columns(3)
            
            # Gold (1st place)
            with podium_cols[0]:
                top1 = filtered_df.iloc[0]
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ffb81c 0%, #ffa500 100%); 
                            padding: 1.5rem; border-radius: 0.8rem; text-align: center;
                            color: #1a472a; box-shadow: 0 6px 20px rgba(255, 184, 28, 0.3);">
                    <h1 style="color: #1a472a; border: none; margin: 0;">🥇</h1>
                    <h3 style="color: #1a472a; border: none; margin: 0.5rem 0;">1st Place</h3>
                    <h2 style="color: #1a472a; border: none; margin: 0.5rem 0; font-size: 1.2rem;">{top1['user_name']}</h2>
                    <div style="background: rgba(0,0,0,0.1); padding: 0.8rem; border-radius: 0.5rem; margin-top: 1rem;">
                        <p style="color: #1a472a; margin: 0; font-weight: 600;">⭐ {int(top1['total_points'])} Points</p>
                        <p style="color: #1a472a; margin: 0.3rem 0 0 0; font-size: 0.9rem;">📊 {top1['accuracy_percentage']:.1f}% Accuracy</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Silver (2nd place)
            if len(filtered_df) >= 2:
                top2 = filtered_df.iloc[1]
                with podium_cols[1]:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #c0c0c0 0%, #a8a8a8 100%); 
                                padding: 1.5rem; border-radius: 0.8rem; text-align: center;
                                color: #ffffff; box-shadow: 0 6px 20px rgba(192, 192, 192, 0.3);">
                        <h1 style="color: #ffffff; border: none; margin: 0;">🥈</h1>
                        <h3 style="color: #ffffff; border: none; margin: 0.5rem 0;">2nd Place</h3>
                        <h2 style="color: #ffffff; border: none; margin: 0.5rem 0; font-size: 1.2rem;">{top2['user_name']}</h2>
                        <div style="background: rgba(0,0,0,0.1); padding: 0.8rem; border-radius: 0.5rem; margin-top: 1rem;">
                            <p style="color: #ffffff; margin: 0; font-weight: 600;">⭐ {int(top2['total_points'])} Points</p>
                            <p style="color: #ffffff; margin: 0.3rem 0 0 0; font-size: 0.9rem;">📊 {top2['accuracy_percentage']:.1f}% Accuracy</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Bronze (3rd place)
            if len(filtered_df) >= 3:
                top3 = filtered_df.iloc[2]
                with podium_cols[2]:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #cd7f32 0%, #b87333 100%); 
                                padding: 1.5rem; border-radius: 0.8rem; text-align: center;
                                color: #ffffff; box-shadow: 0 6px 20px rgba(205, 127, 50, 0.3);">
                        <h1 style="color: #ffffff; border: none; margin: 0;">🥉</h1>
                        <h3 style="color: #ffffff; border: none; margin: 0.5rem 0;">3rd Place</h3>
                        <h2 style="color: #ffffff; border: none; margin: 0.5rem 0; font-size: 1.2rem;">{top3['user_name']}</h2>
                        <div style="background: rgba(0,0,0,0.1); padding: 0.8rem; border-radius: 0.5rem; margin-top: 1rem;">
                            <p style="color: #ffffff; margin: 0; font-weight: 600;">⭐ {int(top3['total_points'])} Points</p>
                            <p style="color: #ffffff; margin: 0.3rem 0 0 0; font-size: 0.9rem;">📊 {top3['accuracy_percentage']:.1f}% Accuracy</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Full table
        st.markdown("<h3 style='color: #1a472a; border: none; margin-bottom: 1rem;'>📊 Complete Rankings</h3>", unsafe_allow_html=True)
        
        # Create display dataframe
        display_df = filtered_df[[
            'rank', 'user_name', 'total_points', 'total_predictions',
            'correct_predictions', 'accuracy_percentage'
        ]].copy()
        
        display_df.columns = [
            '🏅', 'Player', '⭐ Points', '🎯 Preds', '✅ Correct', '📊 Accuracy %'
        ]
        
        # Add medal emojis
        display_df['🏅'] = display_df['🏅'].apply(lambda x: 
            '🥇' if x == 1 else '🥈' if x == 2 else '🥉' if x == 3 else f'#{x}'
        )
        
        display_df['📊 Accuracy %'] = display_df['📊 Accuracy %'].apply(lambda x: f"{x:.1f}%")
        
        # Deprecation Warning Fixed: width="stretch" replaces use_container_width=True
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Highlight user's rank
        if st.session_state.get('user_id'):
            user_rank = storage.get_user_rank(st.session_state.user_id)
            if user_rank:
                st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>👤 Your Ranking</h2>", unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <p style="color: #ffb81c; margin: 0; font-size: 0.9rem;">🎯 Rank</p>
                        <h3 style="color: #ffb81c; border: none; margin: 0.5rem 0; font-size: 2rem;">#{user_rank['rank']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <p style="color: #ffb81c; margin: 0; font-size: 0.9rem;">⭐ Points</p>
                        <h3 style="color: #ffb81c; border: none; margin: 0.5rem 0; font-size: 2rem;">{user_rank['total_points']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <p style="color: #ffb81c; margin: 0; font-size: 0.9rem;">📊 Accuracy</p>
                        <h3 style="color: #ffb81c; border: none; margin: 0.5rem 0; font-size: 2rem;">{user_rank['accuracy_percentage']:.1f}%</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <p style="color: #ffb81c; margin: 0; font-size: 0.9rem;">🎯 Preds</p>
                        <h3 style="color: #ffb81c; border: none; margin: 0.5rem 0; font-size: 2rem;">{user_rank['total_predictions']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Progress to next rank
                total_players = len(filtered_df)
                if total_players > 0:
                    rank_pct = (user_rank['rank'] / total_players) * 100
                    
                    st.markdown(f"""
                    <div style="background: #f5f5f5; padding: 1.5rem; border-radius: 0.8rem;
                                border-left: 4px solid #ffb81c;">
                        <p style="color: #1a472a; margin: 0; font-weight: 600;">
                            You're in the top {100 - rank_pct:.1f}% of {total_players} players 🎯
                        </p>
                        <div style="background: #e0e0e0; height: 10px; border-radius: 5px; margin-top: 0.8rem; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #ffb81c 0%, #e53238 100%); 
                                        height: 100%; width: {100 - rank_pct}%; border-radius: 5px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Display live timestamp
        now = datetime.datetime.now().strftime("%H:%M:%S")
        st.caption(f"🔄 Live rankings updated at: {now} (Auto-refreshes every 10 seconds)")

    # Execute the fragment
    live_leaderboard_display(min_predictions, sort_by)

except Exception as e:
    st.error(f"Error loading leaderboard: {e}")
