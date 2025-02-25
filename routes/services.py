from fastapi import APIRouter, HTTPException
import os, requests
from pydantic import BaseModel

email_router = APIRouter()
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")

class EmailData(BaseModel):
    to: str
    subject: str
    message: str

# ✅ Send General Email
@email_router.post("/")
def send_email(email_data: EmailData):
    data = {
        "sender": {"name": "Homezy", "email": BREVO_SENDER_EMAIL},
        "to": [{"email": email_data.to}],
        "subject": email_data.subject,
        "htmlContent": email_data.message
    }
    response = requests.post("https://api.brevo.com/v3/smtp/email", json=data, headers={"api-key": BREVO_API_KEY})
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Email sending failed")
    
    return {"message": "Email sent successfully!"}
