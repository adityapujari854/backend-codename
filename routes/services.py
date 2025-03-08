from fastapi import APIRouter, HTTPException, Depends
from pymongo.collection import Collection
from database import services_collection

# ✅ Initialize Router
services_router = APIRouter()

def get_services_collection() -> Collection:
    """Dependency to get the MongoDB services collection."""
    return services_collection

# ✅ Fetch All Services
@services_router.get("/")
async def get_all_services(collection: Collection = Depends(get_services_collection)):
    services = list(collection.find({}, {"_id": 1, "name": 1, "description": 1, "price": 1, "image": 1}))
    
    # Convert `_id` to a string (MongoDB ObjectId cannot be sent as JSON)
    for service in services:
        service["_id"] = str(service["_id"])
    
    if not services:
        raise HTTPException(status_code=404, detail="No services found")
    return {"services": services}


# ✅ Fetch Single Service by Name
@services_router.get("/{service_name}")
async def get_service(service_name: str, collection: Collection = Depends(get_services_collection)):
    service = collection.find_one({"name": service_name}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    return {"service": service}

# ✅ Add a New Service
@services_router.post("/add")
async def add_service(service_data: dict, collection: Collection = Depends(get_services_collection)):
    existing_service = collection.find_one({"name": service_data.get("name")})
    if existing_service:
        raise HTTPException(status_code=400, detail="Service already exists")

    collection.insert_one(service_data)
    return {"message": "Service added successfully"}

# ✅ Delete a Service
@services_router.delete("/{service_name}")
async def delete_service(service_name: str, collection: Collection = Depends(get_services_collection)):
    result = collection.delete_one({"name": service_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    return {"message": "Service deleted successfully"}
