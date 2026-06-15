import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid

# Configure the Streamlit page
st.set_page_config(
    page_title="FIFA World Cup Poll",
    page_icon="⚽",
    layout="wide"
)

# Setup data directories and files
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
FIXTURE_FILE = "data/FIFA2026_schedule_fixtures.csv"
VOTES_FILE = "data/votes.csv"

# Create votes file automatically if it doesn't exist
try:
    pd.read_csv(VOTES_FILE)
except FileNotFoundError:
    pd.DataFrame(
        columns=[
            "vote_id",
            "match_number",
            "username",
            "prediction",
            "timestamp"
        ]
    ).to_csv(VOTES_FILE, index=False)

@st.cache_data
def load_fixture():
    # Attempt to load fixtures, handle gracefully if the user forgot to add the CSV
    try:
        df = pd.read_csv(FIXTURE_FILE)
        df["date_dt"] = pd.to_datetime(
            df["date_dt"],
            format="%d-%m-%Y",
            errors="coerce"
        )
        return df
    except FileNotFoundError:
        st.error(f"⚠️ Fixture file not found. Please ensure `{FIXTURE_FILE}` exists.")
        st.stop()

def load_votes():
    return pd.read_csv(VOTES_FILE)

def save_vote(record):
    votes = load_votes()
    # Add new record to the end of the dataframe
    votes.loc[len(votes)] = record
    votes.to_csv(VOTES_FILE, index=False)

# --- UI Starts Here ---
st.title("🏆 FIFA World Cup 2026 Poll")

# Require username before showing matches
username = st.text_input("Enter your Username to vote:")
if not username:
    st.info("Please enter a username above to see today's matches and cast your votes.")
    st.stop()

fixtures = load_fixture()
today = pd.Timestamp.today().normalize()

# Filter schedule for today's games
today_games = fixtures[fixtures["date_dt"].dt.normalize() == today]

if len(today_games) == 0:
    st.info("No matches scheduled for today. Check back tomorrow!")
    st.stop()

# Load all votes
votes = load_votes()

# Iterate through today's matches and create a polling section for each
for _, game in today_games.iterrows():
    match_id = str(game["match_number"])
    team1 = game["team 1"]
    team2 = game["team 2"]

    st.divider() # Visual separator
    st.subheader(f"⚽ {team1} vs {team2}")

    # Check if this user already voted on this specific match
    already = votes[
        (votes["username"] == username) &
        (votes["match_number"].astype(str) == match_id)
    ]

    if len(already) == 0:
        # Create unique keys for widgets using the match_id
        choice = st.radio(
            "Make your prediction:",
            [team1, team2, "Draw"],
            key=f"radio_{match_id}" 
        )

        if st.button("Vote", key=f"btn_{match_id}"):
            record = [
                str(uuid.uuid4()),
                match_id,
                username,
                choice,
                str(datetime.now())
            ]
            save_vote(record)
            st.success("Your vote has been saved!")
            st.rerun() # Refresh app to show updated poll chart
    else:
        # Show what they voted for
        user_choice = already.iloc[0]['prediction']
        st.info(f"✅ You voted for: **{user_choice}**")

    # Load live results for this match
    live_votes = load_votes()
    match_results = live_votes[live_votes["match_number"].astype(str) == match_id]

    if not match_results.empty:
        st.write("**Live Poll Results:**")
        chart_data = match_results["prediction"].value_counts()
        st.bar_chart(chart_data)
