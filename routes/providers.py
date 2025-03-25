import os
import requests
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List
from pymongo.collection import Collection
from database import services_collection  # ✅ MongoDB connection
from bson import ObjectId
import logging

# ✅ Logger Configuration
logging.basicConfig(level=logging.INFO)

# ✅ Load API Key from Environment Variables
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
if not FOURSQUARE_API_KEY:
    logging.warning("⚠️ FOURSQUARE_API_KEY not set. Using MongoDB fallback.")

# ✅ Foursquare API Constants
FOURSQUARE_API_URL = "https://api.foursquare.com/v3/places/search"
HEADERS = {
    "Authorization": f"Bearer {FOURSQUARE_API_KEY}" if FOURSQUARE_API_KEY else "",
    "Accept": "application/json"
}

# ✅ Initialize Router
providers_router = APIRouter(prefix="/api/providers", tags=["Service Providers"])

# ✅ Helper Function to Convert MongoDB Documents
def convert_mongo_document(doc):
    """Convert MongoDB ObjectId to string format."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# ✅ Dependency to Get MongoDB Collection
def get_services_collection() -> Collection:
    if services_collection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return services_collection

# ✅ Foursquare API Request
async def fetch_from_foursquare(service_name: str, city: str, limit: int) -> List[Dict[str, str]]:
    """Fetch service providers from Foursquare API."""
    params = {"query": service_name, "near": city, "limit": limit}

    try:
        response = requests.get(FOURSQUARE_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            logging.warning("⚠️ No providers found in Foursquare.")
            return []

        providers = [
            {
                "business_name": place.get("name", "Unknown"),
                "address": place.get("location", {}).get("formatted_address", "Not available"),
                "contact_number": place.get("tel", "N/A"),
                "website": place.get("website", "N/A"),
                "categories": [category["name"] for category in place.get("categories", [])]
            }
            for place in results
        ]

        logging.info(f"✅ Foursquare Providers Found: {len(providers)}")
        return providers

    except requests.exceptions.RequestException as req_err:
        logging.error(f"❌ Foursquare API Request Error: {req_err}")
        return []

# ✅ MongoDB Fallback Query
async def fetch_from_mongo(
    service_name: str, city: str, limit: int, collection: Collection
) -> List[Dict[str, str]]:
    """Fetch providers from MongoDB if Foursquare API fails."""
    try:
        query = {
            "name": {"$regex": f"^{service_name}$", "$options": "i"},  
            "city": {"$regex": f"^{city}$", "$options": "i"}           
        }

        providers = list(collection.find(query).limit(limit))

        if not providers:
            logging.warning("⚠️ No providers found in MongoDB.")
            return []

        providers = [convert_mongo_document(provider) for provider in providers]

        logging.info(f"✅ MongoDB Providers Found: {len(providers)}")
        return providers

    except Exception as e:
        logging.error(f"❌ MongoDB Query Error: {e}")
        return []

# ✅ Route: Get Providers (Foursquare + MongoDB Fallback)
@providers_router.get("/", summary="Get Service Providers with Foursquare & MongoDB Fallback")
async def get_providers(
    service_name: str = Query(..., title="Service Name"),
    city: str = Query("Pune", title="City"),
    limit: int = Query(10, le=20),
    collection: Collection = Depends(get_services_collection)
) -> Dict[str, Any]:
    """
    Fetch service providers from Foursquare API, fallback to MongoDB if Foursquare fails.
    """
    providers = []

    # ✅ Attempt Foursquare API first
    if FOURSQUARE_API_KEY:
        providers = await fetch_from_foursquare(service_name, city, limit)

    # ✅ Fallback to MongoDB if Foursquare API fails or is empty
    if not providers:
        logging.info("🛠️ Fallback to MongoDB")
        providers = await fetch_from_mongo(service_name, city, limit, collection)

    if not providers:
        raise HTTPException(status_code=404, detail="No providers found")

    return {"providers": providers}
