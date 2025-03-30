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
    address = booking_data.get("address")
    services = booking_data.get("services", [])

    # ✅ Ensure fields exist and are consistent
    if not all([email, name, phone, address, services]):
        logger.error("❌ Missing booking details for email confirmation")
        return False

    # ✅ Format service details correctly
    services_details = "\n".join([
        f"- {service.get('serviceName', 'N/A')} by {service.get('providerName', 'N/A')}" 
        for service in services
    ])

    # ✅ Email Subject and Body
    subject = "🔔 Booking Confirmation - Homezy"
    body = f"""
    Dear {name},

    🎉 Thank you for booking with Homezy!

    📌 **Booking Details:**
    - Phone: {phone}
    - Address: {address}

    🛠️ **Services Booked:**
    {services_details}

    ✅ Your booking is confirmed. We'll reach out shortly with further details.

    Regards,  
    The Homezy Team
    """

    # ✅ Send the Email
    try:
        send_email(email, subject, body)
        logger.info(f"✅ Booking confirmation email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send booking confirmation email: {e}")
        return False
