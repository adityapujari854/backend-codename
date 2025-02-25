from fastapi import APIRouter, HTTPException, Depends, Header
from models.booking import Booking
from database import bookings_collection
from middlewares.middleware import get_current_user
import requests
import os

# ✅ Load Brevo API Key
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# ✅ Initialize Router
router = APIRouter()

# ✅ Function to Send Booking Confirmation Email via Brevo API
def send_booking_confirmation(booking: Booking):
    email_data = {
        "sender": {"name": "Homezy Services", "email": "no-reply@homezy.com"},
        "to": [{"email": booking.email, "name": booking.name}],
        "subject": "Booking Confirmation - Homezy",
        "htmlContent": f"""
            <h2>Booking Confirmation</h2>
            <p>Dear {booking.name},</p>
            <p>Your booking for <strong>{booking.serviceName}</strong> with <strong>{booking.providerName}</strong> has been confirmed.</p>
            <p><strong>Details:</strong></p>
            <ul>
                <li><strong>Service:</strong> {booking.serviceName}</li>
                <li><strong>Provider:</strong> {booking.providerName}</li>
                <li><strong>Price:</strong> ₹{booking.price}</li>
                <li><strong>Address:</strong> {booking.address}</li>
                <li><strong>Phone:</strong> {booking.phone}</li>
                <li><strong>Remarks:</strong> {booking.remarks}</li>
            </ul>
            <p>Thank you for choosing Homezy!</p>
        """
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }

    response = requests.post("https://api.brevo.com/v3/smtp/email", json=email_data, headers=headers)
    
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Failed to send confirmation email")

# ✅ Save a booking (Requires authentication)
@router.post("/api/bookings")
def create_booking(booking: Booking, authorization: str = Header(None)):
    user_email = get_current_user(authorization)

    if user_email != booking.email:
        raise HTTPException(status_code=403, detail="Unauthorized booking request")

    # ✅ Store booking in the database
    bookings_collection.insert_one(booking.dict())

    # ✅ Send email confirmation
    send_booking_confirmation(booking)

    return {"message": "Booking confirmed & email sent"}

# ✅ Fetch all bookings for a user (Requires authentication)
@router.get("/api/bookings")
def get_user_bookings(authorization: str = Header(None)):
    user_email = get_current_user(authorization)
    bookings = list(bookings_collection.find({"email": user_email}, {"_id": 0}))

    if not bookings:
        raise HTTPException(status_code=404, detail="No bookings found")

    return {"bookings": bookings}
