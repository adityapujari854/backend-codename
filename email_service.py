import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import logging
import time

# ✅ Load environment variables
load_dotenv()

# ✅ Email Config
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RETRIES = 3
RETRY_DELAY = 5  # seconds

# ✅ Ensure environment variables are set
if not SMTP_SERVER or not SMTP_USERNAME or not SMTP_PASSWORD:
    raise ValueError("❌ SMTP configuration is missing in environment variables")

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(to_email, subject, message, is_html=False):
    """Send email with retries and error handling."""
    for attempt in range(RETRIES):
        try:
            # ✅ Set up the email
            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'html' if is_html else 'plain'))

            # ✅ Connect to the SMTP server
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_USERNAME, to_email, msg.as_string())

            logger.info(f"✅ Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPException as e:  # Only retry for SMTP-related errors
            logger.error(f"❌ SMTP Error: {e}. Attempt {attempt + 1} of {RETRIES}")
            time.sleep(RETRY_DELAY)

        except Exception as e:
            logger.error(f"❌ Unexpected Error: {e}")
            return False  # Don't retry for non-SMTP errors

    logger.error(f"❌ Failed to send email after {RETRIES} attempts")
    return False
