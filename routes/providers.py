import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List

# ✅ Foursquare API Constants (Directly Using Key)
FOURSQUARE_API_KEY = "fsq3LYB6FD4cl0rKy+iRre2J6vX3OYbh/RT7ZBwx0wfb2C4="
FOURSQUARE_API_URL = "https://api.foursquare.com/v3/places/search"

# ✅ Headers with Correct Authorization Format
HEADERS = {
    "Authorization": FOURSQUARE_API_KEY,
    "Accept": "application/json"
}

# ✅ Initialize Router
providers_router = APIRouter(tags=["Service Providers"])

# ✅ Mapped Services to Filter Irrelevant Results
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

# ✅ Fetch service providers from Foursquare API
@providers_router.get("/", summary="Get service providers from Foursquare")
async def get_providers(
    service_name: str = Query(..., title="Service Name", description="Name of the service to search"),
    limit: int = Query(15, le=20, title="Limit", description="Number of providers to fetch (max: 20)")
) -> Dict[str, Any]:
    """
    Fetch service providers based on a given service name and city (Pune) using the Foursquare API.
    """

    # ✅ Debugging logs
    print(f"🔍 Incoming Request - service_name={service_name}, limit={limit}")

    # ✅ Foursquare Query Parameters
    params = {
        "query": service_name,
        "near": "Pune",           # 🔥 Fixed to Pune city
        "limit": limit
    }

    try:
        # ✅ API Request
        response = requests.get(FOURSQUARE_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        print("✅ Foursquare API Response:", data)

        # ✅ Extract Results
        results = data.get("results", [])

        if not results:
            print("⚠️ No providers found in Foursquare API response.")
            raise HTTPException(status_code=404, detail="⚠️ No providers found for the given service.")

        # ✅ Filter results to show only relevant services
        keywords = SERVICE_KEYWORDS.get(service_name, [])
        
        filtered_providers: List[Dict[str, str]] = []

        for place in results:
            categories = [category["name"].lower() for category in place.get("categories", [])]
            
            # ✅ Only include providers matching relevant keywords
            if any(keyword in " ".join(categories) for keyword in keywords):
                filtered_providers.append({
                    "business_name": place.get("name", "Unknown"),
                    "address": place.get("location", {}).get("formatted_address", "Not available"),
                    "contact_number": place.get("tel", "N/A"),
                    "website": place.get("website", "N/A"),
                    "categories": categories,
                    "latitude": str(place.get("geocodes", {}).get("main", {}).get("latitude", "N/A")),
                    "longitude": str(place.get("geocodes", {}).get("main", {}).get("longitude", "N/A")),
                    "rating": place.get("rating", "N/A"),
                    "price": place.get("price", {}).get("tier", "N/A")
                })

        if not filtered_providers:
            print("⚠️ No relevant providers found after filtering.")
            raise HTTPException(status_code=404, detail="⚠️ No relevant providers found for the given service.")

        print(f"✅ Providers Found: {len(filtered_providers)}")
        return {"providers": filtered_providers}

    except requests.exceptions.RequestException as req_err:
        print(f"❌ API Request Error: {req_err}")
        raise HTTPException(status_code=502, detail=f"External API request failed: {str(req_err)}")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
