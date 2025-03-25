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

# ✅ Fetch service providers from Foursquare API
@providers_router.get("/", summary="Get service providers from Foursquare")
async def get_providers(
    service_name: str = Query(..., title="Service Name", description="Name of the service to search"),
    limit: int = Query(20, le=20, title="Limit", description="Number of providers to fetch (max: 20)")
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

        # ✅ Process and Format Foursquare Data
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
