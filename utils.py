from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import logging
import time
from email_service import send_email

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Config
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "homezy_db"
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
            
            return client[DB_NAME]

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
    """
    db = get_db()
    if db:
        bookings_collection = db["bookings"]
        
        # ✅ Insert the booking into MongoDB
        try:
            result = bookings_collection.insert_one(booking_data)
            logger.info(f"✅ Booking stored in MongoDB with ID: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store booking in MongoDB: {e}")
            return False
    else:
        logger.error("❌ MongoDB connection not available.")
        return False


# ✅ Send Email Confirmation for Booking
def send_booking_confirmation_email(booking_data):
    """
    Send booking confirmation email.

    Args:
        booking_data (dict): Booking information.
    """
    # ✅ Extract necessary booking details
    email = booking_data.get("email")
    name = booking_data.get("name")
    phone = booking_data.get("phone")
    address = booking_data.get("address")
    
    services = booking_data.get("services", [])
    total_price = booking_data.get("total_price", "N/A")

    services_details = "\n".join([f"- {s['service_name']} ({s['provider_name']}): ₹{s['price']}" for s in services])

    # ✅ Email Subject and Body
    subject = "🔔 Booking Confirmation - Homezy"
    body = f"""
    Dear {name},

    Thank you for booking with Homezy! 🎉

    📌 **Booking Details:**
    - **Phone:** {phone}
    - **Address:** {address}

    🛠️ **Services Booked:**
    {services_details}

    💰 **Total Price:** ₹{total_price}

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
