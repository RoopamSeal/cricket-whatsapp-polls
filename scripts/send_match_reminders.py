"""
send_match_reminders.py

FIFA World Cup 2026 Prediction Platform
Automatic pre-match email reminders — runs every hour via GitHub Actions.

Sends reminders to users who haven't predicted yet for matches
kicking off within the next REMINDER_MINUTES minutes.

NOTE: kickoff_time in the DB is treated as UTC. If your fixtures store
kickoff in a local timezone, adjust KICKOFF_TZ_OFFSET_HOURS accordingly.
"""

import os
import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


# ==========================================================
# CONFIG
# ==========================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

EMAIL_USER     = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FROM_EMAIL     = os.getenv("FROM_EMAIL")

# Send reminders for matches kicking off within the next 60 minutes
REMINDER_MINUTES = 60

# If kickoff_time in DB is in a local timezone, set the UTC offset here.
# e.g. EDT = -4, IST = +5.5, UTC = 0
KICKOFF_TZ_OFFSET_HOURS = 0


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
    """Return scheduled matches kicking off within the reminder window."""
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    window_end = now_utc + timedelta(minutes=REMINDER_MINUTES)

    # Shift by the stored timezone offset so comparison is in UTC
    offset = timedelta(hours=KICKOFF_TZ_OFFSET_HOURS)

    query = """
    SELECT
        match_id,
        team_1,
        team_2,
        match_date,
        kickoff_time,
        venue
    FROM matches
    WHERE status = 'scheduled'
      AND (match_date::date + kickoff_time::time) - %s::interval > %s
      AND (match_date::date + kickoff_time::time) - %s::interval <= %s
    """

    with conn.cursor() as cur:
        offset_str = f"{abs(int(KICKOFF_TZ_OFFSET_HOURS))} hours"
        # Subtract offset to convert stored local time → UTC before comparing
        cur.execute(query, (offset_str, now_utc, offset_str, window_end))
        return cur.fetchall()


# ==========================================================
# USERS TO NOTIFY
# ==========================================================

def users_without_prediction(conn, match_id):
    """Return active users who have not yet predicted for this match."""
    query = """
    SELECT
        u.user_id,
        u.user_name,
        u.email
    FROM users u
    WHERE u.email IS NOT NULL
      AND u.email != ''
      AND NOT EXISTS (
          SELECT 1
          FROM predictions p
          WHERE p.user_id = u.user_id
            AND p.match_id = %s
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

    msg = MIMEMultipart()
    msg["From"]    = FROM_EMAIL
    msg["To"]      = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
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
