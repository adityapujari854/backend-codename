from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://adityapujari542:XQTSjRrFFQpIlGoM@cluster0.dxy3w.mongodb.net/")
client = MongoClient(MONGO_URI)
db = client["homezy_db"]
services_collection = db["services"]
bookings_collection = db["bookings"]
users_collection = db["users"]
cart_collection = db["cart"]

# ✅ FastAPI App
app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Security Settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Pydantic Models
class UserSignup(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class BookingData(BaseModel):
    user_id: str
    service_name: str
    provider_name: str
    price: int
    user_details: dict

class CartItem(BaseModel):
    user_id: str
    service_name: str
    provider_name: str
    price: int

# ✅ Hashing Password
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# ✅ JWT Token Creation
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ User Signup
@app.post("/api/signup")
def signup(user: UserSignup):
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = hash_password(user.password)
    users_collection.insert_one({
        "username": user.username,
        "email": user.email,
        "password": hashed_password
    })
    return {"message": "User registered successfully"}

# ✅ User Login
@app.post("/api/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ✅ Fetch all services from MongoDB
@app.get("/api/services")
def get_services():
    services = list(services_collection.find({}, {"_id": 0}))  # Exclude _id
    return {"services": services}

# ✅ Fetch service providers from Foursquare API
@app.get("/api/providers")
def get_providers(service_name: str, city: str = "Pune"):
    headers = {
        "Authorization": os.getenv("FOURSQUARE_API_KEY"),
        "Accept": "application/json",
    }
    params = {"query": service_name, "near": city, "limit": 10}

    try:
        response = requests.get("https://api.foursquare.com/v3/places/search", headers=headers, params=params)
        data = response.json()
        providers = [{
            "business_name": place["name"],
            "address": place["location"].get("formatted_address", "Address not available"),
            "contact_number": place.get("tel", "Contact not available"),
            "website": place.get("website", ""),
        } for place in data.get("results", [])]
        return {"providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Save a booking (Requires user login)
@app.post("/api/bookings")
def create_booking(booking: BookingData):
    bookings_collection.insert_one(booking.dict())
    return {"message": "Booking confirmed"}

# ✅ Add item to cart
@app.post("/api/cart/add")
def add_to_cart(cart_item: CartItem):
    cart_collection.insert_one(cart_item.dict())
    return {"message": "Item added to cart"}

# ✅ Fetch user's cart items
@app.get("/api/cart/{user_id}")
def get_cart(user_id: str):
    items = list(cart_collection.find({"user_id": user_id}, {"_id": 0}))
    return {"cart": items}

# ✅ Remove item from cart
@app.delete("/api/cart/remove/{user_id}/{service_name}")
def remove_from_cart(user_id: str, service_name: str):
    cart_collection.delete_one({"user_id": user_id, "service_name": service_name})
    return {"message": "Item removed from cart"}
