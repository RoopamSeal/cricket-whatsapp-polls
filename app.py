import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="FIFA World Cup 2026 Poll",
    page_icon="🏆",
    layout="wide" 
)

# ==========================================
# 2. DATA MANAGEMENT
# ==========================================
FIXTURE_FILE = "data/FIFA2026_schedule_fixtures.csv" # Ensure this is in the same directory
VOTES_FILE = "votes.csv"

# Initialize votes.csv with the requested columns if it doesn't exist
if not os.path.exists(VOTES_FILE):
    pd.DataFrame(
        columns=["vote_id", "match_number", "username", "prediction", "timestamp", "score"]
    ).to_csv(VOTES_FILE, index=False)

@st.cache_data(ttl=60)
def load_schedule():
    try:
        # Load the CSV. If using GitHub, use the RAW URL here.
        df = pd.read_csv(FIXTURE_FILE)
        
        # Strip whitespace from column names to prevent key errors
        df.columns = df.columns.str.strip()
        
        # Explicitly parse the DD-MM-YYYY format from your date_dt column
        df['date_dt'] = pd.to_datetime(df['date_dt'], format='%d-%m-%Y', errors='coerce').dt.date
        
        # Drop rows where dates failed to parse (just in case there are empty rows at the bottom)
        df = df.dropna(subset=['date_dt'])
        
        return df
    except Exception as e:
        st.error(f"⚠️ Failed to load fixtures: {e}")
        st.stop()

def load_votes():
    return pd.read_csv(VOTES_FILE)

def save_vote(username, match_number, prediction):
    votes_df = load_votes()
    
    # Check if user already voted for this match
    if not votes_df[(votes_df['username'] == username) & (votes_df['match_number'] == match_number)].empty:
        return False 
        
    # Create the new vote record. 
    # Score initializes at 0. (Points will be awarded later when real match results are verified).
    new_vote = pd.DataFrame([{
        "vote_id": str(uuid.uuid4()),
        "match_number": match_number,
        "username": username, 
        "prediction": prediction,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": 0 
    }])
    
    votes_df = pd.concat([votes_df, new_vote], ignore_index=True)
    votes_df.to_csv(VOTES_FILE, index=False)
    return True

# ==========================================
# 3. USER INTERFACE LAYOUT
# ==========================================

left_col, right_col = st.columns([2, 1], gap="large")

# ------------------------------------------
# LEFT COLUMN: Polling Interface
# ------------------------------------------
with left_col:
    st.title("🏆 FIFA World Cup 2026 Poll")
    st.write("---")
    
    username = st.text_input("Enter your Username to vote:", placeholder="e.g., Roopam")
    
    if username:
        schedule = load_schedule()
        
        # Get today's date and filter the schedule based on the date_dt column
        today = datetime.today().date()
        today_matches = schedule[schedule['date_dt'] == today]
        
        if today_matches.empty:
            st.info(f"No matches scheduled for today ({today.strftime('%d-%m-%Y')}). Check back later!")
        else:
            votes_df = load_votes()
            
            # Loop through today's matches to render polls
            for index, row in today_matches.iterrows():
                match_num = row['match_number']
                team_a = row['team 1']
                team_b = row['team 2']
                
                # Verify if user has already voted
                user_voted = not votes_df[(votes_df['username'] == username) & (votes_df['match_number'] == match_num)].empty
                
                st.write("") 
                st.subheader(f"{match_num}: {team_a} vs {team_b}")
                
                if user_voted:
                    predicted_team = votes_df[(votes_df['username'] == username) & (votes_df['match_number'] == match_num)].iloc[0]['prediction']
                    st.success(f"✅ Voted for: **{predicted_team}**")
                else:
                    # Create the radio buttons
                    prediction = st.radio(
                        "Select your prediction:",
                        [team_a, team_b, "Draw"],
                        key=f"radio_{match_num}",
                        label_visibility="collapsed"
                    )
                    
                    if st.button("Submit Prediction", key=f"btn_{match_num}", type="primary"):
                        success = save_vote(username, match_num, prediction)
                        if success:
                            st.balloons() 
                            st.success("Vote recorded successfully!")
                            st.rerun() 

# ------------------------------------------
# RIGHT COLUMN: Leaderboard
# ------------------------------------------
with right_col:
    st.header("🏅 Leaderboard")
    
    votes_df = load_votes()
    
    if votes_df.empty:
        st.info("No votes yet. Be the first to predict!")
    else:
        # Calculate scores per user
        leaderboard = votes_df.groupby('username')['score'].sum().reset_index()
        leaderboard = leaderboard.sort_values(by='score', ascending=False).head(5)
        leaderboard.index = range(1, len(leaderboard) + 1)
        
        st.dataframe(
            leaderboard,
            column_config={
                "username": st.column_config.TextColumn("Player Name", width="medium"),
                "score": st.column_config.NumberColumn("Total Points", format="%d 🏆")
            },
            hide_index=False,
            use_container_width=True
        )
        st.caption("Note: Scores are awarded (10 points) once match results are finalized!")
