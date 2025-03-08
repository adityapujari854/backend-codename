from fastapi import APIRouter, HTTPException, Depends
from pymongo.collection import Collection
from database import services_collection
from bson import ObjectId  # ✅ For handling `_id`

# ✅ Initialize Router
services_router = APIRouter()

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
            doc["_id"] = doc["_id"]["$oid"]  # Convert MongoDB `$oid` format to string
    return doc

# ✅ Fetch All Services
@services_router.get("/")
async def get_all_services(collection: Collection = Depends(get_services_collection)):
    services = list(collection.find({}, {"_id": 1, "name": 1, "description": 1, "price": 1, "image": 1}))

    if not services:
        raise HTTPException(status_code=404, detail="No services found")

    # ✅ Convert `_id` for all services
    services = [convert_mongo_document(service) for service in services]

    return {"services": services}

# ✅ Fetch Single Service by Name (Case-Insensitive)
@services_router.get("/{service_name}")
async def get_service(service_name: str, collection: Collection = Depends(get_services_collection)):
    service = collection.find_one(
        {"name": {"$regex": f"^{service_name}$", "$options": "i"}}, 
        {"_id": 1, "name": 1, "description": 1, "price": 1, "image": 1}
    )
    
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    service = convert_mongo_document(service)  # ✅ Convert `_id`

    return {"service": service}

# ✅ Add a New Service (With Validation)
@services_router.post("/add")
async def add_service(service_data: dict, collection: Collection = Depends(get_services_collection)):
    required_fields = ["name", "description", "price", "image"]

    # ✅ Validate required fields
    for field in required_fields:
        if field not in service_data or not service_data[field]:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    # ✅ Ensure `price` is a number
    if not isinstance(service_data["price"], (int, float)):
        raise HTTPException(status_code=400, detail="Price must be a number")

    # ✅ Check if service already exists (Case-Insensitive)
    existing_service = collection.find_one({"name": {"$regex": f"^{service_data['name']}$", "$options": "i"}})
    
    if existing_service:
        raise HTTPException(status_code=400, detail="Service already exists")

    # ✅ Ensure `_id` is properly set
    service_data["_id"] = str(ObjectId())

    collection.insert_one(service_data)
    return {"message": "Service added successfully", "service": service_data}

# ✅ Delete a Service (Case-Insensitive)
@services_router.delete("/{service_name}")
async def delete_service(service_name: str, collection: Collection = Depends(get_services_collection)):
    result = collection.delete_one({"name": {"$regex": f"^{service_name}$", "$options": "i"}})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    return {"message": "Service deleted successfully"}
