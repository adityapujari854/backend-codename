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

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://adityapujari542:XQTSjRrFFQpIlGoM@cluster0.dxy3w.mongodb.net/")
client = MongoClient(MONGO_URI)
db = client["homezy_db"]
services_collection = db["services"]
users_collection = db["users"]
bookings_collection = db["bookings"]

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

# ✅ JWT Secret Key
SECRET_KEY = "cl"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ✅ User Model
class User(BaseModel):
    username: str
    password: str

# ✅ Booking Model
class Booking(BaseModel):
    user_id: str
    service_name: str
    provider_name: str
    user_details: dict
    price: int

# ✅ Foursquare API Config
FOURSQUARE_API_KEY = "fsq3LYB6FD4cl0rKy+iRre2J6vX3OYbh/RT7ZBwx0wfb2C4="
FOURSQUARE_URL = "https://api.foursquare.com/v3/places/search"

# ✅ Hash password function
def hash_password(password: str):
    return pwd_context.hash(password)

# ✅ Verify password function
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# ✅ Create JWT Token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ Register User
@app.post("/api/register")
def register_user(user: User):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = hash_password(user.password)
    users_collection.insert_one({"username": user.username, "password": hashed_password})
    return {"message": "User registered successfully"}

# ✅ Login User
@app.post("/api/login")
def login_user(user: User):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token}

# ✅ Fetch all services from MongoDB
@app.get("/api/services")
def get_services():
    services = list(services_collection.find({}, {"_id": 0}))  # Exclude _id
    return {"services": services}

# ✅ Save a booking
@app.post("/api/bookings")
def create_booking(booking: Booking):
    bookings_collection.insert_one(booking.dict())
    return {"message": "Booking confirmed"}
