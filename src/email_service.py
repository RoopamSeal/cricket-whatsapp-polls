import os
import smtplib
import psycopg2
import logging

from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailService:

    def __init__(self):

        self.conn = psycopg2.connect(
            os.getenv("DATABASE_URL")
        )

        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = 587
        self.user = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.sender = os.getenv("FROM_EMAIL")

    def get_users(self):

        cur = self.conn.cursor()

        cur.execute("""
            SELECT
                user_id,
                user_name,
                email
            FROM user_master
            WHERE status='ACTIVE'
        """)

        rows = cur.fetchall()

        return rows

    def already_sent_today(
        self,
        user_id,
        reminder_type
    ):

        cur = self.conn.cursor()

        cur.execute("""
        SELECT 1
        FROM email_log

        WHERE user_id=%s
        AND reminder_type=%s
        AND DATE(sent_at)=CURRENT_DATE
        """, (
            user_id,
            reminder_type
        ))

        return cur.fetchone() is not None

    def record_send(
        self,
        user_id,
        reminder_type
    ):

        cur = self.conn.cursor()

        cur.execute("""
        INSERT INTO email_log(
            user_id,
            reminder_type
        )
        VALUES(%s,%s)
        """, (
            user_id,
            reminder_type
        ))

        self.conn.commit()

    def send_email(
        self,
        email,
        username,
        subject,
        body
    ):

        try:

            msg = MIMEMultipart()

            msg["From"] = self.sender
            msg["To"] = email
            msg["Subject"] = subject

            msg.attach(
                MIMEText(
                    body,
                    "plain"
                )
            )

            with smtplib.SMTP(
                self.smtp_host,
                self.smtp_port
            ) as server:

                server.starttls()

                server.login(
                    self.user,
                    self.password
                )

                server.send_message(msg)

            return True

        except Exception as e:

            logger.exception(e)

            return False

    def send_daily_reminders(self):

        users = self.get_users()

        sent = 0

        for user in users:

            uid, name, email = user

            if self.already_sent_today(
                uid,
                "DAILY"
            ):
                continue

            ok = self.send_email(
                email,
                name,
                "⚽ FIFA World Cup Daily Reminder",
                f"""
Hello {name},

Your predictions may still be open.

Visit the platform and submit today's picks.

Good luck.
"""
            )

            if ok:

                self.record_send(
                    uid,
                    "DAILY"
                )

                sent += 1

        return sent

    def send_admin_blast(self):

        users = self.get_users()

        sent = 0

        for user in users:

            uid, name, email = user

            ok = self.send_email(
                email,
                name,
                "🚨 Extra Reminder from Admin",
                f"""
Hello {name},

Admin has opened an additional reminder.

Don't forget to make today's prediction.

Good luck.
"""
            )

            if ok:

                self.record_send(
                    uid,
                    "ADMIN"
                )

                sent += 1

        return sent
