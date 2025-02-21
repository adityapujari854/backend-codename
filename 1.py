from pymongo import MongoClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["homezy_db"]
users_collection = db["users"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Test login with the email and password
test_email = "adityapujari954@gmail.com"
test_password = "1234"

user = users_collection.find_one({"email": test_email})

if user:
    print(f"🛠 Stored Password Hash for {test_email}: {user['password']}")
    
    if pwd_context.verify(test_password, user["password"]):
        print(f"✅ Password matches for: {test_email}")
    else:
        print(f"❌ Password Mismatch for: {test_email}")
else:
    print(f"❌ User not found: {test_email}")
