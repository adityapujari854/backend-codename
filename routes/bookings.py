from fastapi import APIRouter, HTTPException, Depends, Header, Body
from models.booking import Booking
from database import bookings_collection
from middlewares.middleware import get_current_user
from utils.utils import store_booking_in_db, send_booking_confirmation_email
import logging

# ✅ Initialize Router
bookings_router = APIRouter()

# ✅ Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ✅ Save a Booking (Requires Authentication)
@bookings_router.post("/", summary="Create a new booking")
def create_booking(booking: Booking, authorization: str = Header(None)):
    """
    Save a new booking and send confirmation email.

    Args:
        booking (Booking): Booking details.
        authorization (str): JWT token for authentication.

    Returns:
        dict: Confirmation message.
    """
    logger.info("📥 Received Booking Request: %s", booking.dict())
    logger.info("🛂 Authorization Header: %s", authorization)

    # ✅ Authenticate User
    user_email = get_current_user(authorization)

    if user_email != booking.email:
        logger.warning("❌ Unauthorized Booking Attempt by %s", user_email)
        raise HTTPException(status_code=403, detail="Unauthorized booking request")

    # ✅ Prepare booking data for MongoDB
    booking_data = {
        "email": booking.email,
        "name": booking.name,
        "phone": booking.phone,
        "address": booking.address,
        "services": [
            {
                "service_name": booking.serviceName,
                "provider_name": booking.providerName,
                "price": booking.price,
                "remarks": booking.remarks
            }
        ],
        "total_price": booking.price
    }

    # ✅ Store booking in MongoDB
    if not store_booking_in_db(booking_data):
        raise HTTPException(status_code=500, detail="Failed to store booking in database")

    # ✅ Send confirmation email
    if not send_booking_confirmation_email(booking_data):
        raise HTTPException(status_code=500, detail="Failed to send confirmation email")

    logger.info("✅ Booking confirmed & email sent to %s", booking.email)

    return {"message": "✅ Booking confirmed & email sent!"}


# ✅ Fetch All Bookings for a User (Requires Authentication)
@bookings_router.get("/", summary="Get all bookings for the logged-in user")
def get_user_bookings(authorization: str = Header(None)):
    """
    Fetch all bookings for the authenticated user.

    Args:
        authorization (str): JWT token for authentication.

    Returns:
        dict: User bookings.
    """
    # ✅ Authenticate User
    user_email = get_current_user(authorization)
    
    # ✅ Fetch bookings from MongoDB
    bookings = list(bookings_collection.find({"email": user_email}, {"_id": 0}))

    if not bookings:
        logger.warning("⚠️ No bookings found for %s", user_email)
        raise HTTPException(status_code=404, detail="⚠️ No bookings found!")

    logger.info(f"✅ {len(bookings)} bookings found for {user_email}")
    return {"bookings": bookings}
