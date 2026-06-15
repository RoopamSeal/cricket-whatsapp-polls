import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid

# ==================================================

# CONFIG

# ==================================================

st.set_page_config(
page_title="FIFA World Cup 2026 Poll",
page_icon="⚽",
layout="wide"
)

FIXTURE_PATH = "data/FIFA2026_schedule_fixtures.csv"
VOTES_PATH = "data/votes.csv"

# ==================================================

# CREATE DATA DIRECTORY

# ==================================================

Path("data").mkdir(exist_ok=True)

if not Path(VOTES_PATH).exists():
empty_votes = pd.DataFrame(
columns=[
"vote_id",
"match_number",
"username",
"prediction",
"timestamp",
]
)

```
empty_votes.to_csv(
    VOTES_PATH,
    index=False
)
```

# ==================================================

# LOAD DATA

# ==================================================

@st.cache_data
def load_fixtures():

```
df = pd.read_csv(FIXTURE_PATH)

df["date_dt"] = pd.to_datetime(
    df["date_dt"],
    format="%d-%m-%Y",
    errors="coerce"
)

return df
```

def load_votes():

```
return pd.read_csv(VOTES_PATH)
```

def store_vote(vote):

```
existing = load_votes()

updated = pd.concat(
    [
        existing,
        pd.DataFrame([vote])
    ],
    ignore_index=True
)

updated.to_csv(
    VOTES_PATH,
    index=False
)
```

# ==================================================

# APP HEADER

# ==================================================

st.title("🏆 FIFA World Cup 2026 Match Poll")

username = st.text_input(
"Enter your username"
)

if username == "":
st.stop()

# ==================================================

# DATE FILTER

# ==================================================

fixtures = load_fixtures()

today = pd.Timestamp.now().normalize()

matches = fixtures[
fixtures["date_dt"].dt.normalize()
== today
]

# ==================================================

# NO MATCH

# ==================================================

if matches.empty:

```
st.info(
    "No FIFA World Cup match today."
)

upcoming = (
    fixtures[
        fixtures["date_dt"]
        > today
    ]
    .sort_values("date_dt")
    .head(10)
)

st.subheader(
    "Upcoming Fixtures"
)

st.dataframe(
    upcoming
)

st.stop()
```

# ==================================================

# ACTIVE MATCHES

# ==================================================

votes = load_votes()

for _, match in matches.iterrows():

```
match_id = str(
    match["match_number"]
)

team1 = str(
    match["team 1"]
)

team2 = str(
    match["team 2"]
)

st.divider()

st.subheader(
    f"{team1} vs {team2}"
)

st.write(
    f"🏟 {match['stadium']}"
)

previous = votes[
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

if previous.empty:

    prediction = st.radio(
        "Who will win?",
        [
            team1,
            team2,
            "Draw"
        ],
        key=match_id
    )

    submit = st.button(
        "Submit Vote",
        key=f"btn_{match_id}"
    )

    if submit:

        new_vote = {

            "vote_id":
            str(
                uuid.uuid4()
            ),

            "match_number":
            match_id,

            "username":
            username,

            "prediction":
            prediction,

            "timestamp":
            datetime.utcnow()
        }

        store_vote(
            new_vote
        )

        st.success(
            "Vote stored."
        )

        st.rerun()

else:

    st.warning(
        "You already voted."
    )

# RESULTS

results = load_votes()

results = results[
    results[
        "match_number"
    ].astype(str)
    == match_id
]

if not results.empty:

    st.subheader(
        "Live Results"
    )

    summary = (
        results[
            "prediction"
        ]
        .value_counts()
        .reset_index()
    )

    summary.columns = [
        "Selection",
        "Votes"
    ]

    st.dataframe(
        summary,
        use_container_width=True
    )

    st.bar_chart(
        summary.set_index(
            "Selection"
        )
    )
```

# ==================================================

# HISTORY

# ==================================================

st.divider()

st.subheader(
"Recent Votes"
)

history = load_votes()

if history.empty:

```
st.info(
    "No votes recorded."
)
```

else:

```
st.dataframe(
    history.tail(20),
    use_container_width=True
)
```
