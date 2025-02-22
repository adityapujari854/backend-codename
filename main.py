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

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")

client = MongoClient(MONGO_URI)
db = client["homezy_db"]
services_collection = db["services"]
bookings_collection = db["bookings"]
users_collection = db["users"]
cart_collection = db["cart"]

app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://codename2025.vercel.app"],
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

# ✅ Booking Model
class Booking(BaseModel):
    email: EmailStr
    name: str
    phone: str
    address: str
    serviceName: str
    providerName: str
    price: int

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
    token = authorization.split(" ")[1]  # Extract token from "Bearer <token>"
    return verify_jwt_token(token)

# ✅ Signup API
@app.post("/api/signup")
def signup(user: UserSignup):
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(user.password)  # ✅ Hashing password
    users_collection.insert_one({"name": user.name, "email": user.email, "password": hashed_password})

    return {"message": "User registered successfully"}

# ✅ Login API
@app.post("/api/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})
    if not existing_user:
        raise HTTPException(status_code=400, detail="User not found")

    if not pwd_context.verify(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid password")

    token = create_jwt_token(user.email)
    return {"message": "Login successful", "token": token, "name": existing_user["name"]}

# ✅ Logout API
@app.post("/api/logout")
def logout():
    return {"message": "Logged out successfully"}

# ✅ Verify JWT Token API
@app.get("/api/verify-token")
def verify_token(authorization: str = Header(None)):
    user_email = get_current_user(authorization)
    return {"message": "Token is valid", "email": user_email}

# ✅ Fetch User Details API
@app.get("/api/user")
def get_user(authorization: str = Header(None)):
    email = get_current_user(authorization)
    user = users_collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}

# ✅ Fetch all services
@app.get("/api/services")
def get_services():
    services = list(services_collection.find({}, {"_id": 0}))
    return {"services": services}

# ✅ Save a booking (Requires authentication)
@app.post("/api/bookings")
def create_booking(booking: Booking, authorization: str = Header(None)):
    user_email = get_current_user(authorization)
    if user_email != booking.email:
        raise HTTPException(status_code=403, detail="Unauthorized booking request")
    bookings_collection.insert_one(booking.dict())
    return {"message": "Booking confirmed"}

# ✅ Fetch cart items (Requires authentication)
@app.get("/api/cart")
def get_cart_items(authorization: str = Header(None)):
    user_email = get_current_user(authorization)
    cart_items = list(cart_collection.find({"email": user_email}, {"_id": 0, "email": 0}))
    return {"cart": cart_items}

# ✅ FIX: Allow Preflight CORS Requests
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return {"message": "Preflight request allowed"}
