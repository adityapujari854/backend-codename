from fastapi import APIRouter, HTTPException, Depends, Header, Request
from models.booking import Booking
from database import bookings_collection
from middlewares.middleware import get_current_user
from utils import store_booking_in_db, send_booking_confirmation_email
import logging
from pydantic import ValidationError

# ✅ Initialize Router
bookings_router = APIRouter()

# ✅ Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Save a Booking (Requires Authentication)
@bookings_router.post("/", summary="Create a new booking")
async def create_booking(request: Request, authorization: str = Header(None)):
    """
    Save a new booking and send confirmation email.

    Args:
        request (Request): Incoming booking request.
        authorization (str): JWT token for authentication.

    Returns:
        dict: Confirmation message.
    """
    logger.info("📥 Received Booking Request")

    # ✅ Authenticate User
    user_email = get_current_user(authorization)

    try:
        data = await request.json()

        # ✅ Validate required fields (Removed price validation)
        required_fields = ["email", "name", "phone", "address", "services"]

        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"❌ Missing field: {field}")
                raise HTTPException(status_code=422, detail=f"Missing or invalid field: {field}")

        if user_email != data.get("email"):
            logger.warning("❌ Unauthorized Booking Attempt by %s", user_email)
            raise HTTPException(status_code=403, detail="Unauthorized booking request")

        # ✅ Validate services list
        if not isinstance(data["services"], list) or len(data["services"]) == 0:
            logger.error("❌ Invalid or empty services list")
            raise HTTPException(status_code=422, detail="Invalid services list")

        for service in data["services"]:
            if "serviceName" not in service or "providerName" not in service:
                logger.error("❌ Missing service details: %s", service)
                raise HTTPException(status_code=422, detail="Missing or invalid service details")

        # ✅ Store booking in MongoDB (With `None` check)
        if bookings_collection is not None:
            if not store_booking_in_db(data):
                logger.error("❌ Database Insertion Failed for Booking: %s", data)
                raise HTTPException(status_code=500, detail="Failed to store booking in database")
        else:
            logger.error("❌ MongoDB collection is None")
            raise HTTPException(status_code=500, detail="Database connection error")

        # ✅ Send confirmation email
        email_status = send_booking_confirmation_email(data)
        if not email_status:
            logger.error("❌ Email Sending Failed for Booking: %s", data)
            raise HTTPException(status_code=500, detail="Failed to send confirmation email")

        logger.info("✅ Booking confirmed & email sent to %s", data["email"])

        return {"message": "✅ Booking confirmed & email sent!"}

    except ValidationError as e:
        logger.error("❌ Validation Error: %s", str(e))
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

    except Exception as e:
        logger.error("❌ Internal Server Error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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

    if bookings_collection is not None:
        # ✅ Fetch bookings from MongoDB
        bookings = list(bookings_collection.find({"email": user_email}, {"_id": 0}))

        if not bookings:
            logger.warning("⚠️ No bookings found for %s", user_email)
            raise HTTPException(status_code=404, detail="⚠️ No bookings found!")

        logger.info(f"✅ {len(bookings)} bookings found for {user_email}")
        return {"bookings": bookings}

    else:
        logger.error("❌ MongoDB collection is None")
        raise HTTPException(status_code=500, detail="Database connection error")
