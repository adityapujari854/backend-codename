from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr, Field, ValidationError
from pymongo.collection import Collection
from database import bookings_collection
from middlewares.middleware import get_current_user
from email_service import send_email
import logging
from typing import List, Optional

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

# ✅ Address Model
class Address(BaseModel):
    flat: str = Field(..., min_length=2, max_length=100)
    road: str = Field(..., min_length=2, max_length=100)
    landmark: str = Field(..., min_length=2, max_length=100)

# ✅ Booking Model
class Booking(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15, pattern=r'^\d+$')
    address: Address
    services: List[ServiceItem]

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
                f"- Road: {booking.address.road}\n"
                f"- Landmark: {booking.address.landmark}"
            )

            # ✅ Email Content
            email_message = (
                f"Dear {booking.name},\n\n"
                "🎉 Thank you for booking with Homezy!\n\n"
                "📌 *Booking Details:*\n"
                f"- Phone: {booking.phone}\n"
                f"{address}\n\n"
                "🛠 *Services Booked:*\n"
                f"{services_list}\n\n"
                "✅ Your booking is confirmed. We'll reach out shortly with further details.\n\n"
                "Regards,\n"
                "The Homezy Team"
            )

            # ✅ Send the email with proper parameters
            send_email(
                to=booking.email,               # ✅ Corrected parameter
                subject="Booking Confirmed - Homezy",
                message=email_message
            )

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
