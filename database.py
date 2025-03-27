from pymongo import MongoClient
import os

# ✅ Get MongoDB URI
MONGO_URI = os.getenv("MONGO_URI")

# ✅ MongoDB Connection
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["homezy_db"]
    client.server_info()  # Force connection to check if it's working
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    exit(1)

# ✅ Collections
users_collection = db["users"]
otp_collection = db["otp"]
bookings_collection = db["bookings"]
services_collection = db["services"]