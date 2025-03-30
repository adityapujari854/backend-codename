from fastapi import APIRouter, HTTPException, Depends, Query
from pymongo.collection import Collection
from database import services_collection
from bson import ObjectId
import logging
import requests
import os

# ✅ Initialize Router
services_router = APIRouter()

# ✅ Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Dependency to Get Services Collection
def get_services_collection() -> Collection:
    return services_collection

# ✅ Foursquare API Credentials (Replace with Your API Key)
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
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

# ✅ Fetch Providers from Foursquare API
def fetch_providers_from_foursquare(category_name: str):
    headers = {"Authorization": FOURSQUARE_API_KEY}
    params = {
        "query": category_name,
        "near": "Mumbai",  # Change this to dynamically fetch the user’s location
        "limit": 5
    }

    try:
        response = requests.get(FOURSQUARE_API_URL, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        providers = []
        for place in data.get("results", []):
            providers.append({
                "business_name": place.get("name", "Unknown"),
                "address": place.get("location", {}).get("formatted_address", "Address not available"),
                "contact_number": place.get("contact", {}).get("phone", "N/A"),
                "website": place.get("website", "N/A"),
                "price": place.get("price", "N/A"),
                "rating": place.get("rating", "No rating"),
            })

        return providers

    except requests.RequestException as e:
        logger.error(f"❌ Error fetching providers for {category_name}: {e}")
        return []

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

# ✅ Fetch Categories with Providers for a Service
@services_router.get("/categories/{service_id}", tags=["Categories"])
async def get_categories_with_providers(service_id: str, collection: Collection = Depends(get_services_collection)):
    # ✅ Fetch service details
    service = collection.find_one({"_id": ObjectId(service_id)}, {"categories": 1})

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    categories = service.get("categories", [])

    # ✅ Fetch providers for each category
    categories_with_providers = [
        {
            "name": category,
            "providers": fetch_providers_from_foursquare(category)
        }
        for category in categories
    ]

    return {"categories": categories_with_providers}

# ✅ Fetch All Services with Pagination (Fixed)
@services_router.get("/")
async def get_all_services(
    collection: Collection = Depends(get_services_collection),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    skip = (page - 1) * page_size
    
    # ✅ Fetch total count
    total_services = collection.count_documents({})
    
    # ✅ Apply pagination
    services_cursor = collection.find({}, {"_id": 1, "name": 1, "description": 1, "image": 1, "categories": 1})
    services = [convert_mongo_document(service) for service in services_cursor.skip(skip).limit(page_size)]
    
    if not services:
        logger.warning("❌ No services found in MongoDB")
        raise HTTPException(status_code=404, detail="No services found")

    logger.info(f"✅ {len(services)} services retrieved from MongoDB")
    
    return {
        "total": total_services,
        "page": page,
        "page_size": page_size,
        "services": services
    }

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

# ✅ Add a New Service (Fixed `_id`)
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

    # ✅ Convert `_id` to string before inserting
    service_data["_id"] = str(ObjectId())  
    collection.insert_one(service_data)
    
    logger.info("✅ Service added: %s", service_data)

    return {"message": "Service added successfully", "service": service_data}

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
