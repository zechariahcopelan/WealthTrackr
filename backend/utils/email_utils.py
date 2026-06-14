# ~/Documents/WealthTrackr/backend/utils/email_utils.py

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)

print(f"🔍 EMAIL_USER loaded: {EMAIL_USER}")
print(f"🔍 EMAIL_PASSWORD loaded: {EMAIL_PASSWORD[:4]}****")  # Only show first 4 chars
print(f"🔍 SMTP_SERVER loaded: {SMTP_SERVER}")

def send_email(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
    """
    Sends an email with both HTML and plain text versions.
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

def send_verification_email(request: Request, email: str, username: str, token: str) -> bool:
    """
    Sends a verification email with a link containing a DB-backed token.
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    verification_url = f"{base_url}/auth/verify-email?token={token}"

    subject = "Verify Your WealthTrackr Account"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color:#f9f9f9;padding:20px;border-radius:8px;">
                <h2>Welcome to WealthTrackr, {username}!</h2>
                <p>Please click the button below to verify your email address:</p>
                <a href="{verification_url}" style="padding:10px 20px;background:#007bff;color:#fff;border-radius:5px;text-decoration:none;">Verify Email</a>
                <p>Or paste this link in your browser:</p>
                <p><a href="{verification_url}">{verification_url}</a></p>
                <p><small>This link expires in 1 hour. If you didn’t request this, ignore this message.</small></p>
            </div>
        </body>
    </html>
    """

    text_content = f"""
    Welcome to WealthTrackr, {username}!

    Click the link to verify your email address:
    {verification_url}

    This link expires in 1 hour. If you didn’t request this, ignore this message.
    """

    return send_email(email, subject, html_content, text_content)

def send_password_reset_email(request: Request, email: str, username: str, reset_token: str) -> bool:
    """
    Sends a password reset email with a secure link.
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    reset_url = f"{base_url}/auth/reset-password?token={reset_token}"

    subject = "Reset Your WealthTrackr Password"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color:#f9f9f9;padding:20px;border-radius:8px;">
                <h2>Hello {username},</h2>
                <p>You requested to reset your WealthTrackr password.</p>
                <a href="{reset_url}" style="padding:10px 20px;background:#dc3545;color:#fff;border-radius:5px;text-decoration:none;">Reset Password</a>
                <p>Or paste this link in your browser:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p><small>This link expires in 30 minutes. If you didn’t request this, ignore this message.</small></p>
            </div>
        </body>
    </html>
    """

    text_content = f"""
    Hello {username},

    You requested to reset your WealthTrackr password.

    Click the link to reset:
    {reset_url}

    This link expires in 30 minutes. If you didn’t request this, ignore this message.
    """

    return send_email(email, subject, html_content, text_content)

