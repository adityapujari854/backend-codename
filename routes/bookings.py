from fastapi import APIRouter, HTTPException, Header, Depends, Request
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

    # ✅ Authenticate User with "Bearer" Token
    if not authorization or not authorization.startswith("Bearer "):
        logger.error("❌ Missing or invalid Authorization header format.")
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = authorization.split(" ")[1]
    user_email = get_current_user(f"Bearer {token}")

    try:
        data = await request.json()

        # ✅ Validate required fields
        required_fields = ["email", "name", "phone", "address", "services"]

        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"❌ Missing field: {field}")
                raise HTTPException(status_code=422, detail=f"Missing or invalid field: {field}")

        # ✅ Ensure the authenticated user is booking for themselves
        if user_email != data.get("email"):
            logger.warning("❌ Unauthorized Booking Attempt by %s", user_email)
            raise HTTPException(status_code=403, detail="Unauthorized booking request")

        # ✅ Validate address structure
        address = data.get("address", {})
        address_fields = ["flat", "street", "landmark", "city", "state", "pincode"]

        for field in address_fields:
            if field not in address or not address[field]:
                logger.warning(f"❌ Missing address field: {field}")
                raise HTTPException(status_code=422, detail=f"Missing or invalid address field: {field}")

        # ✅ Validate services list
        if not isinstance(data["services"], list) or len(data["services"]) == 0:
            logger.error("❌ Invalid or empty services list")
            raise HTTPException(status_code=422, detail="Invalid services list")

        for service in data["services"]:
            if "serviceName" not in service or "providerName" not in service:
                logger.error("❌ Missing service details: %s", service)
                raise HTTPException(status_code=422, detail="Missing or invalid service details")

        # ✅ Database Validation: Check if MongoDB collection is valid
        if bookings_collection is None:
            logger.error("❌ Database collection is not initialized")
            raise HTTPException(status_code=500, detail="Database collection is None")

        # ✅ Store booking in MongoDB
        if not store_booking_in_db(data):
            logger.error("❌ Database Insertion Failed for Booking: %s", data)
            raise HTTPException(status_code=500, detail="Failed to store booking in database")

        # ✅ Send confirmation email with all address fields
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
    if not authorization or not authorization.startswith("Bearer "):
        logger.error("❌ Missing or invalid Authorization header format.")
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = authorization.split(" ")[1]
    user_email = get_current_user(f"Bearer {token}")

    # ✅ Database Validation: Check if MongoDB collection is valid
    if bookings_collection is None:
        logger.error("❌ Database collection is not initialized")
        raise HTTPException(status_code=500, detail="Database collection is None")

    # ✅ Fetch bookings from MongoDB
    bookings = list(bookings_collection.find({"email": user_email}, {"_id": 0}))

    if not bookings:
        logger.warning("⚠️ No bookings found for %s", user_email)
        raise HTTPException(status_code=404, detail="⚠️ No bookings found!")

    logger.info(f"✅ {len(bookings)} bookings found for {user_email}")
    return {"bookings": bookings}
