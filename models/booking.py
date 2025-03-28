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
    price: float = Field(..., gt=0)  # Accepts both `int` and `float`
    remarks: Optional[str] = Field(default="", max_length=300)  # Optional remarks

# ✅ Booking Model (Updated to Support Multiple Services)
class Booking(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15, pattern=r'^\d+$')
    address: str = Field(..., min_length=5, max_length=200)
    services: List[ServiceItem]  # ✅ Multiple services per booking
    total_price: float = Field(..., gt=0)  # Sum of all service prices

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
    try:
        # ✅ Authenticate User
        user_email = get_current_user(authorization)

        # ✅ Ensure user is booking for themselves
        if user_email != booking.email:
            logger.warning("❌ Unauthorized booking attempt by %s", user_email)
            raise HTTPException(status_code=403, detail="Unauthorized booking request")

        # ✅ Validate service data
        if not booking.services or len(booking.services) == 0:
            logger.error("❌ No services provided in the booking request")
            raise HTTPException(status_code=422, detail="Missing or invalid field: services")

        for service in booking.services:
            if not service.serviceName or not service.providerName:
                logger.error("❌ Missing service details: %s", service.dict())
                raise HTTPException(status_code=422, detail="Missing or invalid service details")

        # ✅ Calculate total price
        calculated_total = sum(service.price for service in booking.services)
        if calculated_total != booking.total_price:
            logger.warning("⚠️ Mismatch in total price calculation: Expected %s, Got %s", calculated_total, booking.total_price)
            raise HTTPException(status_code=422, detail="Total price mismatch")

        # ✅ Insert booking into MongoDB
        try:
            booking_dict = booking.dict()
            collection.insert_one(booking_dict)
            logger.info("✅ Booking saved successfully in DB for %s", booking.email)
        except Exception as db_error:
            logger.error("❌ Database Insertion Failed: %s", str(db_error))
            raise HTTPException(status_code=500, detail="Database error: Could not save booking")

        # ✅ Send Confirmation Email
        try:
            service_details = "\n".join(
                [f"- {s.serviceName} with {s.providerName}: ₹{s.price}" for s in booking.services]
            )
            send_email(
                recipient_email=booking.email,
                subject="Booking Confirmed - Homezy",
                message=f"Your booking has been confirmed!\n\nDetails:\n{service_details}\nTotal: ₹{booking.total_price}"
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
