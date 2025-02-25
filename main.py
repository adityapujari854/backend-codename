from fastapi import FastAPI, HTTPException, Depends, Header
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import random

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

client = MongoClient(MONGO_URI)
db = client["homezy_db"]
services_collection = db["services"]
bookings_collection = db["bookings"]
users_collection = db["users"]
cart_collection = db["cart"]
otp_collection = db["otp_verification"]

app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"],
)

# ✅ Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ User Models
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

# ✅ Booking Model
class Booking(BaseModel):
    email: EmailStr
    name: str
    phone: str
    address: str
    serviceName: str
    providerName: str
    price: int
    remarks: str

# ✅ Generate JWT Token
def create_jwt_token(email: str):
    payload = {"sub": email, "exp": datetime.utcnow() + timedelta(days=1)}
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token

# ✅ Decode & Verify JWT Token
def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Middleware to get the current user from JWT
def get_current_user(authorization: str = Header(None)):
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid format")

    token = authorization.split(" ")[1]
    return verify_jwt_token(token)

# ✅ Function to Send Emails via Brevo API
def send_email(to_email, subject, html_content):
    email_data = {
        "sender": {"name": "Homezy Services", "email": "no-reply@homezy.com"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }

    response = requests.post("https://api.brevo.com/v3/smtp/email", json=email_data, headers=headers)
    
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Failed to send email")

# ✅ Signup API with Email Verification
@app.post("/api/signup")
def signup(user: UserSignup):
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(user.password)
    users_collection.insert_one({"name": user.name, "email": user.email, "password": hashed_password, "verified": False})

    # ✅ Send account creation email
    send_email(
        user.email,
        "🎉 Welcome to Homezy!",
        f"<h2>Hi {user.name},</h2><p>Your account has been successfully created! 🎉</p><p>Please verify your email to start using Homezy.</p>"
    )

    return {"message": "User registered successfully. Please verify your email."}

# ✅ OTP Generation & Email Sending
@app.post("/api/send-otp")
def send_otp(email: EmailStr):
    otp = str(random.randint(100000, 999999))

    # ✅ Store OTP in Database
    otp_collection.update_one(
        {"email": email},
        {"$set": {"otp": otp, "created_at": datetime.utcnow()}},
        upsert=True
    )

    # ✅ Send OTP Email
    send_email(
        email,
        "🔐 Homezy Email Verification OTP",
        f"<h2>Your OTP: <strong>{otp}</strong></h2><p>Please enter this OTP to verify your email.</p>"
    )

    return {"message": "OTP sent successfully."}

# ✅ Verify OTP & Activate Account
@app.post("/api/verify-otp")
def verify_otp(data: VerifyOTP):
    record = otp_collection.find_one({"email": data.email})

    if not record or record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # ✅ Mark user as verified
    users_collection.update_one({"email": data.email}, {"$set": {"verified": True}})
    otp_collection.delete_one({"email": data.email})  # ✅ Remove OTP after verification

    return {"message": "Email verified successfully!"}

# ✅ Login API
@app.post("/api/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})

    if not existing_user:
        raise HTTPException(status_code=400, detail="User not found")

    if not pwd_context.verify(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid password")

    if not existing_user.get("verified", False):
        raise HTTPException(status_code=400, detail="Email not verified. Please verify your email.")

    token = create_jwt_token(user.email)
    return {"message": "Login successful", "token": token, "name": existing_user["name"]}

# ✅ Save a booking & Send Email Confirmation
@app.post("/api/bookings")
def create_booking(booking: Booking, authorization: str = Header(None)):
    user_email = get_current_user(authorization)

    if user_email != booking.email:
        raise HTTPException(status_code=403, detail="Unauthorized booking request")

    bookings_collection.insert_one(booking.dict())

    # ✅ Send booking confirmation email
    send_email(
        booking.email,
        "📅 Booking Confirmation - Homezy",
        f"""
        <h2>Booking Confirmed!</h2>
        <p>Dear {booking.name},</p>
        <p>Your booking for <strong>{booking.serviceName}</strong> with <strong>{booking.providerName}</strong> has been confirmed.</p>
        <ul>
            <li><strong>Service:</strong> {booking.serviceName}</li>
            <li><strong>Provider:</strong> {booking.providerName}</li>
            <li><strong>Price:</strong> ₹{booking.price}</li>
            <li><strong>Address:</strong> {booking.address}</li>
        </ul>
        <p>Thank you for choosing Homezy!</p>
        """
    )

    return {"message": "Booking confirmed & email sent"}

# ✅ Fetch all services
@app.get("/api/services")
def get_services():
    services = list(services_collection.find({}, {"_id": 0}))
    return {"services": services}

# ✅ FIX: Allow Preflight CORS Requests
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return {"message": "Preflight request allowed"}
