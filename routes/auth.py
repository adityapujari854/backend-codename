from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from pymongo import MongoClient
from datetime import datetime, timedelta
import jwt, os, random, requests

# ✅ Load environment variables (with defaults)
MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "no-reply@homezy.com")

# ✅ Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["homezy_db"]
users_collection = db["users"]

# ✅ Initialize Router & Password Hasher
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

class RequestOTP(BaseModel):
    email: EmailStr

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

# ✅ Generate JWT Token
def create_jwt_token(email: str):
    payload = {"sub": email, "exp": datetime.utcnow() + timedelta(days=1)}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

# ✅ Verify JWT Token
def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Get User Profile API
@auth_router.get("/profile")
def get_user_profile(authorization: str = Header(None)):
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid format")

    email = verify_jwt_token(authorization.split(" ")[1])  # Extract token & verify
    user = users_collection.find_one({"email": email}, {"_id": 0, "password": 0, "otp": 0, "otp_expiry": 0})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user": user}

# ✅ Request OTP API
@auth_router.post("/request-otp")
def request_otp(data: RequestOTP):
    email = data.email
    existing_user = users_collection.find_one({"email": email})

    if not existing_user:
        raise HTTPException(status_code=400, detail="User not found")

    if existing_user.get("is_verified", False):
        raise HTTPException(status_code=400, detail="User already verified")

    otp = str(random.randint(100000, 999999))
    expiry_time = datetime.utcnow() + timedelta(minutes=10)

    users_collection.update_one({"email": email}, {"$set": {"otp": otp, "otp_expiry": expiry_time}})
    
    return {"message": "OTP sent successfully!"}

# ✅ Signup API
@auth_router.post("/signup")
def signup(user: UserSignup):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(user.password)
    otp = str(random.randint(100000, 999999))

    users_collection.insert_one({
        "name": user.name,
        "email": user.email,
        "password": hashed_password,
        "is_verified": False,
        "otp": otp,
        "otp_expiry": datetime.utcnow() + timedelta(minutes=10),
    })

    return {"message": "Signup successful! Please verify your email."}

# ✅ Verify OTP API
@auth_router.post("/verify-otp")
def verify_otp(data: VerifyOTP):
    user = users_collection.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if user.get("is_verified", False):
        raise HTTPException(status_code=400, detail="User already verified")

    if user.get("otp") != data.otp or user.get("otp_expiry") < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    users_collection.update_one(
        {"email": data.email},
        {"$set": {"is_verified": True}, "$unset": {"otp": "", "otp_expiry": ""}}
    )

    return {"message": "Email verified successfully!"}

# ✅ Login API (Updated to return `is_verified`)
@auth_router.post("/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})

    if not existing_user or not pwd_context.verify(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "token": create_jwt_token(user.email),
        "name": existing_user["name"],
        "is_verified": existing_user.get("is_verified", False),
    }

# ✅ Check Verification API
@auth_router.post("/check-verification")
def check_verification(data: RequestOTP):
    user = users_collection.find_one({"email": data.email}, {"is_verified": 1, "_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"is_verified": user.get("is_verified", False)}
