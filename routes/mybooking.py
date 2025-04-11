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

# ✅ Fetch All Bookings for a User (used by frontend at /api/mybooking)
@mybooking_router.get("/api/mybooking", summary="Get all bookings for the logged-in user")
def get_my_bookings(authorization: str = Header(None)):
    """
    Fetch all bookings for the authenticated user (clean API used by /mybooking frontend page).

    Args:
        authorization (str): JWT token for authentication.

    Returns:
        dict: List of bookings for the logged-in user.
    """
    logger.info("📥 MyBooking request received")

    # ✅ Validate Authorization Header
    if not authorization or not authorization.startswith("Bearer "):
        logger.error("❌ Invalid or missing Authorization header")
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    # ✅ Extract Bearer Token and Get Email
    token = authorization.split(" ")[1]
    user_email = get_current_user(f"Bearer {token}")

    if not user_email:
        logger.warning("❌ Invalid token or user not found")
        raise HTTPException(status_code=403, detail="User authentication failed")

    # ✅ Check MongoDB Connection
    if bookings_collection is None:
        logger.critical("❌ Bookings collection not available in DB")
        raise HTTPException(status_code=500, detail="Database error")

    try:
        # ✅ Query Bookings by Email
        bookings = list(bookings_collection.find({"email": user_email}, {"_id": 0}))

        if not bookings:
            logger.info("⚠️ No bookings found for user: %s", user_email)
            raise HTTPException(status_code=404, detail="⚠️ No bookings found!")

        logger.info("✅ %d bookings found for user: %s", len(bookings), user_email)
        return {"bookings": bookings}

    except Exception as e:
        logger.exception("❌ Unexpected error while fetching bookings")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
