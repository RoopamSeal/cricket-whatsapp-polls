"""
Admin page - Administrative functions with PostgreSQL backend
"""
import streamlit as st
import pandas as pd
from src.config import Config
from src.storage import get_storage
from src.email_service import EmailService

config = Config()
storage = get_storage()
service = EmailService()

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
            ok = storage.save_result(selected_match['match_id'], winner)
            if ok:
                st.success(f"✅ Result saved for {selected_match['team_1']} vs {selected_match['team_2']}!")
                st.rerun()
            else:
                st.error("❌ Failed to save result. Check logs.")
    else:
        st.info("No scheduled matches available.")

# ========== TAB 3: Maintenance ==========
# ========== TAB 3: Maintenance ==========
with tab3:

    st.markdown("## 🔧 Maintenance")

    # -----------------------------
    # RESULT SYNC
    # -----------------------------
    st.markdown("### 📡 Match Data")

    if st.button(
        "🔄 Sync Results from API",
        key="sync_results",
        use_container_width=True
    ):
        try:
            updated = storage.sync_results_from_api("WC")

            st.success(
                f"✅ Synced successfully ({updated} updated)"
            )

        except Exception as e:
            st.error(f"Sync failed: {e}")

    st.markdown("---")

    # =============================
    # EMAIL REMINDERS SECTION
    # =============================

    st.markdown("""
    <div style="
        background:linear-gradient(
            135deg,
            #1a472a,
            #14532d
        );
        padding:20px;
        border-radius:18px;
        margin-bottom:20px;
        color:white;
    ">
        <h3>📧 Email Reminder Center</h3>
        <p>
        Send prediction reminders to all registered users.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "📨 Send Reminder Now",
            key="manual_email",
            use_container_width=True,
            type="primary"
        ):

            with st.spinner(
                "Sending reminder emails..."
            ):

                try:

                    sent = service.send_daily_reminders()

                    st.success(
                        f"✅ Sent to {sent} users"
                    )

                except Exception as e:

                    st.error(
                        f"Email failed: {str(e)}"
                    )

    with col2:

        if st.button(
            "🧪 Send Test Email",
            key="test_email",
            use_container_width=True
        ):

            try:

                admin_email = storage.db.fetch_one("""
                    SELECT email
                    FROM users
                    WHERE email IS NOT NULL
                    LIMIT 1
                """)

                if admin_email:

                    service.send_test_email(
                        admin_email["email"]
                    )

                    st.success(
                        f"Test sent → {admin_email['email']}"
                    )

                else:
                    st.warning(
                        "No user email found"
                    )

            except Exception as e:
                st.error(str(e))

    st.markdown("---")

    # -----------------------------
    # RESET
    # -----------------------------
    st.markdown("### ⚠️ Dangerous Actions")

    confirm = st.checkbox(
        "I understand this deletes prediction data"
    )

    if st.button(
        "🔴 RESET ALL TABLES",
        use_container_width=True,
        disabled=not confirm
    ):

        try:

            storage.db.execute(
                "DELETE FROM predictions"
            )

            storage.db.execute(
                "DELETE FROM match_results"
            )

            storage.db.execute(
                "DELETE FROM user_stats"
            )

            storage.db.execute(
                """
                UPDATE matches
                SET status='scheduled'
                """
            )

            st.success(
                "Database reset complete"
            )

        except Exception as e:

            st.error(str(e))
