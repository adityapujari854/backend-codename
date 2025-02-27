from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr
from pymongo.collection import Collection
from database import bookings_collection
from middlewares.middleware import get_current_user
from email_service import send_email

# ✅ Initialize Router
bookings_router = APIRouter()

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
    user_email = get_current_user(authorization)

    # ✅ Ensure user is booking for themselves
    if user_email != booking.email:
        raise HTTPException(status_code=403, detail="Unauthorized booking request")

    # ✅ Insert booking into MongoDB
    collection.insert_one(booking.dict())

    # ✅ Send Confirmation Email
    try:
        send_email(
            recipient_email=booking.email,
            subject="Booking Confirmed - Homezy",
            message=f"Your booking for {booking.serviceName} with {booking.providerName} has been confirmed. Total: ₹{booking.price}"
        )
    except Exception as e:
        print(f"❌ Error sending email: {e}")

    return {"message": "✅ Booking confirmed & email sent!"}
