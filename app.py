import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid

# ----------------------------------

# CONFIG

# ----------------------------------

st.set_page_config(
page_title="FIFA 2026 Poll",
page_icon="⚽",
layout="wide"
)

DATA_DIR = Path("data")
FIXTURE_FILE = DATA_DIR / "FIFA2026_schedule_fixtures.csv"
VOTES_FILE = DATA_DIR / "votes.csv"

# ----------------------------------

# CREATE DATA STORAGE

# ----------------------------------

DATA_DIR.mkdir(exist_ok=True)

if not VOTES_FILE.exists():
pd.DataFrame(
columns=[
    "vote_id",
    "match_number",
    "username",
    "prediction",
    "timestamp"
]
).to_csv(
VOTES_FILE,
index=False
)

# ----------------------------------

# HELPERS

# ----------------------------------

@st.cache_data
def load_fixtures():

```
df = pd.read_csv(FIXTURE_FILE)

df["date_dt"] = pd.to_datetime(
    df["date_dt"],
    format="%d-%m-%Y",
    errors="coerce"
)

return df
```

def load_votes():

```
if VOTES_FILE.exists():
    return pd.read_csv(VOTES_FILE)

return pd.DataFrame()
```

def save_vote(record):

```
votes = load_votes()

votes = pd.concat(
    [
        votes,
        pd.DataFrame([record])
    ],
    ignore_index=True
)

votes.to_csv(
    VOTES_FILE,
    index=False
)
```

# ----------------------------------

# UI

# ----------------------------------

st.title("🏆 FIFA World Cup 2026 Daily Poll")

username = st.text_input(
"Username"
)

if not username:
st.stop()

fixtures = load_fixtures()

today = pd.Timestamp.today().normalize()

today_matches = fixtures[
fixtures["date_dt"].dt.normalize()
== today
]

# ----------------------------------

# NO MATCH

# ----------------------------------

if len(today_matches) == 0:

```
st.info(
    "No match scheduled today."
)

st.stop()
```

# ----------------------------------

# SHOW POLLS

# ----------------------------------

votes = load_votes()

for _, match in today_matches.iterrows():

```
match_id = str(
    match["match_number"]
)

team1 = match["team 1"]
team2 = match["team 2"]

st.divider()

st.subheader(
    f"{team1} vs {team2}"
)

st.write(
    f"🏟️ {match['stadium']}"
)

already = votes[
    (
        votes["username"]
        == username
    )
    &
    (
        votes[
            "match_number"
        ].astype(str)
        == match_id
    )
]

if len(already) == 0:

    choice = st.radio(
        "Choose winner",
        [
            team1,
            team2,
            "Draw"
        ],
        key=match_id
    )

    if st.button(
        "Submit Vote",
        key=f"submit_{match_id}"
    ):

        save_vote({

            "vote_id":
            str(uuid.uuid4()),

            "match_number":
            match_id,

            "username":
            username,

            "prediction":
            choice,

            "timestamp":
            datetime.now()
        })

        st.success(
            "Vote submitted"
        )

        st.rerun()

else:

    st.warning(
        "Already voted"
    )

results = load_votes()

results = results[
    results[
        "match_number"
    ].astype(str)
    == match_id
]

if len(results):

    summary = (
        results[
            "prediction"
        ]
        .value_counts()
    )

    st.bar_chart(
        summary
    )

    st.dataframe(
        summary
    )
```
