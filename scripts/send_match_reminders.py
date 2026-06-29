"""
send_match_reminders.py

FIFA World Cup 2026 Prediction Platform
Automatic pre-match email reminders — runs every hour via GitHub Actions.

Sends reminders to users who haven't predicted yet for matches
kicking off within the next REMINDER_MINUTES minutes.
"""

import os
import logging
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import resend


# ==========================================================
# CONFIG
# ==========================================================

load_dotenv()

DATABASE_URL  = os.getenv("DATABASE_URL")
FROM_EMAIL    = os.getenv("FROM_EMAIL")
resend.api_key = os.getenv("RESEND_API_KEY")

REMINDER_MINUTES = 60
IST = timezone(timedelta(hours=5, minutes=30))


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("email-reminder")


# ==========================================================
# DB
# ==========================================================

def get_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor,
    )


# ==========================================================
# MATCH QUERY
# ==========================================================

def get_upcoming_matches(conn):
    now_ist    = datetime.now(IST).replace(tzinfo=None)
    window_end = now_ist + timedelta(minutes=REMINDER_MINUTES)

    logger.info("IST now: %s | Window end: %s", now_ist.strftime("%Y-%m-%d %H:%M:%S"), window_end.strftime("%Y-%m-%d %H:%M:%S"))

    # kickoff_time stored in EDT (UTC-4); adding 9h30m converts to IST
    query = """
    SELECT match_id, team_1, team_2, match_date, kickoff_time, kickoff_time_ist, venue
    FROM matches
    WHERE status = 'scheduled'
      AND (match_date::date + kickoff_time::time) + interval '9 hours 30 minutes' > %s
      AND (match_date::date + kickoff_time::time) + interval '9 hours 30 minutes' <= %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (now_ist, window_end))
        return cur.fetchall()


# ==========================================================
# USERS TO NOTIFY
# ==========================================================

def users_without_prediction(conn, match_id):
    query = """
    SELECT u.user_id, u.user_name, u.email
    FROM users u
    WHERE u.email IS NOT NULL
      AND u.email != ''
      AND NOT EXISTS (
          SELECT 1 FROM predictions p
          WHERE p.user_id = u.user_id AND p.match_id = %s
      )
    """
    with conn.cursor() as cur:
        cur.execute(query, (match_id,))
        return cur.fetchall()


# ==========================================================
# EMAIL
# ==========================================================

def send_email(recipient, username, team1, team2, kickoff, venue):
    subject = f"⚽ Predict before kickoff: {team1} vs {team2}"

    body = f"""Hello {username},

Your FIFA World Cup 2026 prediction window is closing soon!

Match:   {team1} vs {team2}
Kickoff: {kickoff}
Venue:   {venue or 'TBD'}

Open the app and submit your prediction before kickoff — you have less than an hour!

Good luck,
FIFA World Cup 2026 Predictor
"""

    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": recipient,
            "subject": subject,
            "text": body,
        })
        logger.info("Email sent → %s", recipient)
        return True
    except Exception:
        logger.exception("Email failed → %s", recipient)
        return False


# ==========================================================
# MAIN JOB
# ==========================================================

def run():
    logger.info("Starting reminder job (window: %d min)", REMINDER_MINUTES)

    conn = get_connection()
    try:
        matches = get_upcoming_matches(conn)

        if not matches:
            logger.info("No matches kicking off in the next %d minutes", REMINDER_MINUTES)
            return

        for match in matches:
            match_id = match["match_id"]
            team1    = match["team_1"]
            team2    = match["team_2"]
            kickoff  = f"{match['match_date']} {match['kickoff_time']}"
            venue    = match.get("venue", "")

            users = users_without_prediction(conn, match_id)
            logger.info("Match %s (%s vs %s): %d user(s) to notify", match_id, team1, team2, len(users))

            sent = 0
            for user in users:
                if send_email(user["email"], user["user_name"], team1, team2, kickoff, venue):
                    sent += 1

            logger.info("Sent %d/%d reminders for match %s", sent, len(users), match_id)

    finally:
        conn.close()

    logger.info("Reminder job complete")


if __name__ == "__main__":
    run()
