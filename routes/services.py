from fastapi import APIRouter, HTTPException, Depends, Query
from pymongo.collection import Collection
from database import services_collection
from bson import ObjectId
import logging
import requests

# ✅ Initialize Router
services_router = APIRouter()

# ✅ Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Dependency to Get Services Collection
def get_services_collection() -> Collection:
    return services_collection

# ✅ Foursquare API Credentials (Replace with Your API Key)
FOURSQUARE_API_KEY = "fsq3LYB6FD4cl0rKy+iRre2J6vX3OYbh/RT7ZBwx0wfb2C4="
FOURSQUARE_API_URL = "https://api.foursquare.com/v3/places/search"

# ✅ Fetch Price from Foursquare API
def fetch_price_from_foursquare(service_name: str):
    headers = {"Authorization": FOURSQUARE_API_KEY}
    params = {"query": service_name, "limit": 1}

    try:
        response = requests.get(FOURSQUARE_API_URL, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            return data["results"][0].get("price")
    except requests.RequestException as e:
        logger.error(f"❌ Foursquare API error: {e}")

    return None

# ✅ Convert MongoDB Documents
def convert_mongo_document(doc):
    """Convert MongoDB `_id` from ObjectId to string."""
    doc["_id"] = str(doc["_id"]) if "_id" in doc else None
    doc.setdefault("categories", [])
    return doc

# ✅ Fetch Unique Categories
@services_router.get("/categories", tags=["Categories"])
async def get_all_categories(collection: Collection = Depends(get_services_collection)):
    services = list(collection.find({}, {"categories": 1}))

    if not services:
        raise HTTPException(status_code=404, detail="No categories found")

    unique_categories = set()
    for service in services:
        unique_categories.update(service.get("categories", []))

    return {"categories": sorted(unique_categories)}

# ✅ Fetch All Services with Pagination (Main Fix)
@services_router.get("/")
async def get_all_services(
    collection: Collection = Depends(get_services_collection),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    skip = (page - 1) * page_size
    services_cursor = collection.find({}, {"_id": 1, "name": 1, "description": 1, "image": 1, "categories": 1})

    services = [convert_mongo_document(service) for service in services_cursor]

    if not services:
        logger.warning("❌ No services found in MongoDB")
        raise HTTPException(status_code=404, detail="No services found")

    logger.info(f"✅ {len(services)} services retrieved from MongoDB")
    
    return {"total": len(services), "services": services}

# ✅ Fetch Single Service by Name
@services_router.get("/{service_name}")
async def get_service(service_name: str, collection: Collection = Depends(get_services_collection)):
    service = collection.find_one(
        {"name": {"$regex": f"^{service_name}$", "$options": "i"}},
        {"_id": 1, "name": 1, "description": 1, "image": 1, "categories": 1}
    )

    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    service = convert_mongo_document(service)

    # ✅ Fetch price only if missing
    if not service.get("price"):
        service["price"] = fetch_price_from_foursquare(service_name)

    return {"service": service}

# ✅ Add a New Service
@services_router.post("/add")
async def add_service(service_data: dict, collection: Collection = Depends(get_services_collection)):
    required_fields = ["name", "description", "image"]

    for field in required_fields:
        if field not in service_data or not service_data[field]:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    if "categories" in service_data and not isinstance(service_data["categories"], list):
        raise HTTPException(status_code=400, detail="Categories must be a list of strings")

    existing_service = collection.find_one({"name": {"$regex": f"^{service_data['name']}$", "$options": "i"}})
    if existing_service:
        raise HTTPException(status_code=400, detail="Service already exists")

    service_data["_id"] = ObjectId()  # Store as ObjectId in MongoDB
    collection.insert_one(service_data)
    logger.info("✅ Service added: %s", service_data)

    return {"message": "Service added successfully", "service": convert_mongo_document(service_data)}

# ✅ Delete a Service
@services_router.delete("/{service_name}")
async def delete_service(service_name: str, collection: Collection = Depends(get_services_collection)):
    result = collection.delete_one({"name": {"$regex": f"^{service_name}$", "$options": "i"}})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    return {"message": "Service deleted successfully"}

# ✅ Health Check
@services_router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is running!"}
