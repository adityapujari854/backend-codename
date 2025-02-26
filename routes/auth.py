from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from pymongo import MongoClient
from datetime import datetime, timedelta
import jwt, os, random, requests

# ✅ Load environment variables
MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
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

class RequestOTP(BaseModel):  # ✅ Fixed Model for Request Body
    email: EmailStr

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

# ✅ Generate JWT Token
def create_jwt_token(email: str):
    payload = {"sub": email, "exp": datetime.utcnow() + timedelta(days=1)}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

# ✅ Request OTP (Fixed API)
@auth_router.post("/request-otp")
def request_otp(data: RequestOTP):  # ✅ Use Pydantic model to extract JSON body
    email = data.email  # ✅ Extract email from request body

    existing_user = users_collection.find_one({"email": email})
    
    if not existing_user:
        raise HTTPException(status_code=400, detail="User not found")

    otp = str(random.randint(100000, 999999))
    expiry_time = datetime.utcnow() + timedelta(minutes=10)

    users_collection.update_one({"email": email}, {"$set": {"otp": otp, "otp_expiry": expiry_time}})

    if not send_verification_email(email, otp):
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "OTP sent successfully!"}

# ✅ Send Verification Email
def send_verification_email(email: str, otp: str):
    data = {
        "sender": {"name": "Homezy", "email": BREVO_SENDER_EMAIL},
        "to": [{"email": email}],
        "subject": "Verify Your Homezy Account",
        "htmlContent": f"<p>Your OTP is <strong>{otp}</strong>. Valid for 10 minutes.</p>",
    }

    headers = {"Content-Type": "application/json", "api-key": BREVO_API_KEY}
    response = requests.post("https://api.brevo.com/v3/smtp/email", json=data, headers=headers)

    if response.status_code not in [200, 201]:
        print("❌ Failed to send OTP email:", response.json())  # Debugging
        return False
    return True

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

    if not send_verification_email(user.email, otp):
        raise HTTPException(status_code=500, detail="Signup successful, but failed to send OTP")

    return {"message": "Signup successful! Please verify your email."}

# ✅ Verify OTP
@auth_router.post("/verify-otp")
def verify_otp(data: VerifyOTP):
    user = users_collection.find_one({"email": data.email})

    if not user or user.get("otp") != data.otp or user.get("otp_expiry") < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    users_collection.update_one({"email": data.email}, {"$set": {"is_verified": True}})
    return {"message": "Email verified successfully!"}

# ✅ Login API
@auth_router.post("/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})

    if not existing_user or not pwd_context.verify(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "token": create_jwt_token(user.email),
        "name": existing_user["name"],
    }
