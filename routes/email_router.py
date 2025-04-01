from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from send_email import send_email, get_booking_confirmation_email_template, get_otp_email_template

# Create an APIRouter instance
email_router = APIRouter()

# Pydantic models for input validation
class BookingData(BaseModel):
    email: str
    name: str
    phone: str
    address: str
    services: list

class OTPData(BaseModel):
    otp_code: str

# Endpoint to send a booking confirmation email
@email_router.post("/send-booking-confirmation")
async def send_booking_confirmation_email(booking_data: BookingData):
    try:
        # Generate the HTML template for booking confirmation
        email_template = get_booking_confirmation_email_template(booking_data.dict())

        # Send the email
        success = send_email(booking_data.email, "Booking Confirmation - Homezy", email_template, is_html=True)

        # Return success message if email is sent
        if success:
            return {"message": "Booking confirmation email sent successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to send booking confirmation email")
    
    except Exception as e:
        # If any error occurs during email sending, raise an HTTP exception
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

# Endpoint to send an OTP email
@email_router.post("/send-otp")
async def send_otp_email(otp_data: OTPData):
    try:
        # Generate the HTML template for OTP email
        otp_template = get_otp_email_template(otp_data.otp_code)

        # Send the OTP email
        success = send_email("user@example.com", "Your OTP Code", otp_template, is_html=True)

        # Return success message if OTP email is sent
        if success:
            return {"message": "OTP email sent successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to send OTP email")
    
    except Exception as e:
        # If any error occurs during OTP email sending, raise an HTTP exception
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
