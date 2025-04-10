from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from database import users_collection
from auth.jwt_handler import create_access_token, create_refresh_token, verify_token
from utils import send_verification_email
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

# ✅ Refresh Token Input Model
class RefreshRequest(BaseModel):
    refresh_token: str

# ✅ OTP Storage (Temporary, In-Memory)
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
        "is_verified": False
    })

    # ✅ Generate & Send OTP
    otp = str(random.randint(100000, 999999))
    otp_storage[user.email] = otp
    send_verification_email(user.email, otp)

    return {"message": "Signup successful. Please verify your email to proceed."}

# ✅ Login API — returns access token as `token` (for frontend compatibility)
@auth_router.post("/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})
    
    if not existing_user:
        raise HTTPException(status_code=400, detail="User not found")

    if not pwd_context.verify(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid password")

    if not existing_user.get("is_verified", False):
        raise HTTPException(status_code=403, detail="Email not verified. Please verify to login.")

    # ✅ Generate tokens
    access_token = create_access_token(user.email)
    refresh_token = create_refresh_token(user.email)

    return {
        "message": "Login successful",
        "token": access_token,  # ✅ matches frontend's expected key
        "refresh_token": refresh_token,
        "name": existing_user["name"]
    }

# ✅ Refresh Access Token using Refresh Token
@auth_router.post("/refresh-token")
def refresh_access_token(data: RefreshRequest):
    email = verify_token(data.refresh_token, token_type="refresh")
    new_access_token = create_access_token(email)
    return {
        "token": new_access_token,  # ✅ frontend can still store as `token`
        "message": "Access token refreshed"
    }

# ✅ Verify Email OTP
@auth_router.post("/verify-email")
def verify_email(verification: EmailVerification):
    stored_otp = otp_storage.get(verification.email)

    if not stored_otp or stored_otp != verification.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    users_collection.update_one(
        {"email": verification.email},
        {"$set": {"is_verified": True}}
    )
    otp_storage.pop(verification.email, None)

    return {"message": "Email verified successfully"}

# ✅ Logout Endpoint (Token-based Logout, optional)
@auth_router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}
