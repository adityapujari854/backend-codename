from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from database import bookings_collection
from middlewares.middleware import get_current_user
from email_service import send_email

router = APIRouter()

# ✅ Booking Model
class Booking(BaseModel):
    email: EmailStr
    name: str
    phone: str
    address: str
    serviceName: str
    providerName: str
    price: int
    remarks: str  

# ✅ Create Booking API (Requires Authentication)
@router.post("/bookings")
def create_booking(booking: Booking, authorization: str = Header(None)):
    user_email = get_current_user(authorization)

    if user_email != booking.email:
        raise HTTPException(status_code=403, detail="Unauthorized booking request")

    bookings_collection.insert_one(booking.dict())

    # ✅ Send Confirmation Email
    send_email(
        booking.email,
        "Booking Confirmed - Homezy",
        f"Your booking for {booking.serviceName} with {booking.providerName} has been confirmed. Total: ₹{booking.price}"
    )

    return {"message": "Booking confirmed & email sent"}
