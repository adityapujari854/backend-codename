# routes/mybooking.py

from fastapi import APIRouter, HTTPException, Header
from database import bookings_collection
from middlewares.middleware import get_current_user
import logging

# ✅ Initialize Router
mybooking_router = APIRouter()

# ✅ Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Fetch All Bookings for a User (Separate clean route)
@mybooking_router.get("/mybooking", summary="Get all bookings for the logged-in user")
def get_my_bookings(authorization: str = Header(None)):
    """
    Fetch all bookings for the authenticated user (clean version for frontend MyBooking page).

    Args:
        authorization (str): JWT token for authentication.

    Returns:
        dict: List of bookings for the logged-in user.
    """
    # ✅ Authenticate User
    if not authorization or not authorization.startswith("Bearer "):
        logger.error("❌ Missing or invalid Authorization header format.")
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = authorization.split(" ")[1]
    user_email = get_current_user(f"Bearer {token}")

    if bookings_collection is None:
        logger.error("❌ Bookings collection not initialized")
        raise HTTPException(status_code=500, detail="Database error")

    # ✅ Fetch all bookings for the user
    bookings = list(bookings_collection.find({"email": user_email}, {"_id": 0}))

    if not bookings:
        logger.warning("⚠️ No bookings found for %s", user_email)
        raise HTTPException(status_code=404, detail="⚠️ No bookings found!")

    logger.info(f"✅ Found {len(bookings)} bookings for {user_email}")
    return {"bookings": bookings}
