from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import redis
import random
from email_service import send_email
import os

# ✅ Initialize Redis Connection
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# ✅ Load Brevo API Key from environment
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# ✅ Initialize Router
email_router = APIRouter()

# ✅ Email Request Model
class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    message: str

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

# ✅ OTP Email Content Template
def get_otp_email_template(otp: str):
    """
    Generate a custom OTP email template with a visually appealing design.
    
    Args:
        otp (str): The OTP to be included in the email.
    
    Returns:
        str: HTML content for the OTP email.
    """
    return f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
        <div style="text-align: center; padding: 20px; background-color: #f0f0f0; border-radius: 8px;">
            <h2 style="color: #007bff;">Your OTP Verification Code</h2>
            <p style="font-size: 16px; color: #555;">
                Hello, <br><br>
                We have received a request to verify your email address. Please use the OTP below to complete the verification process.
            </p>
            <div style="font-size: 24px; font-weight: bold; color: #007bff; padding: 10px; background-color: #e0f7fa; border-radius: 6px;">
                {otp}
            </div>
            <p style="font-size: 14px; color: #777; margin-top: 20px;">
                This OTP is valid for 5 minutes only. If you didn't request this, please ignore this email.
            </p>
        </div>
    </div>
    """

# ✅ Function to Send Email via Brevo API (Updated with new template)
def send_email_via_brevo(to: str, subject: str, message: str):
    """Send email using Brevo API."""
    try:
        send_email(to, subject, message)
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

# ✅ API to Send Custom Emails
@email_router.post("/send")
def send_custom_email(email_request: EmailRequest):
    try:
        send_email_via_brevo(email_request.to, email_request.subject, email_request.message)
        return {"message": "📨 Email sent successfully!"}
    except HTTPException as e:
        return {"error": str(e.detail)}

# ✅ API to Send OTP Verification Email
@email_router.post("/send-otp")
def send_otp_email(email: EmailStr):
    otp = str(random.randint(100000, 999999))

    # ✅ Store OTP in Redis with 5-minute expiration
    redis_client.setex(f"otp:{email}", 300, otp)

    # ✅ Get OTP email content with enhanced visuals
    otp_message = get_otp_email_template(otp)

    # ✅ Send OTP email via Brevo API
    try:
        send_email_via_brevo(email, "Your OTP Verification Code", otp_message)
        return {"message": "OTP sent successfully!"}
    except HTTPException as e:
        return {"error": str(e.detail)}

# ✅ API to Verify OTP
@email_router.post("/verify-otp")
def verify_otp(request: OTPVerifyRequest):
    stored_otp = redis_client.get(f"otp:{request.email}")

    if stored_otp is None:
        raise HTTPException(status_code=400, detail="OTP expired or not found")

    if stored_otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # ✅ OTP is valid, delete it after verification
    redis_client.delete(f"otp:{request.email}")
    
    return {"message": "✅ OTP verified successfully!"}
