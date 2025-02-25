from fastapi import APIRouter, HTTPException, Header
from pymongo import MongoClient
from dotenv import load_dotenv
import os, jwt, random, requests
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta

# ✅ Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")

client = MongoClient(MONGO_URI)
db = client["homezy_db"]
users_collection = db["users"]

auth_router = APIRouter()
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

# ✅ Generate JWT Token
def create_jwt_token(email: str):
    payload = {"sub": email, "exp": datetime.utcnow() + timedelta(days=1)}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

# ✅ Signup API (Sends OTP)
@auth_router.post("/signup")
def signup(user: UserSignup):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists")

    otp = str(random.randint(100000, 999999))
    hashed_password = pwd_context.hash(user.password)

    users_collection.insert_one({
        "name": user.name,
        "email": user.email,
        "password": hashed_password,
        "is_verified": False,
        "otp": otp,
        "otp_expiry": datetime.utcnow() + timedelta(minutes=10)
    })

    send_verification_email(user.email, otp)
    return {"message": "Signup successful! Please verify your email."}

# ✅ Send Verification Email
def send_verification_email(email, otp):
    data = {
        "sender": {"name": "Homezy", "email": BREVO_SENDER_EMAIL},
        "to": [{"email": email}],
        "subject": "Verify Your Homezy Account",
        "htmlContent": f"<p>Your OTP is <strong>{otp}</strong>. Valid for 10 minutes.</p>",
    }
    requests.post("https://api.brevo.com/v3/smtp/email", json=data, headers={"api-key": BREVO_API_KEY})

# ✅ Verify OTP
@auth_router.post("/verify-otp")
def verify_otp(data: VerifyOTP):
    user = users_collection.find_one({"email": data.email})
    if not user or user["otp"] != data.otp or user["otp_expiry"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    users_collection.update_one({"email": data.email}, {"$set": {"is_verified": True}})
    return {"message": "Email verified successfully!"}

# ✅ Login API
@auth_router.post("/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})
    if not existing_user or not pwd_context.verify(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if not existing_user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Email not verified")

    return {"message": "Login successful", "token": create_jwt_token(user.email), "name": existing_user["name"]}
