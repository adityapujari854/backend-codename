import requests
import os
from fastapi import HTTPException

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

def send_verification_email(email: str, otp: str):
    """Sends an OTP email using Brevo API for email verification."""
    
    email_data = {
        "sender": {"name": "Homezy Services", "email": "no-reply@homezy.com"},
        "to": [{"email": email}],
        "subject": "Verify Your Email - Homezy",
        "htmlContent": f"""
            <h2>Email Verification</h2>
            <p>Hello,</p>
            <p>Your OTP for verifying your email is <strong>{otp}</strong>.</p>
            <p>Please enter this OTP in the verification form to activate your account.</p>
            <p>If you didn't request this, please ignore this email.</p>
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
        raise HTTPException(status_code=500, detail="Failed to send verification email")
