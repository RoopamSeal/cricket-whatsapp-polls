# app.py

```python
import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import *

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="FIFA World Cup 2026 Match Poll",
    page_icon="⚽",
    layout="wide"
)

FIXTURE_FILE = "/Workspace/Shared/FIFA2026_schedule_fixtures.csv"

DATABASE = "fifa_poll_db"
TABLE = "match_votes"

# ============================================================
# SPARK SESSION
# ============================================================

spark = SparkSession.builder.getOrCreate()

spark.sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {DATABASE}.{TABLE}
(
vote_id STRING,
match_number STRING,
match_date STRING,
team_vote STRING,
user_session STRING,
vote_timestamp TIMESTAMP
)
USING DELTA
""")

# ============================================================
# LOAD FIXTURE
# ============================================================

@st.cache_data
def load_fixture():

    df = pd.read_csv(FIXTURE_FILE)

    df["date_dt"] = pd.to_datetime(
        df["date_dt"],
        format="%d-%m-%Y"
    )

    return df


fixture_df = load_fixture()

# ============================================================
# GET TODAY MATCHES
# ============================================================

today = pd.Timestamp.now().normalize()

today_matches = fixture_df[
    fixture_df["date_dt"] == today
]

# ============================================================
# SAVE VOTE
# ============================================================

def save_vote(
    match_number,
    match_date,
    selected_team,
    session_id
):

    existing = spark.sql(f"""
    SELECT *
    FROM {DATABASE}.{TABLE}
    WHERE user_session='{session_id}'
    AND match_number='{match_number}'
    """)

    if existing.count() > 0:
        return False

    vote = [
        (
            str(uuid.uuid4()),
            match_number,
            match_date,
            selected_team,
            session_id,
            datetime.now()
        )
    ]

    schema = StructType([
        StructField("vote_id",StringType()),
        StructField("match_number",StringType()),
        StructField("match_date",StringType()),
        StructField("team_vote",StringType()),
        StructField("user_session",StringType()),
        StructField("vote_timestamp",TimestampType())
    ])

    sdf = spark.createDataFrame(vote,schema)

    (
        sdf.write
        .format("delta")
        .mode("append")
        .saveAsTable(
            f"{DATABASE}.{TABLE}"
        )
    )

    return True


# ============================================================
# RESULTS
# ============================================================

def get_results(match_number):

    q = f"""
    SELECT
    team_vote,
    COUNT(*) votes
    FROM {DATABASE}.{TABLE}
    WHERE match_number='{match_number}'
    GROUP BY team_vote
    """

    return spark.sql(q).toPandas()


# ============================================================
# UI
# ============================================================

st.title("🏆 FIFA World Cup 2026 Daily Poll")

st.markdown(
"""
Vote only on match day.
Polls are generated automatically.
"""
)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(
        uuid.uuid4()
    )

session_id = st.session_state.session_id

if len(today_matches) == 0:

    st.success(
        "No FIFA World Cup matches today."
    )

else:

    st.subheader(
        f"Today's Matches ({len(today_matches)})"
    )

    for idx,row in today_matches.iterrows():

        match_id = row["match_number"]

        team1 = row["team 1"]
        team2 = row["team 2"]

        with st.container():

            st.markdown("---")

            st.header(
                f"{team1} vs {team2}"
            )

            st.caption(
                f"""
                Match:
                {match_id}

                Group:
                {row['group']}

                Stadium:
                {row['stadium']}
                """
            )

            poll = st.radio(
                "Who will win?",
                [
                    team1,
                    team2
                ],
                key=f"poll_{idx}"
            )

            if st.button(
                "Submit Vote",
                key=f"vote_{idx}"
            ):

                ok = save_vote(
                    match_id,
                    str(
                        row["date_dt"].date()
                    ),
                    poll,
                    session_id
                )

                if ok:
                    st.success(
                        "Vote stored."
                    )

                else:
                    st.warning(
                        "You already voted."
                    )

            st.markdown(
                "### Live Results"
            )

            results = get_results(
                match_id
            )

            if len(results):

                total = results[
                    "votes"
                ].sum()

                results[
                    "percent"
                ] = (
                    results["votes"]
                    / total
                    * 100
                )

                st.dataframe(
                    results
                )

                for _,r in results.iterrows():

                    st.progress(
                        int(
                            r["percent"]
                        )
                    )

                    st.write(
                        f"""
                        {r['team_vote']}
                        —
                        {r['percent']:.1f}%
                        """
                    )

            else:

                st.info(
                    "No votes yet."
                )

# ============================================================
# HISTORY
# ============================================================

st.markdown("---")

if st.checkbox(
    "Show Historical Votes"
):

    hist = spark.sql(
        f"""
        SELECT *
        FROM {DATABASE}.{TABLE}
        ORDER BY vote_timestamp DESC
        """
    ).toPandas()

    st.dataframe(hist)
```
