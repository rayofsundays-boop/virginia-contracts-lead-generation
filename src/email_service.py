"""
Email Service for VA Contracts Lead Generation Platform
Handles sending emails via Gmail SMTP with SSL/TLS encryption
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email(to, subject, html):
    """
    Send an HTML email using Gmail SMTP
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject line
        html (str): HTML content of the email
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    email_user = os.environ.get("EMAIL_USER")
    email_pass = os.environ.get("EMAIL_PASS")

    if not email_user or not email_pass:
        print("⚠️ Email credentials missing. Set EMAIL_USER and EMAIL_PASS environment variables.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_user
    msg["To"] = to

    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(email_user, email_pass)
            server.sendmail(email_user, to, msg.as_string())
        print(f"✅ Email sent successfully to {to}")
        return True
    except Exception as e:
        print(f"❌ ERROR sending email to {to}: {e}")
        return False
