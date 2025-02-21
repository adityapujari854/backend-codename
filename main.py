from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    allow_origins=["*"],  # Change this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ User Signup Model
class UserSignup(BaseModel):
    email: str
    password: str

# ✅ User Login Model
class UserLogin(BaseModel):
    email: str
    password: str

# ✅ Booking Model
class Booking(BaseModel):
    email: str
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

# ✅ Signup API
@app.post("/api/signup")
def signup(user: UserSignup):
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(user.password)
    users_collection.insert_one({"email": user.email, "password": hashed_password})
    return {"message": "User registered successfully"}

# ✅ Login API
@app.post("/api/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})
    if not existing_user or not pwd_context.verify(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = create_jwt_token(user.email)
    return {"message": "Login successful", "token": token}

# ✅ Fetch all services
@app.get("/api/services")
def get_services():
    services = list(services_collection.find({}, {"_id": 0}))
    return {"services": services}

# ✅ Fetch service providers from Foursquare API
@app.get("/api/providers")
def get_providers(service_name: str, city: str = "Pune"):
    headers = {
        "Authorization": FOURSQUARE_API_KEY,
        "Accept": "application/json",
    }
    params = {"query": service_name, "near": city, "limit": 10}

    try:
        response = requests.get("https://api.foursquare.com/v3/places/search", headers=headers, params=params)
        data = response.json()
        providers = [
            {
                "business_name": place["name"],
                "address": place["location"].get("formatted_address", "Address not available"),
                "contact_number": place.get("tel", "Contact not available"),
                "website": place.get("website", ""),
            }
            for place in data.get("results", [])
        ]
        return {"providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Save a booking
@app.post("/api/bookings")
def create_booking(booking: Booking):
    bookings_collection.insert_one(booking.dict())
    return {"message": "Booking confirmed"}

# ✅ Add service to cart
@app.post("/api/cart")
def add_to_cart(data: dict):
    user_email = data.get("email")
    service = data.get("service")

    if not user_email or not service:
        raise HTTPException(status_code=400, detail="Invalid request")

    cart_collection.insert_one({"email": user_email, "service": service})
    return {"message": "Service added to cart"}

# ✅ Fetch cart items
@app.get("/api/cart/{email}")
def get_cart_items(email: str):
    cart_items = list(cart_collection.find({"email": email}, {"_id": 0, "email": 0}))
    return {"cart": cart_items}
