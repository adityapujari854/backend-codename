import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is required")

DB_NAME = os.getenv("DATABASE_NAME", "homezy_db")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

try:
    client.admin.command("ping")
except PyMongoError as exc:
    client.close()
    raise RuntimeError(
        "Unable to connect to MongoDB. Verify MONGO_URI credentials and Atlas access."
    ) from exc

users_collection = db["users"]
otp_collection = db["otp"]
bookings_collection = db["bookings"]
services_collection = db["services"]
