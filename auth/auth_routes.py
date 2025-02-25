from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from database import users_collection
from auth.jwt_handler import create_jwt_token, verify_jwt_token
from utils.utils import send_verification_email
import os
import random

# ✅ Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Load Brevo API Key
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# ✅ Initialize Router
auth_router = APIRouter()

# ✅ User Signup Model
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str

# ✅ User Login Model
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ✅ Email Verification Model
class EmailVerification(BaseModel):
    email: EmailStr
    otp: str

# ✅ OTP Storage (Temporary)
otp_storage = {}

# ✅ Signup API
@auth_router.post("/signup")
def signup(user: UserSignup):
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # ✅ Hash Password
    hashed_password = pwd_context.hash(user.password)

    # ✅ Store User in Database (Initially Unverified)
    users_collection.insert_one({
        "name": user.name,
        "email": user.email,
        "password": hashed_password,
        "is_verified": False  # Mark user as unverified initially
    })

    # ✅ Generate & Send OTP for Email Verification
    otp = str(random.randint(100000, 999999))  # 6-digit OTP
    otp_storage[user.email] = otp
    send_verification_email(user.email, otp)  # Send OTP via Brevo

    return {"message": "Signup successful. Please verify your email to proceed."}

# ✅ Login API
@auth_router.post("/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})
    
    if not existing_user:
        raise HTTPException(status_code=400, detail="User not found")

    # ✅ Verify Password
    if not pwd_context.verify(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid password")

    # ✅ Check if Email is Verified
    if not existing_user.get("is_verified", False):
        raise HTTPException(status_code=403, detail="Email not verified. Please verify to login.")

    # ✅ Generate JWT Token
    token = create_jwt_token(user.email)
    
    return {
        "message": "Login successful",
        "token": token,
        "name": existing_user["name"],
    }

# ✅ Verify Email OTP API
@auth_router.post("/verify-email")
def verify_email(verification: EmailVerification):
    stored_otp = otp_storage.get(verification.email)

    if not stored_otp or stored_otp != verification.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # ✅ Mark User as Verified
    users_collection.update_one(
        {"email": verification.email},
        {"$set": {"is_verified": True}}
    )

    # ✅ Remove OTP after successful verification
    otp_storage.pop(verification.email, None)

    return {"message": "Email verified successfully"}

# ✅ Logout API (Token-based logout)
@auth_router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}
