import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from database import providers_collection  # MongoDB collection

# ✅ Foursquare API Constants
FOURSQUARE_API_KEY = "fsq3LYB6FD4cl0rKy+iRre2J6vX3OYbh/RT7ZBwx0wfb2C4="
FOURSQUARE_API_URL = "https://api.foursquare.com/v3/places/search"

# ✅ Headers with Authorization
HEADERS = {
    "Authorization": FOURSQUARE_API_KEY,
    "Accept": "application/json"
}

# ✅ Initialize Router
providers_router = APIRouter(tags=["Service Providers"])

# ✅ Mapped Services
SERVICE_KEYWORDS = {
    "Plumbing Service": ["plumbing", "pipe repair", "leak", "faucet", "drain"],
    "Electrical Repair": ["electrician", "circuit repair", "wiring", "fuse"],
    "House Cleaning": ["cleaning", "maid", "housekeeping", "janitorial"],
    "Carpentry": ["carpenter", "woodwork", "furniture", "cabinet"],
    "AC Repair": ["AC repair", "air conditioning", "HVAC", "cooling"],
    "Pest Control": ["pest", "insect", "termite", "cockroach", "rodent"],
    "Home Painting": ["painting", "painter", "wall paint", "interior"],
    "Gardening": ["gardening", "lawn care", "planting", "landscaping"],
    "Car Repair": ["car repair", "mechanic", "auto service", "tire change"],
    "CCTV Installation": ["cctv", "camera", "security system", "surveillance"]
}

# ✅ Fetch providers with Foursquare and MongoDB fallback
@providers_router.get("/", summary="Get service providers with categories")
async def get_providers(
    service_name: str = Query(..., title="Service Name"),
    limit: int = Query(10, le=20, title="Limit")
) -> Dict[str, Any]:
    """
    Fetch service providers with categories from Foursquare and MongoDB fallback.
    """
    print(f"🔍 Fetching providers for: {service_name} (Limit: {limit})")

    # ✅ MongoDB fallback
    cached_providers = list(providers_collection.find(
        {"service_name": service_name}
    ).limit(limit))

    if cached_providers:
        print("✅ Using MongoDB providers")
        return {"providers": cached_providers}

    # ✅ Foursquare Query Parameters
    params = {
        "query": service_name,
        "near": "Pune",
        "limit": limit
    }

    try:
        # ✅ Foursquare API Request
        response = requests.get(FOURSQUARE_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        # ✅ Extract Results
        results = data.get("results", [])

        if not results:
            raise HTTPException(status_code=404, detail="⚠️ No providers found.")

        # ✅ Parse Results with Categories
        final_providers = []
        for place in results:
            categories = [
                category["name"].lower() for category in place.get("categories", [])
            ]

            provider = {
                "business_name": place.get("name", "Unknown"),
                "address": place.get("location", {}).get("formatted_address", "N/A"),
                "contact_number": place.get("tel", "N/A"),
                "website": place.get("website", "N/A"),
                "rating": place.get("rating", "N/A"),
                "price": place.get("price", {}).get("tier", "N/A"),
                "category": categories[0] if categories else "General"
            }

            # ✅ Store in MongoDB for caching
            providers_collection.insert_one(provider)
            final_providers.append(provider)

        return {"providers": final_providers}

    except requests.exceptions.RequestException as req_err:
        raise HTTPException(status_code=502, detail=f"API request failed: {str(req_err)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
