import os
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "your-email@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "your-app-password")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def send_verification_email(email: str, token: str):
    link = f"{FRONTEND_URL}/verify-email?token={token}"
    body = f"""
    Hi there,

    Please verify your email by clicking the link below:
    {link}

    If you didn’t create an account, you can ignore this message.
    """

    msg = MIMEText(body)
    msg["Subject"] = "Verify Your Email - WealthTrackr"
    msg["From"] = SMTP_USER
    msg["To"] = email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"Verification email sent to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}: {str(e)}")

