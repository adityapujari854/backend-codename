from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import logging
import time

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Config
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("homezy_db")
RETRIES = 3
RETRY_DELAY = 5  # seconds

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    """Establish MongoDB connection with retry logic."""
    for attempt in range(RETRIES):
        try:
            logger.info(f"🔗 Connecting to MongoDB (Attempt {attempt + 1}/{RETRIES})...")
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            
            # ✅ Check if the connection is successful
            client.server_info()  
            logger.info("✅ MongoDB connection established successfully")
            
            return client[DB_NAME]

        except errors.ServerSelectionTimeoutError as e:
            logger.error(f"❌ MongoDB connection timeout: {e}")
            time.sleep(RETRY_DELAY)

        except Exception as e:
            logger.error(f"❌ Unexpected MongoDB connection error: {e}")
            time.sleep(RETRY_DELAY)

    logger.error("❌ Failed to connect to MongoDB after retries")
    return None
