from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import requests
import os
import redis
import random

# ✅ Load Brevo API Key
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# ✅ Initialize Redis Connection
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

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

# ✅ Function to Send Email via Brevo API
def send_email(to: str, subject: str, message: str):
    email_data = {
        "sender": {"name": "Homezy Services", "email": "no-reply@homezy.com"},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": f"<html><body>{message}</body></html>"
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }

    response = requests.post("https://api.brevo.com/v3/smtp/email", json=email_data, headers=headers)

    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Failed to send email")

# ✅ API to Send Custom Emails
@email_router.post("/send")
def send_custom_email(email_request: EmailRequest):
    try:
        send_email(email_request.to, email_request.subject, email_request.message)
        return {"message": "📨 Email sent successfully!"}
    except HTTPException as e:
        return {"error": str(e.detail)}

# ✅ API to Send OTP Verification Email
@email_router.post("/send-otp")
def send_otp_email(email: EmailStr):
    otp = str(random.randint(100000, 999999))

    # ✅ Store OTP in Redis with 5-minute expiration
    redis_client.setex(f"otp:{email}", 300, otp)

    # ✅ OTP email content with better visuals
    otp_message = f"""
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

    try:
        send_email(email, "Your OTP Verification Code", otp_message)
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
