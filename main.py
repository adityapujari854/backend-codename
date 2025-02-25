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
BREVO_API_KEY = os.getenv("BREVO_API_KEY")  # ✅ Added Brevo API key

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

# ✅ Booking Model (Includes remarks)
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

# ✅ Function to Send Booking Confirmation Email using Brevo API
def send_booking_confirmation(booking: Booking):
    email_data = {
        "sender": {"name": "Homezy Services", "email": "no-reply@homezy.com"},
        "to": [{"email": booking.email, "name": booking.name}],
        "subject": "Booking Confirmation - Homezy",
        "htmlContent": f"""
            <h2>Booking Confirmation</h2>
            <p>Dear {booking.name},</p>
            <p>Your booking for <strong>{booking.serviceName}</strong> with <strong>{booking.providerName}</strong> has been confirmed.</p>
            <p><strong>Details:</strong></p>
            <ul>
                <li><strong>Service:</strong> {booking.serviceName}</li>
                <li><strong>Provider:</strong> {booking.providerName}</li>
                <li><strong>Price:</strong> ₹{booking.price}</li>
                <li><strong>Address:</strong> {booking.address}</li>
                <li><strong>Phone:</strong> {booking.phone}</li>
                <li><strong>Remarks:</strong> {booking.remarks}</li>
            </ul>
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
        raise HTTPException(status_code=500, detail="Failed to send confirmation email")

# ✅ Signup API
@app.post("/api/signup")
def signup(user: UserSignup):
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(user.password)
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
    return {
        "message": "Login successful",
        "token": token,
        "name": existing_user["name"],
    }

# ✅ Logout API
@app.post("/api/logout")
def logout():
    return {"message": "Logged out successfully"}

# ✅ Verify JWT Token API
@app.get("/api/verify-token")
def verify_token(authorization: str = Header(None)):
    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return {"message": "Token is valid", "email": payload["sub"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Fetch all services
@app.get("/api/services")
def get_services():
    services = list(services_collection.find({}, {"_id": 0}))
    return {"services": services}

# ✅ Fetch service providers from Foursquare API
@app.get("/api/providers")
def get_providers(service_name: str, city: str = "Pune"):
    headers = {"Authorization": FOURSQUARE_API_KEY, "Accept": "application/json"}
    params = {"query": service_name, "near": city, "limit": 10}

    try:
        response = requests.get("https://api.foursquare.com/v3/places/search", headers=headers, params=params)
        data = response.json()
        providers = [
            {
                "business_name": place["name"],
                "address": place["location"].get("formatted_address", "N/A"),
                "contact_number": place.get("tel", "N/A"),
                "website": place.get("website", ""),
            }
            for place in data.get("results", [])
        ]
        return {"providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Save a booking (Requires authentication)
@app.post("/api/bookings")
def create_booking(booking: Booking, authorization: str = Header(None)):
    user_email = get_current_user(authorization)

    if user_email != booking.email:
        raise HTTPException(status_code=403, detail="Unauthorized booking request")

    bookings_collection.insert_one(booking.dict())

    # ✅ Send email confirmation
    send_booking_confirmation(booking)

    return {"message": "Booking confirmed & email sent"}

# ✅ FIX: Allow Preflight CORS Requests
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return {"message": "Preflight request allowed"}