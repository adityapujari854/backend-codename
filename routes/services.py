from fastapi import APIRouter, HTTPException, Depends, Query
from pymongo.collection import Collection
from database import services_collection
from bson import ObjectId  # ✅ For handling MongoDB `_id`
import logging

# ✅ Initialize Router
services_router = APIRouter()

# ✅ Initialize Logger
logging.basicConfig(level=logging.INFO)

# ✅ Dependency to Get Services Collection
def get_services_collection() -> Collection:
    return services_collection

# ✅ Helper Function to Convert MongoDB Documents
def convert_mongo_document(doc):
    """Converts MongoDB `_id` from ObjectId format to a string for JSON response."""
    if "_id" in doc:
        if isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        elif isinstance(doc["_id"], dict) and "$oid" in doc["_id"]:
            doc["_id"] = doc["_id"]["$oid"]  # Handle `$oid` format
    return doc

# ✅ Fetch All Services with Pagination and Category Filter
@services_router.get("/")
async def get_all_services(
    collection: Collection = Depends(get_services_collection),
    page: int = Query(1, alias="page", ge=1),          # ✅ Pagination
    page_size: int = Query(10, alias="page_size", ge=1, le=100),
    category: str = Query(None, alias="category")       # ✅ Category filter
):
    """
    Fetch all services with pagination and optional category filtering.
    """
    skip = (page - 1) * page_size

    # ✅ Apply category filter if provided
    query = {}
    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    services = list(collection.find(query)
                     .skip(skip)
                     .limit(page_size))

    if not services:
        raise HTTPException(status_code=404, detail="No services found")

    services = [convert_mongo_document(service) for service in services]

    return {
        "page": page,
        "page_size": page_size,
        "total_services": collection.count_documents(query),
        "services": services
    }

# ✅ Fetch Single Service by Name with Category
@services_router.get("/{service_name}")
async def get_service(
    service_name: str, 
    collection: Collection = Depends(get_services_collection),
    category: str = Query(None, alias="category")
):
    """
    Fetch a single service by name, optionally filtered by category.
    """
    query = {
        "name": {"$regex": f"^{service_name}$", "$options": "i"}
    }

    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    service = collection.find_one(query)

    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    service = convert_mongo_document(service)
    return {"service": service}

# ✅ Add a New Service (With Validation and Category Support)
@services_router.post("/add")
async def add_service(service_data: dict, collection: Collection = Depends(get_services_collection)):
    """
    Add a new service with validation and category support.
    """
    required_fields = ["name", "description", "price", "image", "category"]

    # ✅ Validate required fields
    for field in required_fields:
        if field not in service_data or not service_data[field]:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    # ✅ Ensure `price` is a number
    if not isinstance(service_data["price"], (int, float)):
        raise HTTPException(status_code=400, detail="Price must be a number")

    # ✅ Check if service already exists (Case-Insensitive)
    existing_service = collection.find_one({
        "name": {"$regex": f"^{service_data['name']}$", "$options": "i"}
    })

    if existing_service:
        raise HTTPException(status_code=400, detail="Service already exists")

    # ✅ Set MongoDB `_id`
    service_data["_id"] = str(ObjectId())

    # ✅ Insert into MongoDB
    collection.insert_one(service_data)
    
    logging.info("✅ Service added: %s", service_data)
    
    return {"message": "Service added successfully", "service": service_data}

# ✅ Update a Service (With Category)
@services_router.put("/{service_name}")
async def update_service(
    service_name: str, 
    service_data: dict, 
    collection: Collection = Depends(get_services_collection)
):
    """
    Update an existing service by name with category support.
    """
    query = {"name": {"$regex": f"^{service_name}$", "$options": "i"}}
    existing_service = collection.find_one(query)

    if not existing_service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    collection.update_one(query, {"$set": service_data})

    return {"message": "Service updated successfully"}

# ✅ Delete a Service (Case-Insensitive)
@services_router.delete("/{service_name}")
async def delete_service(
    service_name: str, 
    collection: Collection = Depends(get_services_collection)
):
    """
    Delete a service by name.
    """
    result = collection.delete_one({
        "name": {"$regex": f"^{service_name}$", "$options": "i"}
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    return {"message": "Service deleted successfully"}

# ✅ Health Check Route
@services_router.get("/health")
async def health_check():
    """
    Health check route to verify the service is running.
    """
    return {"status": "ok", "message": "Service is running!"}
