from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import requests
import os

# ✅ Load Brevo API Key
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# ✅ Initialize Router
email_router = APIRouter()

# ✅ Email Request Model
class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    message: str

# ✅ Function to Send Email via Brevo API
def send_email(to: str, subject: str, message: str):
    email_data = {
        "sender": {"name": "Homezy Services", "email": "no-reply@homezy.com"},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": f"<p>{message.replace('\n', '<br>')}</p>"
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
    import random
    otp = str(random.randint(100000, 999999))

    # ✅ Store OTP temporarily (In-memory storage, Redis, or Database can be used)
    # TODO: Implement proper OTP storage & expiration logic
    otp_storage = {}  # Temporary dictionary storage
    otp_storage[email] = otp

    try:
        send_email(email, "Your OTP Verification Code", f"Your OTP code is: <strong>{otp}</strong>")
        return {"message": "OTP sent successfully!", "otp": otp}  # Remove OTP in production response
    except HTTPException as e:
        return {"error": str(e.detail)}
