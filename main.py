from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
from fastapi.middleware.cors import CORSMiddleware

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://adityapujari542:XQTSjRrFFQpIlGoM@cluster0.dxy3w.mongodb.net/")
client = MongoClient(MONGO_URI)
db = client["homezy_db"]
services_collection = db["services"]
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

# ✅ Foursquare API Config
FOURSQUARE_API_KEY = "fsq3LYB6FD4cl0rKy+iRre2J6vX3OYbh/RT7ZBwx0wfb2C4="
FOURSQUARE_URL = "https://api.foursquare.com/v3/places/search"

# ✅ Fetch all services from MongoDB
@app.get("/api/services")
def get_services():
    services = list(services_collection.find({}, {"_id": 0}))  # Exclude _id
    return {"services": services}

# ✅ Fetch service providers from Foursquare API
@app.get("/api/providers")
def get_providers(service_name: str, city: str = "Pune"):
    headers = {
        "Authorization": FOURSQUARE_API_KEY,
        "Accept": "application/json",
    }
    params = {
        "query": service_name,
        "near": city,
        "limit": 10
    }

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
def create_booking(booking: dict):
    bookings_collection.insert_one(booking)
    return {"message": "Booking confirmed"}
