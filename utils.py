from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import logging
import time
from email_service import send_email

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "homezy_db")
RETRIES = 3
RETRY_DELAY = 5  # seconds

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ MongoDB Connection with Retry Logic
def get_db():
    """Establish MongoDB connection with retry logic."""
    for attempt in range(RETRIES):
        try:
            logger.info(f"🔗 Connecting to MongoDB (Attempt {attempt + 1}/{RETRIES})...")
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

            # ✅ Check if the connection is successful
            client.server_info()  
            logger.info("✅ MongoDB connection established successfully")

            database = client[DB_NAME]

            if database is None:
                logger.error("❌ Database connection failed (None)")
                return None

            return database

        except errors.ServerSelectionTimeoutError as e:
            logger.error(f"❌ MongoDB connection timeout: {e}")
            time.sleep(RETRY_DELAY)

        except Exception as e:
            logger.error(f"❌ Unexpected MongoDB connection error: {e}")
            time.sleep(RETRY_DELAY)

    logger.error("❌ Failed to connect to MongoDB after retries")
    return None


# ✅ Store Booking in MongoDB
def store_booking_in_db(booking_data):
    """
    Store booking details in MongoDB.

    Args:
        booking_data (dict): Booking information.

    Returns:
        bool: True if booking stored successfully, False otherwise.
    """
    db = get_db()

    # ✅ Database Validation
    if db is None:
        logger.error("❌ Database connection is None")
        return False

    bookings_collection = db["bookings"] if db is not None else None

    if bookings_collection is None:
        logger.error("❌ Bookings collection is None")
        return False

    # ✅ Insert the booking into MongoDB
    try:
        result = bookings_collection.insert_one(booking_data)
        logger.info(f"✅ Booking stored in MongoDB with ID: {result.inserted_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to store booking in MongoDB: {e}")
        return False


# ✅ Send Email Confirmation for Booking
def send_booking_confirmation_email(booking_data):
    """
    Send booking confirmation email.

    Args:
        booking_data (dict): Booking information.

    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    # ✅ Extract necessary booking details
    email = booking_data.get("email")
    name = booking_data.get("name")
    phone = booking_data.get("phone")
    address = booking_data.get("address", {})
    services = booking_data.get("services", [])

    # ✅ Ensure fields exist and are consistent
    if not all([email, name, phone, address, services]):
        logger.error("❌ Missing booking details for email confirmation")
        return False

    # ✅ Format the address properly (flat, street, city, state - pincode)
    formatted_address = f"{address.get('flat', 'N/A')}, {address.get('street', 'N/A')}, {address.get('city', 'N/A')}, {address.get('state', 'N/A')} - {address.get('pincode', 'N/A')}"
    
    # ✅ Format service details correctly
    services_details = "\n".join([f"- {service.get('serviceName', 'N/A')} by {service.get('providerName', 'N/A')}" 
                                 for service in services])

    # ✅ Email Subject and Body (Improved Design with HTML)
    subject = "🔔 Booking Confirmation - Homezy"
    body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                margin: 0;
                padding: 0;
            }}
            .container {{
                width: 100%;
                max-width: 650px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }}
            .header {{
                text-align: center;
                background-color: #28a745;
                padding: 15px;
                border-radius: 8px;
                color: white;
            }}
            .header h2 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                margin: 25px 0;
                font-size: 16px;
            }}
            .address {{
                font-weight: bold;
                color: #333;
            }}
            .address p {{
                margin: 0;
            }}
            .services {{
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 6px;
                margin-top: 20px;
            }}
            .services ul {{
                list-style-type: none;
                padding-left: 0;
            }}
            .services li {{
                padding: 5px 0;
            }}
            .footer {{
                text-align: center;
                font-size: 14px;
                color: #888;
                margin-top: 30px;
            }}
            .button {{
                display: inline-block;
                background-color: #28a745;
                color: white;
                padding: 12px 20px;
                border-radius: 5px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin-top: 20px;
            }}
            .button:hover {{
                background-color: #218838;
            }}
        </style>
    </head>
    <body>

    <div class="container">
        <div class="header">
            <h2>🎉 Booking Confirmation</h2>
        </div>

        <div class="content">
            <p>Dear <strong>{name}</strong>,</p>
            <p>🎉 Thank you for booking with Homezy! Your booking has been successfully confirmed.</p>

            <p class="address">📌 <strong>Booking Details:</strong></p>
            <p><strong>Phone:</strong> {phone}</p>
            <p><strong>Address:</strong> {formatted_address}</p>

            <div class="services">
                <p><strong>🛠️ Services Booked:</strong></p>
                <ul>
                    {''.join([f'<li>{service["serviceName"]} by {service["providerName"]} - {service.get("remarks", "No remarks")}</li>' for service in services])}
                </ul>
            </div>

            <p>✅ Your booking is confirmed. We will reach out to you shortly with further details.</p>
            <a href="https://www.homezy.com" class="button">Visit Homezy</a>
        </div>

        <div class="footer">
            <p>Regards,</p>
            <p>The Homezy Team</p>
        </div>
    </div>

    </body>
    </html>
    """

    # ✅ Send the Email
    try:
        send_email(email, subject, body)
        logger.info(f"✅ Booking confirmation email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send booking confirmation email: {e}")
        return False


# ✅ Email Sending Function (Dummy Implementation)
def send_email(to: str, subject: str, message: str):
    """
    Simulates sending an email.

    Args:
        to (str): Recipient email address.
        subject (str): Email subject.
        message (str): Email body content (HTML).
    """
    logger.info(f"Simulating email sent to {to} with subject '{subject}'")
    # For actual implementation, connect to an email service provider
    # such as Sendinblue, Mailgun, etc.
