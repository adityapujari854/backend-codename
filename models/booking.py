from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr, Field, ValidationError
from pymongo.collection import Collection
from database import bookings_collection
from middlewares.middleware import get_current_user
from email_service import send_email
import logging

# ✅ Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Initialize Router
bookings_router = APIRouter()

# ✅ Booking Model with Validation
class Booking(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15, regex=r'^\d+$')
    address: str = Field(..., min_length=5, max_length=200)
    serviceName: str = Field(..., min_length=2, max_length=100)
    providerName: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., gt=0)  # Accepts both `int` and `float`
    remarks: str = Field(..., min_length=0, max_length=300)

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
            logger.warning("Unauthorized booking attempt by %s", user_email)
            raise HTTPException(status_code=403, detail="Unauthorized booking request")

        # ✅ Validate the booking data
        if not booking.price or booking.price <= 0:
            raise HTTPException(status_code=422, detail="Invalid price value")

        # ✅ Insert booking into MongoDB
        collection.insert_one(booking.dict())

        # ✅ Send Confirmation Email
        try:
            send_email(
                recipient_email=booking.email,
                subject="Booking Confirmed - Homezy",
                message=f"Your booking for {booking.serviceName} with {booking.providerName} has been confirmed. Total: ₹{booking.price}"
            )
            logger.info("✅ Email sent successfully to %s", booking.email)

        except Exception as e:
            logger.error("❌ Error sending email: %s", str(e))
            raise HTTPException(status_code=500, detail="Email sending failed")

        return {"message": "✅ Booking confirmed & email sent!"}

    except ValidationError as e:
        logger.error("❌ Validation Error: %s", str(e))
        raise HTTPException(status_code=422, detail="Invalid booking data")

    except Exception as e:
        logger.error("❌ Unexpected Error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
