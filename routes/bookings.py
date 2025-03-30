from fastapi import APIRouter, HTTPException, Header, Depends, Request
from models.booking import Booking
from database import bookings_collection
from middlewares.middleware import get_current_user
from utils import store_booking_in_db, send_booking_confirmation_email
import logging
from pydantic import ValidationError
from typing import List

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
        # ✅ Parse Incoming Data
        data = await request.json()

        # ✅ Validate Required Fields
        required_fields = ["email", "name", "phone", "address", "services"]
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"❌ Missing field: {field}")
                raise HTTPException(status_code=422, detail=f"Missing or invalid field: {field}")

        # ✅ Authorization Check: Ensure user is booking for themselves
        if user_email != data.get("email"):
            logger.warning("❌ Unauthorized Booking Attempt by %s", user_email)
            raise HTTPException(status_code=403, detail="Unauthorized booking request")

        # ✅ Validate Services List
        if not isinstance(data["services"], list) or len(data["services"]) == 0:
            logger.error("❌ Invalid or empty services list")
            raise HTTPException(status_code=422, detail="Invalid services list")

        for service in data["services"]:
            if "serviceName" not in service or "providerName" not in service:
                logger.error("❌ Missing service details: %s", service)
                raise HTTPException(status_code=422, detail="Missing or invalid service details")

        # ✅ Check MongoDB Collection
        if bookings_collection is None:
            logger.error("❌ Database collection is not initialized")
            raise HTTPException(status_code=500, detail="Database collection is None")

        # ✅ Store booking in MongoDB
        if not store_booking_in_db(data):
            logger.error("❌ Database Insertion Failed for Booking: %s", data)
            raise HTTPException(status_code=500, detail="Failed to store booking in database")

        # ✅ Send Confirmation Email with Proper Address Formatting
        try:
            # ✅ Format Address Properly
            address = (
                f"- **Flat:** {data['address'].get('flat', 'N/A')}\n"
                f"- **Street:** {data['address'].get('street', 'N/A')}\n"
                f"- **Landmark:** {data['address'].get('landmark', 'N/A')}\n"
                f"- **City:** {data['address'].get('city', 'N/A')}\n"
                f"- **State:** {data['address'].get('state', 'N/A')}\n"
                f"- **Pincode:** {data['address'].get('pincode', 'N/A')}"
            )

            # ✅ Format Services List
            services_list = "\n".join(
                [f"- {s['serviceName']} by {s['providerName']}" for s in data["services"]]
            )

            # ✅ Email Content
            email_message = (
                f"Dear {data['name']},\n\n"
                "🎉 Thank you for booking with Homezy!\n\n"
                "📌 *Booking Details:*\n"
                f"- 📞 Phone: {data['phone']}\n"
                f"{address}\n\n"
                "🛠️ *Services Booked:*\n"
                f"{services_list}\n\n"
                "✅ Your booking is confirmed. We'll reach out shortly with further details.\n\n"
                "Regards,\n"
                "The Homezy Team"
            )

            # ✅ Send Email
            email_status = send_booking_confirmation_email(
                to=data["email"],
                subject="Booking Confirmed - Homezy",
                message=email_message
            )

            if not email_status:
                logger.error("❌ Email Sending Failed for Booking: %s", data)
                raise HTTPException(status_code=500, detail="Failed to send confirmation email")

            logger.info("✅ Booking confirmed & email sent to %s", data["email"])
            return {"message": "✅ Booking confirmed & email sent!"}

        except Exception as e:
            logger.error("⚠️ Email Sending Failed: %s", str(e))
            raise HTTPException(status_code=500, detail="Booking confirmed, but email failed to send")

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
    logger.info("📥 Fetching bookings for user")

    # ✅ Authenticate User
    user_email = get_current_user(authorization)

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
