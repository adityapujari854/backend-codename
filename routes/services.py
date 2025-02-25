from fastapi import APIRouter, HTTPException
from database import services_collection

# ✅ Initialize Router
services_router = APIRouter()

# ✅ Fetch All Services
@services_router.get("/")
def get_all_services():
    services = list(services_collection.find({}, {"_id": 0}))
    if not services:
        raise HTTPException(status_code=404, detail="No services found")
    return {"services": services}

# ✅ Fetch Single Service by Name
@services_router.get("/{service_name}")
def get_service(service_name: str):
    service = services_collection.find_one({"name": service_name}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"service": service}

# ✅ Add a New Service
@services_router.post("/add")
def add_service(service_data: dict):
    existing_service = services_collection.find_one({"name": service_data.get("name")})
    if existing_service:
        raise HTTPException(status_code=400, detail="Service already exists")

    services_collection.insert_one(service_data)
    return {"message": "Service added successfully"}

# ✅ Delete a Service
@services_router.delete("/{service_name}")
def delete_service(service_name: str):
    result = services_collection.delete_one({"name": service_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {"message": "Service deleted successfully"}
