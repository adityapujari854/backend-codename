import os
import requests

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

def send_email(to_email: str, subject: str, message: str):
    email_data = {
        "sender": {"name": "Homezy", "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<p>{message}</p>"
    }

    headers = {"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post("https://api.brevo.com/v3/smtp/email", json=email_data, headers=headers)

    if response.status_code != 201:
        raise Exception("Failed to send email")
