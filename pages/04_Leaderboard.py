"""
Leaderboard page with auto-refresh.
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Leaderboard", layout="wide")

st.markdown("""
<h1 style="text-align: center;">🏆 GLOBAL LEADERBOARD</h1>
""", unsafe_allow_html=True)

st.markdown("---")

# Import
try:
    from src.storage import get_storage
    storage = get_storage()
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

try:
    # Get leaderboard
    leaderboard = storage.get_leaderboard(limit=100)
    
    if not leaderboard:
        st.info("No leaderboard data yet")
        st.stop()
    
    # Convert to DataFrame
    df = pd.DataFrame(leaderboard)
    df = df[['rank', 'user_name', 'total_points', 'accuracy']].copy()
    df.columns = ['🏅 Rank', '👤 Player', '⭐ Points', '📊 Accuracy %']
    
    # Medal emoji
    df['🏅 Rank'] = df['🏅 Rank'].apply(
        lambda x: '🥇' if x == 1 else '🥈' if x == 2 else '🥉' if x == 3 else f'#{x}'
    )
    
    # Display
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # User's rank
    if 'user_id' in st.session_state and st.session_state.user_id:
        st.markdown("---")
        st.subheader("Your Rank")
        
        user_rank = next((l for l in leaderboard if l['user_id'] == st.session_state.user_id), None)
        
        if user_rank:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏅 Rank", f"#{user_rank['rank']}")
            with col2:
                st.metric("⭐ Points", user_rank['total_points'])
            with col3:
                st.metric("📊 Accuracy", f"{user_rank['accuracy']:.1f}%")
            with col4:
                st.metric("🎯 Predictions", user_rank['total_predictions'])
    
    # Refresh info
    st.info("🔄 Leaderboard updates automatically")

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    st.error(f"Error: {str(e)}")
