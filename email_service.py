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
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
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
            # ✅ Set up the email message
            msg = MIMEMultipart()
            msg['From'] = BREVO_SENDER_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject

            # Attach the message body (HTML or plain text)
            msg.attach(MIMEText(message, 'html' if is_html else 'plain'))

            # ✅ Connect to the SMTP server
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()  # Start TLS encryption
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(BREVO_SENDER_EMAIL, to_email, msg.as_string())

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


def get_booking_confirmation_email_template(booking_data):
    """
    Generate a HTML template for booking confirmation email.
    
    Args:
        booking_data (dict): Contains information about the booking (name, email, services, etc.)
    
    Returns:
        str: HTML formatted string for email body
    """
    # ✅ Extract necessary booking details
    email = booking_data.get("email")
    name = booking_data.get("name")
    phone = booking_data.get("phone")
    address = booking_data.get("address")
    services = booking_data.get("services", [])

    # ✅ Ensure fields exist and are consistent
    if not all([email, name, phone, address, services]):
        raise ValueError("❌ Missing essential booking details")

    # ✅ Format service details correctly
    services_details = "\n".join([ 
        f"- {service.get('serviceName', 'N/A')} by {service.get('providerName', 'N/A')}" 
        for service in services
    ])

    # ✅ Format address with better structure (split by commas and strip extra spaces)
    if isinstance(address, dict):
        # If the address is a dictionary, format it as a string
        formatted_address = "\n".join([f"{key.capitalize()}: {value}" for key, value in address.items()])
    else:
        # If the address is already a string, use it as-is
        formatted_address = address

    # ✅ HTML Template for the Email Body
    email_template = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #4CAF50;
                text-align: center;
            }}
            .details {{
                margin-bottom: 20px;
            }}
            .service {{
                margin-bottom: 10px;
            }}
            .footer {{
                font-size: 12px;
                color: #888;
                margin-top: 20px;
                text-align: center;
            }}
            .cta {{
                display: block;
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 20px;
                text-align: center;
            }}
            .cta:hover {{
                background-color: #45a049;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Booking Confirmation - Homezy</h1>
            <p>Dear {name},</p>
            <p>🎉 **Thank you for booking with Homezy!**</p>

            <div class="details">
                <h3>Booking Details:</h3>
                <p><strong>Phone:</strong> {phone}</p>
                <p><strong>Address:</strong><br>{formatted_address}</p>
            </div>

            <div class="services">
                <h3>Services Booked:</h3>
                <ul>
                    {''.join([f'<li class="service">- {service.get("serviceName", "N/A")} by {service.get("providerName", "N/A")}</li>' for service in services])}
                </ul>
            </div>

            <p>✅ Your booking is confirmed. We will reach out shortly with further details.</p>

            <a href="https://homezy.com/my-bookings" class="cta">View My Bookings</a>

            <div class="footer">
                <p>Regards,</p>
                <p>The Homezy Team</p>
            </div>
        </div>
    </body>
    </html>
    """

    return email_template
