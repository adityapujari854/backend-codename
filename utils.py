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

    # ✅ Format address with better structure (split by commas and strip extra spaces)
    if isinstance(address, dict):
        # If the address is a dictionary, format it as a string
        formatted_address = "\n".join([f"{key.capitalize()}: {value}" for key, value in address.items()])
    else:
        # If the address is already a string, use it as-is
        formatted_address = address

    # ✅ Generate HTML Email Content for Booking Confirmation
    booking_email_content = get_booking_confirmation_email_template(booking_data)

    # ✅ Send the Email
    try:
        send_email(email, "🔔 Booking Confirmation - Homezy", booking_email_content, is_html=True)
        logger.info(f"✅ Booking confirmation email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send booking confirmation email: {e}")
        return False


# ✅ OTP Email Template
def get_otp_email_template(otp_code):
    """
    Generate a HTML template for OTP email.

    Args:
        otp_code (str): The OTP code to be included in the email.

    Returns:
        str: HTML formatted string for email body
    """
    otp_email_template = f"""
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
            .otp {{
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
                text-align: center;
                margin-top: 20px;
            }}
            .footer {{
                font-size: 12px;
                color: #888;
                margin-top: 20px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Your OTP Code</h1>
            <p>Dear User,</p>
            <p>🎉 **Here is your OTP code for verification:**</p>
            <div class="otp">{otp_code}</div>
            <p>Use the OTP to complete your verification process.</p>
            <div class="footer">
                <p>Regards,</p>
                <p>The Homezy Team</p>
            </div>
        </div>
    </body>
    </html>
    """
    return otp_email_template


# ✅ Booking Confirmation Email Template
def get_booking_confirmation_email_template(booking_data):
    """
    Generate a HTML template for booking confirmation email.

    Args:
        booking_data (dict): The booking information.

    Returns:
        str: HTML formatted string for email body
    """
    name = booking_data.get("name", "User")
    phone = booking_data.get("phone", "N/A")
    address = booking_data.get("address", "N/A")
    services = booking_data.get("services", [])
    
    services_details = "".join([
        f"<li>{service.get('serviceName', 'N/A')} by {service.get('providerName', 'N/A')}</li>"
        for service in services
    ])
    
    if isinstance(address, dict):
        formatted_address = "<br>".join([f"{key.capitalize()}: {value}" for key, value in address.items()])
    else:
        formatted_address = address

    booking_email_template = f"""
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
                font-size: 16px;
                color: #333;
                line-height: 1.6;
            }}
            .footer {{
                font-size: 12px;
                color: #888;
                margin-top: 20px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Booking Confirmation</h1>
            <p>Dear {name},</p>
            <p>🎉 **Thank you for booking with Homezy!**</p>
            <p class="details">
                <b>Phone:</b> {phone}<br>
                <b>Address:</b><br>{formatted_address}<br><br>
                <b>Services Booked:</b><br>
                <ul>{services_details}</ul>
            </p>
            <p>✅ **Your booking is confirmed.** We'll reach out shortly with further details.</p>
            <div class="footer">
                <p>Regards,</p>
                <p>The Homezy Team</p>
            </div>
        </div>
    </body>
    </html>
    """
    return booking_email_template
