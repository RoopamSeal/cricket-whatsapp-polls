"""
Admin page - Administrative functions with PostgreSQL backend
"""
import streamlit as st
import pandas as pd
from src.config import Config
from src.storage import Storage

# Initialize
config = Config()
storage = Storage(config)
storage.initialize_data_layer()

st.markdown("""
<h1 style="text-align: center;">⚙️ ADMIN CONSOLE</h1>
<p style="text-align: center; color: #e53238; font-size: 1rem;">
    Manage tournament data here
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Simple auth - check if admin
admin_password = st.secrets.get("admin", {}).get("password", "admin123")

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    password = st.text_input("Enter admin password:", type="password")
    if st.button("🔓 Authenticate", use_container_width=True, type="primary"):
        if password == admin_password:
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("❌ Invalid password")
    st.stop()

# ========== TAB STRUCTURE ==========
tab1, tab2, tab3 = st.tabs(["📊 Database", "✍️ Manual Result Entry", "🔧 Maintenance"])

# ========== TAB 1: Database Statistics ==========
with tab1:
    st.markdown("## 📊 Database Statistics")
    
    # Simple stats fetch
    tables = ["users", "matches", "predictions", "match_results"]
    cols = st.columns(len(tables))
    for i, table in enumerate(tables):
        count = storage.count_table(table)
        cols[i].metric(table.capitalize(), count)
    
    st.markdown("---")
    table_choice = st.selectbox("Select table to preview", tables)
    # Fetch raw data from Postgres
    data = storage.db.fetch_all(f"SELECT * FROM {table_choice} LIMIT 10")
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No data found.")

# ========== TAB 2: Manual Result Entry ==========
with tab2:
    st.markdown("## ✍️ Manual Result Entry")
    
    # Get all scheduled matches
    matches = storage.db.fetch_all("SELECT * FROM matches WHERE status = 'scheduled'")
    
    if matches:
        match_options = {f"{m['team_1']} vs {m['team_2']} ({m['match_date']})": m for m in matches}
        selected_match_str = st.selectbox("Select match", list(match_options.keys()))
        selected_match = match_options[selected_match_str]
        
        winner = st.radio("Winner", [selected_match['team_1'], selected_match['team_2'], 'draw'], horizontal=True)
        
        if st.button("💾 Save Result", use_container_width=True, type="primary"):
            # 1. Update Match Status
            storage.db.update("matches", {"status": "completed"}, "match_id = ?", (selected_match['match_id'],))
            
            # 2. Insert Match Result
            import uuid
            result_data = {
                "result_id": str(uuid.uuid4()),
                "match_id": selected_match['match_id'],
                "actual_winner": winner,
                "result_timestamp": pd.Timestamp.now().isoformat()
            }
            storage.db.insert("match_results", result_data)
            
            # 3. Points calculation logic would trigger here (Automated by your SQL logic)
            st.success(f"✅ Result saved for {selected_match['team_1']} vs {selected_match['team_2']}!")
    else:
        st.info("No scheduled matches available.")

# ========== TAB 3: Maintenance ==========
with tab3:
    st.markdown("## 🔧 Maintenance")
    if st.button("🔴 RESET ALL TABLES (DANGER)", use_container_width=True):
        if st.checkbox("I am absolutely sure"):
            try:
                # Direct SQL to clear data
                storage.db.execute("DELETE FROM predictions")
                storage.db.execute("DELETE FROM match_results")
                storage.db.execute("DELETE FROM user_stats")
                storage.db.execute("UPDATE matches SET status = 'scheduled'")
                st.success("✅ All data wiped except matches.")
            except Exception as e:
                st.error(f"Error: {e}")
