import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List

# ✅ Foursquare API Constants
FOURSQUARE_API_KEY = "fsq3LYB6FD4cl0rKy+iRre2J6vX3OYbh/RT7ZBwx0wfb2C4="
FOURSQUARE_API_URL = "https://api.foursquare.com/v3/places/search"

HEADERS = {
    "Authorization": f"{FOURSQUARE_API_KEY}",
    "Accept": "application/json"
}

# ✅ Mapped Your Services to Foursquare Categories
SERVICE_CATEGORIES = {
    "Plumbing Service": "16020",       # Plumbing
    "Electrical Repair": "16012",      # Electrician
    "House Cleaning": "16014",         # Cleaning Service
    "Carpentry": "16021",              # Carpenter
    "AC Repair": "17029",              # HVAC Repair (AC)
    "Pest Control": "16017",           # Pest Control
    "Home Painting": "16016",          # Painting Service
    "Gardening": "16028",              # Gardening & Landscaping
    "Car Repair": "17069",             # Auto Repair
    "CCTV Installation": "17068"       # Security & CCTV
}

# ✅ Initialize Router
providers_router = APIRouter(prefix="/api/providers", tags=["Service Providers"])

# ✅ Fetch Service Providers from Foursquare
@providers_router.get("/", summary="Get service providers from Foursquare")
async def get_providers(
    service_name: str = Query(..., title="Service Name"),
    limit: int = Query(5, le=20)  # Limit the number of providers
) -> Dict[str, Any]:
    """
    Fetch service providers based on a given service name and city (Pune) using the Foursquare API.
    """

    # ✅ Match the service name to Foursquare categories
    category_id = SERVICE_CATEGORIES.get(service_name)
    
    if not category_id:
        raise HTTPException(status_code=400, detail=f"⚠️ Unknown service: {service_name}")

    # ✅ Query Parameters for Foursquare
    params = {
        "query": service_name,
        "near": "Pune",
        "limit": limit,
        "categories": category_id  # 🔥 Filter by Foursquare category ID
    }

    # ✅ Debugging logs
    print(f"🔍 Incoming Request - service_name={service_name}, category={category_id}, limit={limit}")

    try:
        # ✅ API Request
        response = requests.get(FOURSQUARE_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        print("✅ Foursquare API Response:", data)

        results = data.get("results", [])
        
        if not results:
            print("⚠️ No providers found in Foursquare API response.")
            raise HTTPException(status_code=404, detail="⚠️ No providers found for the given service.")

        # ✅ Process and Return Foursquare Data
        providers: List[Dict[str, str]] = [
            {
                "business_name": place.get("name", "Unknown"),
                "address": place.get("location", {}).get("formatted_address", "Not available"),
                "contact_number": place.get("tel", "N/A"),
                "website": place.get("website", "N/A"),
                "categories": [category["name"] for category in place.get("categories", [])],
                "latitude": str(place.get("geocodes", {}).get("main", {}).get("latitude", "N/A")),
                "longitude": str(place.get("geocodes", {}).get("main", {}).get("longitude", "N/A")),
                "rating": place.get("rating", "N/A"),
                "price": place.get("price", {}).get("tier", "N/A")
            }
            for place in results
        ]

        print(f"✅ Providers Found: {len(providers)}")
        return {"providers": providers}

    except requests.exceptions.RequestException as req_err:
        print(f"❌ API Request Error: {req_err}")
        raise HTTPException(status_code=502, detail=f"External API request failed: {str(req_err)}")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
