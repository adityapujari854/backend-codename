from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["homezy_db"]

users_collection = db["users"]
otp_collection = db["otp"]
bookings_collection = db["bookings"]
services_collection = db["services"]