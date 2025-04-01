from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr, Field, ValidationError
from pymongo.collection import Collection
from database import bookings_collection
from middlewares.middleware import get_current_user
from email_service import send_email
import logging
from typing import List, Optional
import requests
import os

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# ✅ Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Initialize Router
bookings_router = APIRouter()

# ✅ Service Model
class ServiceItem(BaseModel):
    serviceName: str = Field(..., min_length=2, max_length=100)
    providerName: str = Field(..., min_length=2, max_length=100)
    remarks: Optional[str] = Field(default="", max_length=300)

# ✅ Updated Address Model with city, state, and pincode
class Address(BaseModel):
    flat: str = Field(..., min_length=2, max_length=100)
    street: str = Field(..., min_length=2, max_length=100)      # ✅ Changed from road to street
    landmark: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=4, max_length=10, pattern=r'^\d+$')

# ✅ Booking Model
class Booking(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15, pattern=r'^\d+$')
    address: Address
    services: List[ServiceItem]
    
class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    message: str    

# ✅ Dependency to get MongoDB Collection
def get_bookings_collection() -> Collection:
    return bookings_collection

# ✅ Create Booking API (Requires Authentication)
@bookings_router.post("/", summary="Create a new booking")
async def create_booking(
    booking: Booking,
    authorization: str = Header(None),
    collection: Collection = Depends(get_bookings_collection)
):
    """
    Save a new booking and send confirmation email with sender details.

    Args:
        booking (Booking): Incoming booking data.
        authorization (str): JWT token for authentication.
        collection (Collection): MongoDB collection dependency.

    Returns:
        dict: Confirmation message.
    """
    try:
        # ✅ Authenticate User
        user_email = get_current_user(authorization)

        # ✅ Ensure user is booking for themselves
        if user_email != booking.email:
            logger.warning("❌ Unauthorized booking attempt by %s", user_email)
            raise HTTPException(status_code=403, detail="Unauthorized booking request")

        # ✅ Validate service data
        if not booking.services:
            logger.error("❌ No services provided in the booking request")
            raise HTTPException(status_code=422, detail="Missing or invalid field: services")

        for service in booking.services:
            if not service.serviceName or not service.providerName:
                logger.error("❌ Missing service details: %s", service.dict())
                raise HTTPException(status_code=422, detail="Missing or invalid service details")

        # ✅ Insert booking into MongoDB
        if collection is not None:
            try:
                booking_dict = booking.dict()
                collection.insert_one(booking_dict)
                logger.info("✅ Booking saved successfully in DB for %s", booking.email)
            except Exception as db_error:
                logger.error("❌ Database Insertion Failed: %s", str(db_error))
                raise HTTPException(status_code=500, detail="Database error: Could not save booking")
        else:
            logger.error("❌ MongoDB collection is None")
            raise HTTPException(status_code=500, detail="Database connection error")

        # ✅ Send Confirmation Email with Proper Sender Details
        try:
            # ✅ Format Service Details
            services_list = "\n".join(
                [f"- {s.serviceName} by {s.providerName}" for s in booking.services]
            )

            # ✅ Format Address Properly with Line Breaks
            address = (
                f"- Flat: {booking.address.flat}\n"
                f"- Street: {booking.address.street}\n"  # ✅ Changed to street
                f"- Landmark: {booking.address.landmark}\n"
                f"- City: {booking.address.city}\n"
                f"- State: {booking.address.state}\n"
                f"- Pincode: {booking.address.pincode}"
            )

            # ✅ Email Content (Formatted HTML Email)
            email_message = f"""
            <html>
            <head>
            <style>
                body {{
                font-family: Arial, sans-serif;
                color: #333;
                background-color: #f9f9f9;
                margin: 0;
                padding: 0;
                }}
                .container {{
                width: 100%;
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
                padding: 20px;
                }}
                .header {{
                text-align: center;
                background-color: #28a745;
                padding: 15px;
                border-radius: 10px 10px 0 0;
                color: white;
                }}
                .header h2 {{
                margin: 0;
                }}
                .content {{
                margin: 20px 0;
                font-size: 16px;
                }}
                .content p {{
                line-height: 1.5;
                }}
                .content .address {{
                font-weight: bold;
                }}
                .services {{
                margin-top: 20px;
                padding: 10px;
                background-color: #f1f1f1;
                border-radius: 5px;
                }}
                .footer {{
                text-align: center;
                font-size: 14px;
                color: #888;
                margin-top: 30px;
                }}
                .button {{
                background-color: #28a745;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 5px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                margin: 20px 0;
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
                <p>Dear <strong>{booking.name}</strong>,</p>
                <p>Thank you for booking with Homezy! Your booking has been confirmed.</p>
                <p class="address">📌 <strong>Booking Details:</strong></p>
                <p><strong>Phone:</strong> {booking.phone}</p>
                <p><strong>Address:</strong> {booking.address.flat}, {booking.address.street}, {booking.address.landmark}, {booking.address.city}, {booking.address.state} - {booking.address.pincode}</p>
                
                <div class="services">
                    <p><strong>🛠 Services Booked:</strong></p>
                    <ul>
                    {''.join([f'<li>{service.serviceName} by {service.providerName} - {service.remarks or "No remarks"}</li>' for service in booking.services])}
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

            # ✅ Send the email with proper parameters
            def send_email(to: str, subject: str, message: str):
                email_data = {
                    "sender": {"name": "Homezy Services", "email": "no-reply@homezy.com"},
                    "to": [{"email": to}],
                    "subject": subject,
                    "htmlContent": message
                }
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "api-key": BREVO_API_KEY
                }
                response = requests.post("https://api.brevo.com/v3/smtp/email", json=email_data, headers=headers)
                
                if response.status_code != 201:
                    raise HTTPException(status_code=500, detail="Failed to send email")

            logger.info("✅ Email sent successfully to %s", booking.email)
            return {"message": "✅ Booking confirmed & email sent!"}


        except Exception as e:
            logger.error("⚠️ Email Sending Failed: %s", str(e))
            return {"message": "✅ Booking confirmed, but email failed to send"}

    except ValidationError as e:
        logger.error("❌ Validation Error: %s", str(e))
        raise HTTPException(status_code=422, detail="Invalid booking data")

    except Exception as e:
        logger.error("❌ Unexpected Error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
