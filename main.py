from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from typing import Optional

# ✅ Load environment variables
load_dotenv()

# ✅ Securely Store Keys & URLs
MONGO_URI = os.getenv("MONGO_URI")
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
FOURSQUARE_URL = "https://api.foursquare.com/v3/places/search"
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ✅ MongoDB Connection
client = MongoClient(MONGO_URI)
db = client["homezy_db"]
services_collection = db["services"]
bookings_collection = db["bookings"]
users_collection = db["users"]  # ✅ New Collection for User Authentication

app = FastAPI()

# ✅ Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Pydantic Models
class UserSignup(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Booking(BaseModel):
    name: str
    phone: str
    address: str
    serviceName: str
    providerName: str
    price: float

# ✅ Hash Password
def hash_password(password: str):
    return pwd_context.hash(password)

# ✅ Verify Password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# ✅ JWT Token Generation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ Signup API (Register User)
@app.post("/api/signup")
def signup(user: UserSignup):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user.password)
    users_collection.insert_one({"name": user.name, "email": user.email, "password": hashed_password})
    
    return {"message": "User registered successfully"}

# ✅ Login API (Authenticate User)
@app.post("/api/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})
    
    if not existing_user or not verify_password(user.password, existing_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# ✅ Fetch all services from MongoDB
@app.get("/api/services")
def get_services():
    services = list(services_collection.find({}, {"_id": 0}))  # Exclude `_id`
    return {"services": services}

# ✅ Fetch service providers from Foursquare API
@app.get("/api/providers")
def get_providers(service_name: str, city: str = "Pune"):
    headers = {"Authorization": FOURSQUARE_API_KEY, "Accept": "application/json"}
    params = {"query": service_name, "near": city, "limit": 10}

    try:
        response = requests.get(FOURSQUARE_URL, headers=headers, params=params)
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
